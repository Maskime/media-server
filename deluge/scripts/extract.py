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


logger = logger_create('extract_archive', 'extract_archive.log')

if not os.path.exists('runs.db') or not os.path.isfile('runs.db'):
    with open('runs.db', 'w+') as db:
        db.write('[]')


def extract_zip(filepath, extract_log):
    """
    Execute the zip command extraction
    :param extract_log: logger to use for the extraction
    :param filepath: file to extract
    """
    logger.debug('Extracting ZIP')
    try:
        result = subprocess.check_output(['unzip', '-u', filepath], stderr=subprocess.STDOUT)
        extract_log.info(result)
        return True
    except Exception as error:
        logger.error('An error occurred when extracting zip', error)
        extract_log.error('An error occurred when extracting zip', error)
        return False


def extract_rar(filepath, extract_log):
    """
    Execute the rar command extraction
    :param extract_log: logger to use for this extraction
    :param filepath: file to extract
    :return:
    """
    logger.debug('Extracting RAR')
    try:
        result = subprocess.check_output(['unrar', '-o-', 'e', filepath], stderr=subprocess.STDOUT)
        extract_log.info(result)
        return True
    except Exception as error:
        logger.error('An error occurred when extracting rar', error)
        extract_log.error('An error occurred when extracting rar', error)
        return False


archive_types = ['.zip', '.rar']
extractors = {
    '.zip': extract_zip,
    '.rar': extract_rar
}


def is_extensionwithin(filename, types):
    """
    Check if the filename has an extension that within the list
    :param filename: filename to check
    :param types: list of extenstions
    :return: True if filename has an extension within the list False otherwise
    """
    return get_extension(filename) in types


def get_extension(filename):
    """
    Get the extension associated to the filename
    :param filename: filename from which we'd like to find the extension for
    :return: filename extension
    """
    filename, file_ext = os.path.splitext(filename)
    return file_ext


def check_pid(pid_to_check):
    """
    Check if the PID is valid (ie: is in list of current process)
    :param pid_to_check: pid to check
    :return: True if it's in the list, False otherwise
    """
    try:
        os.kill(pid_to_check, 0)
        return True
    except OSError:
        return False


def runfile_getcontent(has_lock=False):
    """
    Get the content of the runfile db
    :return: Content of the runfile db
    """
    if has_lock:
        with open('runs.db', 'r') as db_file:
            runs = json.load(db_file)
    else:
        with FileLock('runs.db'):
            with open('runs.db', 'r') as db_file:
                runs = json.load(db_file)

    return runs


def runfile_writecontent(runs, has_lock=False):
    """
    Rewrite the content of the runfile db file
    :param runs: object to serialize to the file
    """
    if has_lock:
        with open('runs.db', 'w+') as db_file:
            json.dump(runs, db_file)
    else:
        with FileLock('runs.db'):
            with open('runs.db', 'w+') as db_file:
                json.dump(runs, db_file)


def runfile_add(torrent_id, torrent_name, save_path):
    """
    Add an element to the runfile db
    :param torrent_id: torrent id
    :param torrent_name: torrent name
    :param save_path: save path
    """
    with FileLock('runs.db'):
        runs = runfile_getcontent(has_lock=True)
        runs.append({
            'torrent_id': torrent_id,
            'torrent_name': torrent_name,
            'save_path': save_path,
            'state': 'queued',
            'timestamp': time.time()
        })
        runfile_writecontent(runs, has_lock=True)


def runfile_hasnext():
    """
    Check if the runfile is empty
    :return: True if the runfile has other elements, False otherwise
    """
    with FileLock('runs.db'):
        db_content = runfile_getcontent(has_lock=True)
        return len(db_content) > 0


def runfile_getnext():
    """
    Get the next element in the runfile db
    :return: next element
    """
    with FileLock('runs.db'):
        entry_next = runfile_getcontent(has_lock=True)[0]
        return entry_next['torrent_id'], entry_next['torrent_name'], entry_next['save_path']


def failedfile_handle(archive, failed_filepath):
    """
    Handles failed files
    :param archive: archive that has failed
    :param failed_filepath: the failed marker file
    """
    with open(failed_filepath, 'r') as fail_file:
        fail_data = json.load(fail_file)
    max_try = 3
    time_between_try = 120.0
    should_extract = True
    if fail_data['count'] >= max_try:
        should_extract = False
        logger.info(
            'Will not try to extract file [{}] as we already tried [{}] times and it failed every time'.format(archive,
                                                                                                               max_try))
    elif (time.time() - fail_data['last_try']) < time_between_try:
        should_extract = False
        logger.info('Will not try to extract file [{}] as last attempt was less than [{}] seconds ago'.format(archive,
                                                                                                              time_between_try))
    if should_extract:
        start_extract(archive)
    else:
        logger.info(
            'If you changed something and would like to retry, delete the file [{}] and the script will re-try'.format(
                failed_filepath))


def failedfile_update(archive_path):
    """
    Create/update failed file for the given archive
    :param archive_path: archive which we should create the failed file for
    """
    filepath, ext = os.path.splitext(archive_path)
    fail_filepath = filepath + ".failed"
    if os.path.exists(fail_filepath) and os.path.isfile(fail_filepath):
        with open(fail_filepath, 'r') as fail_file:
            fail_data = json.load(fail_file)
    else:
        fail_data = {
            'count': 0,
            'last_try': 0
        }
    fail_data['count'] += 1
    fail_data['last_try'] = time.time()
    with open(fail_filepath, 'w+') as fail_file:
        json.dump(fail_data, fail_file)


def watchdog(torrent_id, torrent_name, save_path):
    """
    Check if there already is an instance of the extractor running.
    If there is one, will add the sent parameters to the runfile db so that the current instance will pick-it up
    for extraction and will stop the new instance.
    :param torrent_id: torrent id
    :param torrent_name: torrent name
    :param save_path: save path
    """
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
    """
    Get the marker file type
    :param filename: marker file name
    :return: will return ['in_progress' | 'done' | 'failed']
    """
    return get_extension(filename).replace('.', '')


def get_markers(marked_file):
    """
    Look in the marked_file directory to see if it finds any markers file.
    :param marked_file: File that should have been marked
    :return: a dictionary with the found markers by type.
    """
    dir_archive = os.path.dirname(marked_file)
    return {get_marker(f): f for marker_file in os.listdir(dir_archive) if
            is_extensionwithin(marker_file, ['.in_progress', '.done', '.failed'])}


def start_extract(archive_path):
    """
    Starts the extraction process for the given file
    :param archive_path: archive to extract
    :return:
    """
    filename = os.path.basename(archive_path)
    log_dir = os.path.dirname(archive_path)
    tag, file_ext = os.path.splitext(filename)
    log_file = os.path.join(log_dir, tag + ".in_progress")
    logger_extract = logger_create(log_tag=tag, log_file=log_file)
    try:
        result = extractors[file_ext](archive_path, logger_extract)
        if result:
            done_file = log_file.replace('.in_progress', '.done')
            os.rename(log_file, done_file)
        else:
            failedfile_update(archive_path)
    except Exception as ex:
        logger.error('An exception occurred when on extraction', ex)
        failedfile_update(archive_path)


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
    to_extract = []
    for root, dirs, files in os.walk('.'):
        archives = [f for f in files if is_extensionwithin(f, archive_types)]
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
                failedfile_handle(archive, markers['failed'])
            elif 'in_progress' in markers:
                logger.info('There is already an extraction in progress for this archive [{}]'.format(archive))

sys.exit(0)
