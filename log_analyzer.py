#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import json
import mimetypes
import os
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
                'filename': 'log_analyzer.log',
            }
        },
        'loggers': {
            'default': {
                'level': 'INFO',
                'handlers': ['file']
            }
        }
    }
}


def get_log_filepath(logs_dir='../logs', log_filename_tmp='nginx-access-ui.log-{today_stamp}.*'):
    logs_in_dir = os.listdir(logs_dir)
    today_stamp = date.today().strftime('%Y%m%d')
    today_log_filename = log_filename_tmp.format(today_stamp=today_stamp)
    found_logs = fnmatch.filter(logs_in_dir, today_log_filename)
    return found_logs[0] if found_logs else None


def read_log(log_filepath):
    log_filetype, log_encoding = mimetypes.guess_type(log_filepath)

    if log_filetype == 'text/plain':
        log_fileobj = open(log_filepath)
    elif log_encoding == 'gzip':
        log_fileobj = gzip.GzipFile(log_filepath)
    else:
        return
    for log_line in log_fileobj:
        yield log_line
    log_fileobj.close()


def is_filepath(path):
    if not os.path.isfile(path):
        raise argparse.ArgumentTypeError(
            "The config file doesn't exist or the path is incorrect"
        )
    return path


def get_args():
    parser = argparse.ArgumentParser(
        description='Nginx log parser and analyzer'
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


def main(args, log=None, config=None):
    logger = log if log else logging

    if config is None:
        logger.error('Config was not found. Terminating script...')
        return

    log_filepath = get_log_filepath()
    logger.info('log_filepath: %s', log_filepath)
    # print(log_filepath)

    # if not log_filepath:
    #     print("No log files was found.")
    #     return
    #
    # print('log_filepath: ', log_filepath)
    # logfile = read_logfile(log_filepath)
    # for line in logfile:
    #     print(line)


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
        main(args, log=log, config=config)
    except BaseException:
        log.exception('Critical error. Terminating script...')
