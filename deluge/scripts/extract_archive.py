#!/usr/bin/env python2

import sys
import logging
import os
from os.path import isfile, join

logger = logging.getLogger('extract_archive')
logger.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

file_handler = logging.FileHandler(filename='/config/extract_archive.log')
console_handler.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)
logger.addHandler(console_handler)
logger.addHandler(file_handler)


def can_extract(filename, formats):
    filename, file_ext = os.path.splitext(filename)
    return file_ext in formats


if len(sys.argv) < 4:
    logger.error('Invalid parameters [%s]', sys.argv)
    sys.exit(1)

torrent_id = sys.argv[1]
torrent_name = sys.argv[2]
save_path = sys.argv[3]

logger.debug('Checking extract necessity 1:[%s] 2:[%s] 3:[%s]', torrent_id, torrent_name, save_path)

formats = ['zip', 'rar']

os.chdir(save_path)
files = [f for f in os.listdir('.') if isfile(join('.', f)) and can_extract(f, formats)]

if len(files) == 0:
    logger.info('No files can be extracted for torrent [%s]', torrent_name)
    sys.exit(0)


sys.exit(0)
