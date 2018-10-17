#!/usr/bin/env python2
import logging
import os
import sys
import time

script_filesroot = '/config'


def logger_create(log_tag, log_file):
    new_logger = logging.getLogger(log_tag)
    new_logger.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)

    file_handler = logging.FileHandler(filename=log_file)
    console_handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    new_logger.addHandler(console_handler)
    new_logger.addHandler(file_handler)
    return new_logger


logger = logger_create('mark_complete', os.path.join(script_filesroot, 'mark_complete.log'))

if len(sys.argv) < 4:
    logger.error('Invalid parameters [%s]', sys.argv)
    sys.exit(1)

torrent_id = sys.argv[1]
torrent_name = sys.argv[2]
save_path = sys.argv[3]

torrent_path = os.path.join(save_path, torrent_name)

if not os.path.exists(torrent_path):
    logger.error('Could not find torrent path at [{}]'.format(torrent_path))
    sys.exit(1)

basename = os.path.basename(torrent_path)
if os.path.isfile(torrent_path) or os.path.isdir(torrent_path):
    mark_filepath = os.path.join(os.path.dirname(torrent_path), basename + '.completed')
else:
    logger.error('Invalid node type [{}], not a dir or a file'.format(torrent_path))
    sys.exit(2)

if os.path.exists(mark_filepath):
    logger.info('Mark file [{}] already exists, do nothing'.format(mark_filepath))
else:
    logger.info('Creating file [{}], for extract script'.format(mark_filepath))
    with open(mark_filepath, 'w+') as mark_file:
        mark_file.write(str(time.time()))
