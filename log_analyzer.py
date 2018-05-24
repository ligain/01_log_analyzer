#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import mimetypes
import os
from datetime import date


# log_format ui_short '$remote_addr $remote_user $http_x_real_ip [$time_local] "$request" '
#                     '$status $body_bytes_sent "$http_referer" '
#                     '"$http_user_agent" "$http_x_forwarded_for" "$http_X_REQUEST_ID" "$http_X_RB_USER" '
#                     '$request_time';

DEFAULT_CONFIG = {
    "REPORT_SIZE": 1000,
    "REPORT_DIR": "./reports",
    "LOG_DIR": "./logs"
}


def get_config():
    pass


def get_log_filepath(logs_dir='../logs', log_filename_tmp='nginx-access-ui.log-{today_stamp}'):
    logs_in_dir = os.listdir(logs_dir)
    today_stamp = date.today().strftime("%Y%m%d")
    today_log_filename = log_filename_tmp.format(today_stamp=today_stamp)

    for log_file in logs_in_dir:
        if today_log_filename in log_file:
            return os.path.join(logs_dir, log_file)
        else:
            continue


def read_logfile(log_filepath):
    log_filetype, _ = mimetypes.guess_type(log_filepath)

    print(log_filetype)
    # with open(file, 'r') as log_file:
    #     pass


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


def main(args):
    log_filepath = get_log_filepath()


if __name__ == "__main__":
    args = get_args()
    main(args)
