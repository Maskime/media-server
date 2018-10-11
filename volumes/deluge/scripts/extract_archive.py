#!/usr/bin/env python2

import sys
import logging

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

if len(sys.argv) < 4:
    logger.error('Invalid parameters [%s]', sys.argv)
    sys.exit(1)

torrent_id = sys.argv[1]
torrent_name = sys.argv[2]
save_path = sys.argv[3]

logger.debug('Received parameters 1:[%s] 2:[%s] 3:[%s]', torrent_id, torrent_name, save_path)



sys.exit(0)