#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import functools
import json
import mimetypes
import os
import re
import logging
import fnmatch
import gzip
import statistics

from datetime import date
from logging.config import dictConfig
from itertools import groupby
from operator import itemgetter

"""
Log analyzer for custom nginx logs.

To run:
$ python3 log_analyzer.py --config path/to/config.json

config.json - should be a configuration json file 
like `DEFAULT_CONFIG` constant.

"""


DEFAULT_CONFIG = {
    'REPORT_SIZE': 1000,
    'REPORT_DIR': './reports',
    'LOG_DIR': './logs',
    'LOG_FILE_TMP': 'nginx-access-ui.log-{today_stamp}.*',
    'LOGGER_CONF': {
        'version': 1,
        'formatters': {
            'default': {
                'format': '[%(asctime)s] %(levelname).1s %(message)s',
                'datefmt': '%Y.%m.%d %H:%M:%S'
            }
        },
        'handlers': {
            'file': {
                'level': 'INFO',
                'formatter': 'default',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': 'log_analyzer.log'
            }
        },
        'loggers': {
            'default': {
                'level': 'INFO',
                'handlers': ['file']
            }
        }
    },
    'REPORT_FILE_TMP': 'report-{year}.{month}.{day}.html',
    'REPORT_TMP_NAME': 'report_template.html',
    'LOG_LINE_PATTERN': r'.+\]\s+\"\w+\s+(?P<request_url>.+?)\s.+?\s'
                        r'(?P<request_time>[\d\.]+)$',
    'PARSE_ERR_THRESHOLD': 0.3
}


def get_log_filepath(logs_dir, today_log_filename):
    try:
        logs_in_dir = os.listdir(logs_dir)
    except FileNotFoundError:
        return
    found_logs = fnmatch.filter(logs_in_dir, today_log_filename)
    if found_logs:
        log_filepath = os.path.join(logs_dir, found_logs[0])
    else:
        log_filepath = None
    return log_filepath


def read_log(log_filepath):
    """
    Opens and reads log file from path `log_filepath`
    It can read both plain text or gzip archive types of logs
    """
    log_filetype, log_encoding = mimetypes.guess_type(log_filepath)

    if log_filetype == 'text/plain':
        log_fileobj = open(log_filepath)
    elif log_encoding == 'gzip':
        log_fileobj = gzip.open(log_filepath, 'rt')
    else:
        return
    for log_line in log_fileobj:
        yield log_line
    log_fileobj.close()


def check_parse_errors(parsed_lines_count, parse_error_count, error_threshold):
    """
    Checks whether parsing errors greater than `error_threshold`
    If yes then returns `True` and stops parsing
    """
    try:
        errors_percent = parse_error_count / parsed_lines_count
    except ZeroDivisionError:
        errors_percent = 0
    return True if errors_percent < error_threshold else False


def process_log_lines(lines, line_pattern, log=None, error_threshold=0.0):
    logger = log if log else logging
    parse_error_count = 0
    compiled_pattern = re.compile(line_pattern)

    for line_number, line in enumerate(lines):

        if not check_parse_errors(line_number,
                                  parse_error_count, error_threshold):
            log.error('Too much parse errors: %d', parse_error_count)
            break

        if line:
            match = compiled_pattern.search(line)
            if match:
                yield match.groupdict()
            else:
                parse_error_count += 1
                logger.info('Skip unmatched log string: %s', line)
        else:
            logger.info('Skip empty line on position: %d', line_number)


def count_statistics(parsed_lines: list, report_size=500):
    total_lines_count = len(parsed_lines)
    total_request_time = functools.reduce(
        lambda total, line: total + float(line.get('request_time', 0.0)),
        parsed_lines,
        0.0
    )
    result = []
    sorted_lines = sorted(parsed_lines, key=itemgetter('request_url'))
    for url, line in groupby(sorted_lines, key=itemgetter('request_url')):
        items = list(line)
        lines_count = len(items)
        url_request_time_list = [float(line.get('request_time', 0.0)) 
                                 for line in items]
        time_sum = round(sum(url_request_time_list), 3)
        result.append({
            'url': url,
            'count': lines_count,
            'count_perc': round((lines_count / total_lines_count) * 100, 3),
            'time_sum': time_sum,
            'time_max': max(
                items,
                key=lambda line: float(line.get('request_time', 0.0))
            ).get('request_time', 0.0),
            'time_avg': round(statistics.mean(url_request_time_list), 3),
            'time_med': round(statistics.median(url_request_time_list), 3),
            'time_perc': round((time_sum / total_request_time) * 100, 3)
        })
    return sorted(result, key=itemgetter('time_avg'),
                  reverse=True)[:report_size]


def generate_and_save_report(report_data, template_report_fullpath,
                             today_report_fullpath):
    table_json = json.dumps(report_data)
    with open(template_report_fullpath) as template_report_fileobj:
        template_report_text = template_report_fileobj.read()
    generated_report_text = template_report_text.replace('$table_json',
                                                         table_json)
    with open(today_report_fullpath, 'w') as generated_report_fileobj:
        generated_report_fileobj.write(generated_report_text)


def is_filepath(path):
    if not os.path.isfile(path):
        raise argparse.ArgumentTypeError(
            "The config file doesn't exist or the path is incorrect"
        )
    return path


def get_args():
    parser = argparse.ArgumentParser(
        description='Custom nginx log parser and analyzer'
    )
    parser.add_argument(
        '-c', '--config',
        help="Path to the script's config file",
        type=is_filepath,
        default='./config.json'
    )
    return parser.parse_args()


def get_config(config_filepath, default_config={}):
    """
    Reads config file which was specified in `config_filepath`
    and merges it with `DEFAULT_CONFIG` constant
    """

    with open(config_filepath) as config_file:
        try:
            decoded_data = json.load(config_file)
        except json.decoder.JSONDecodeError:
            print('Error parsing config file: %s '
                  'Invalid json' % config_filepath)
            return
        except FileNotFoundError:
            print('Config file was not found')
            return
    result_config = default_config.copy()
    result_config.update(decoded_data)
    return result_config


def main(log=None, config=None):
    logger = log if log else logging

    if config is None:
        logger.error('Config was not found. Terminating script...')
        return

    logger.info('Searching for generated report '
                'in directory: %s', config['REPORT_DIR'])
    today = date.today()
    today_report_filename = config['REPORT_FILE_TMP'].format(
        year=today.year, month=today.month, day=today.day)
    today_report_fullpath = os.path.join(config['REPORT_DIR'],
                                         today_report_filename)
    is_report_generated = os.path.isfile(today_report_fullpath)
    if is_report_generated:
        logger.info('We have generated '
                    'a report today: %s', today_report_fullpath)
        return
    else:
        logger.info("No today's reports was found. Continue...")

    logger.info("Looking for logs in directory: %s", config['LOG_DIR'])
    today_stamp = today.strftime('%Y%m%d')
    today_log_filename = config['LOG_FILE_TMP'].format(today_stamp=today_stamp)
    log_filepath = get_log_filepath(
        logs_dir=config['LOG_DIR'],
        today_log_filename=today_log_filename
    )
    if not log_filepath:
        logger.error("There are not today's logs "
                     "in directory: %s", config['LOG_DIR'])
        return

    logger.info('Trying to open logfile: %s', log_filepath)
    log_lines = read_log(log_filepath)

    logger.info('Parsing log lines')
    parsed_lines = process_log_lines(
        log_lines,
        line_pattern=config['LOG_LINE_PATTERN'],
        log=logger,
        error_threshold=config['PARSE_ERR_THRESHOLD']
    )

    logger.info('Calculating statistics for log lines')
    lines_statistics = count_statistics(list(parsed_lines),
                                        config['REPORT_SIZE'])

    logger.info('Generate and save report '
                'in folder: %s', config['REPORT_DIR'])
    template_report_fullpath = os.path.join('.', config['REPORT_TMP_NAME'])
    generate_and_save_report(
        report_data=lines_statistics,
        template_report_fullpath=template_report_fullpath,
        today_report_fullpath=today_report_fullpath
    )

    logger.info('Done!')


if __name__ == '__main__':
    args = get_args()

    config = get_config(
        default_config=DEFAULT_CONFIG,
        config_filepath=args.config
    )

    if config is None:
        exit('Invalid config')

    dictConfig(config['LOGGER_CONF'])
    log = logging.getLogger('default')
    log.info('Start log analyzer script with '
             'config: %s and initial params: %s', config, vars(args))

    try:
        main(log=log, config=config)
    except BaseException:
        log.exception('Critical error. Terminating script...')
