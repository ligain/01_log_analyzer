#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import json
import mimetypes
import os
import re
import logging
import fnmatch
import gzip

from datetime import date
from logging.config import dictConfig


# log_format ui_short '$remote_addr $remote_user $http_x_real_ip [$time_local] "$request" '
#                     '$status $body_bytes_sent "$http_referer" '
#                     '"$http_user_agent" "$http_x_forwarded_for" "$http_X_REQUEST_ID" "$http_X_RB_USER" '
#                     '$request_time';

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
    'LOG_LINE_PATTERN': r'(?P<remote_addr>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\s+'
                        r'(?P<remote_user>[\w\-]+)\s+'
                        r'(?P<http_x_real_ip>[\w\-]+)\s+\['
                        r'(?P<time_local>.+)\]\s+\"'
                        r'(?P<request_method>\w+)\s+'
                        r'(?P<request_url>.+?)\s'
                        r'(?P<request_protocol>.+?)\"\s+'
                        r'(?P<status>\d{3})\s+'
                        r'(?P<body_bytes_sent>\d+)\s+\"'
                        r'(?P<http_referer>.+?)\"\s+\"'
                        r'(?P<http_user_agent>.+?)\"\s+\"'
                        r'(?P<http_x_forwarded_for>[\w\-]+)\"\s+\"'
                        r'(?P<http_x_request_id>.+?)\"\s+\"'
                        r'(?P<http_x_rb_user>.+?)\"\s'
                        r'(?P<request_time>[\d\.]+)$',
    'PARSE_ERR_THRESHOLD': 0.3
}


def get_log_filepath(logs_dir, log_filename_tmp):
    logs_in_dir = os.listdir(logs_dir)
    today_stamp = date.today().strftime('%Y%m%d')
    today_log_filename = log_filename_tmp.format(today_stamp=today_stamp)
    found_logs = fnmatch.filter(logs_in_dir, today_log_filename)
    if found_logs:
        log_filepath = os.path.join(logs_dir, found_logs[0])
    else:
        log_filepath = None
    return log_filepath


def read_log(log_filepath):
    """
    Определяет является ли логфайл по адресу `log_filepath`
    простым текстовым или зархивирован и затем читает его построчно
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
    return True


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

    logger.info("Looking for logs in directory: %s", config['LOG_DIR'])
    log_filepath = get_log_filepath(
        logs_dir=config['LOG_DIR'],
        log_filename_tmp=config['LOG_FILE_TMP']
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

    for parsed_line in parsed_lines:
        print(parsed_line)

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
