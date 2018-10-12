#!/usr/bin/env python2

import sys
import logging
import os
from os.path import isfile, join
import subprocess

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


def can_extract(filename, types):
    return get_extension(filename) in types


def get_extension(filename):
    filename, file_ext = os.path.splitext(filename)
    return file_ext


def extract_zip(filepath):
    logger.debug('Extracting ZIP')
    try:
        result = subprocess.check_output(['unzip', '-u', filepath], stderr=subprocess.STDOUT)
        logger.info(result)
    except OSError as error:
        logger.error('An error occurred when extracting zip', error)


def extract_rar(filepath):
    logger.debug('Extracting RAR')
    try:
        result = subprocess.check_output(['unrar', '-o-', 'e', filepath], stderr=subprocess.STDOUT)
        logger.info(result)
    except OSError as error:
        logger.error('An error occurred when extracting rar', error)


def check_pid(pid_to_check):
    try:
        os.kill(pid_to_check, 0)
        return True
    except OSError:
        return False


def watchdog():
    pid_name = 'extract.pid'
    if os.path.exists(pid_name):
        with open(pid_name, 'r') as pid_file:
            pid = int(pid_file.read().replace('\n', ''))
            if check_pid(pid):
                logger.info("There's already an extractor running PID[{}] stop for now".format(pid))
                exit(1)
    with open(pid_name, 'w+') as pid_file:
        pid_file.write(str(os.getpid()))


if len(sys.argv) < 4:
    logger.error('Invalid parameters [%s]', sys.argv)
    sys.exit(1)

watchdog()

torrent_id = sys.argv[1]
torrent_name = sys.argv[2]
save_path = sys.argv[3]

logger.debug('Checking extract necessity 1:[%s] 2:[%s] 3:[%s]', torrent_id, torrent_name, save_path)

archive_types = ['.zip', '.rar']
extractors = {
    '.zip': extract_zip,
    '.rar': extract_rar
}

os.chdir(save_path)
"""
Avant toutes choses, il faut mettre un marker pour le watchdog
Donc, le save_path va en fait contenir le dossier dans lequel, le torrent a ete telecharge
soit la racine de tous les telechargements.
Il faut donc en fait parcourir ce dossier et ces enfants a la recherche d'une archive
Si on trouve une archive, il faut :
    0. verifier l'existence d'un marker:
        Si marker == en cours, alors ne rien faire
        Si marker == fait, alors ne rien faire
        Si marker == failed, 
            verifier le nombre de tentative qui a ete faite
                si < 3, alors retenter l'extration
                sinon, mettre a jour le marker en incrementant le nb tentative
    1. mettre un marker pour dire qu'on est en train de le traiter
    2. faire l'extraction
        Si extraction OK, alors renommer le marker pour dire que l'extraction a ete faite
        Sinon, renommer le marker pour dire que l'extraction a echouee
"""
to_extract = []
for root, dirs, files in os.walk('.'):
    archives = [f for f in files if can_extract(f, archive_types)]
    logger.debug('[{}][{}]'.format(root, archives))
    if len(archives) > 0:
        path_archives = [join(root, p) for p in archives]
        to_extract = to_extract + path_archives
logger.info("Will extract [{}]".format(to_extract))
# if len(archives) == 0:
#     logger.info('No files can be extracted for torrent [%s]', torrent_name)
#     sys.exit(0)
#
# for archive in archives:
#     path_archive = join(save_path, archive)
#     logger.info('Extracting: [{}]'.format(path_archive))
#     archive_type = get_extension(archive)
#     extractors[archive_type](path_archive)

sys.exit(0)
