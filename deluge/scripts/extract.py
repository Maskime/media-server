#!/usr/bin/env python2

from __future__ import print_function
import json
import logging
import subprocess
from os.path import join

import os
import sys
import time
import errno


class FileLock(object):
    """ A file locking mechanism that has context-manager support so
        you can use it in a ``with`` statement. This should be relatively cross
        compatible as it doesn't rely on ``msvcrt`` or ``fcntl`` for the locking.
    """

    class FileLockException(Exception):
        pass

    def __init__(self, protected_file_path, timeout=None, delay=1, lock_file_contents=None):
        """ Prepare the file locker. Specify the file to lock and optionally
            the maximum timeout and the delay between each attempt to lock.
        """
        self.is_locked = False
        self.lockfile = protected_file_path + ".lock"
        self.timeout = timeout
        self.delay = delay
        self._lock_file_contents = lock_file_contents
        if self._lock_file_contents is None:
            self._lock_file_contents = "Owning process args:\n"
            for arg in sys.argv:
                self._lock_file_contents += arg + "\n"

    def locked(self):
        """
        Returns True iff the file is owned by THIS FileLock instance.
        (Even if this returns false, the file could be owned by another FileLock instance, possibly in a different thread or process).
        """
        return self.is_locked

    def available(self):
        """
        Returns True iff the file is currently available to be locked.
        """
        return not os.path.exists(self.lockfile)

    def acquire(self, blocking=True):
        """ Acquire the lock, if possible. If the lock is in use, and `blocking` is False, return False.
            Otherwise, check again every `self.delay` seconds until it either gets the lock or
            exceeds `timeout` number of seconds, in which case it raises an exception.
        """
        start_time = time.time()
        while True:
            try:
                # Attempt to create the lockfile.
                # These flags cause os.open to raise an OSError if the file already exists.
                fd = os.open(self.lockfile, os.O_CREAT | os.O_EXCL | os.O_RDWR)
                with os.fdopen(fd, 'a') as f:
                    # Print some info about the current process as debug info for anyone who bothers to look.
                    f.write(self._lock_file_contents)
                break
            except OSError as e:
                if e.errno != errno.EEXIST:
                    raise
                if self.timeout is not None and (time.time() - start_time) >= self.timeout:
                    raise FileLock.FileLockException("Timeout occurred.")
                if not blocking:
                    return False
                time.sleep(self.delay)
        self.is_locked = True
        return True

    def release(self):
        """ Get rid of the lock by deleting the lockfile.
            When working in a `with` statement, this gets automatically
            called at the end.
        """
        self.is_locked = False
        os.unlink(self.lockfile)

    def __enter__(self):
        """ Activated when used in the with statement.
            Should automatically acquire a lock to be used in the with block.
        """
        self.acquire()
        return self

    def __exit__(self, type, value, traceback):
        """ Activated at the end of the with statement.
            It automatically releases the lock if it isn't locked.
        """
        self.release()

    def __del__(self):
        """ Make sure this ``FileLock`` instance doesn't leave a .lock file
            lying around.
        """
        if self.is_locked:
            self.release()

    def purge(self):
        """
        For debug purposes only.  Removes the lock file from the hard disk.
        """
        if os.path.exists(self.lockfile):
            self.release()
            return True
        return False


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

if not os.path.exists('runs.db') or not os.path.isfile('runs.db'):
    with open('runs.db', 'w+') as db:
        db.write('[]')
db = FileLock('runs.db')


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


def runfile_getcontent():
    with db:
        with open('runs.db', 'r') as db_file:
            runs = json.load(db_file)
    return runs


def runfile_writecontent(runs):
    with db:
        with open('runs.db', 'w+') as db_file:
            json.dump(runs, db_file)


def runfile_add(torrent_id, torrent_name, save_path):
    with db:
        runs = runfile_getcontent()
        runs.append({
            'torrent_id': torrent_id,
            'torrent_name': torrent_name,
            'save_path': save_path,
            'state': 'queued',
            'timestamp': time.time()
        })
        runfile_writecontent(runs)

def runfile_hasnext():
    with db:

def watchdog(torrent_id, torrent_name, save_path):
    pid_name = 'extract.pid'
    if os.path.exists(pid_name):
        with open(pid_name, 'r') as pid_file:
            pid = int(pid_file.read().replace('\n', ''))

        if pid is not None and check_pid(pid):
            logger.info("There's already an extractor running PID[{}] stop for now".format(pid))
            runfile_add(torrent_id, torrent_name, save_path)
            exit(1)
    with open(pid_name, 'w+') as pid_file:
        pid_file.write(str(os.getpid()))


def get_marker(filename):
    return get_extension(filename).replace('.', '')


def get_markers(marked_file):
    dir_archive = os.path.dirname(marked_file)
    return {get_marker(f): f for marker_file in os.listdir(dir_archive) if
            get_extension(marker_file) in ['.in_progress', '.done', '.failed']}


def start_extract(archive_path):
    return None


archive_types = ['.zip', '.rar']
extractors = {
    '.zip': extract_zip,
    '.rar': extract_rar
}

if len(sys.argv) < 4:
    logger.error('Invalid parameters [%s]', sys.argv)
    sys.exit(1)

torrent_id = sys.argv[1]
torrent_name = sys.argv[2]
save_path = sys.argv[3]

watchdog(torrent_id, torrent_name, save_path)
runfile_add(torrent_id, torrent_name, save_path)

while runfile_hasnext():
    torrent_id, torrent_name, save_path = runfile_getnext()
    logger.debug('Checking extract necessity 1:[%s] 2:[%s] 3:[%s]', torrent_id, torrent_name, save_path)

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
    if len(to_extract) == 0:
        logger.info('No archive to extract')
        sys.exit(0)

    logger.info("Will extract [{}]".format(to_extract))
    for archive in to_extract:
        markers = get_markers(archive)
        if len(markers) == 0:
            start_extract(archive)
        else:
            if 'failed' in markers:
                handle_failedfile(archive, markers['failed'])
            elif 'in_progress' in markers:
                logger.info('There is already an extraction for this archive [{}]'.format(archive))

sys.exit(0)
