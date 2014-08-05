# Copyright 2012 Nebula, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
from __future__ import with_statement  # Python 2.5 compliance

import lockfile
import os
import random
import string


class FilePermissionError(Exception):
    """The key file permissions are insecure."""
    pass


def generate_key(key_length=64):
    """Secret key generator.

    The quality of randomness depends on operating system support,
    see http://docs.python.org/library/random.html#random.SystemRandom.
    """
    if hasattr(random, 'SystemRandom'):
        choice = random.SystemRandom().choice
    else:
        choice = random.choice
    return ''.join(map(lambda x: choice(string.digits + string.ascii_letters),
                       range(key_length)))


def generate_or_read_from_file(key_file='.secret_key', key_length=64):
    """Multiprocess-safe secret key file generator.

    Useful to replace the default (and thus unsafe) SECRET_KEY in settings.py
    upon first start. Save to use, i.e. when multiple Python interpreters
    serve the dashboard Django application (e.g. in a mod_wsgi + daemonized
    environment).  Also checks if file permissions are set correctly and
    throws an exception if not.
    """
    lock = lockfile.FileLock(key_file)
    # with lock:
    if not lock.is_locked():
        if not os.path.exists(key_file):
            key = generate_key(key_length)
            old_umask = os.umask(0o177)  # Use '0600' file permissions
            with open(key_file, 'w') as f:
                f.write(key)
            os.umask(old_umask)
        else:
            if oct(os.stat(key_file).st_mode & 0o777) != '0600':
                raise FilePermissionError("Insecure key file permissions!")
            with open(key_file, 'r') as f:
                key = f.readline()
        return key
