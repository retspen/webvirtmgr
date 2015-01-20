# -*- coding: utf-8 -*-
#
# This class provide from VirtManager project, from console.py
# file.
#
# Copyright (C) 2006-2008 Red Hat, Inc.
# Copyright (C) 2006 Daniel P. Berrange <berrange@redhat.com>
# Copyright (C) 2010 Marc-André Lureau <marcandre.lureau@redhat.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
# MA 02110-1301 USA.
#

import os
import socket
import signal
import logging


class Tunnel(object):
    def __init__(self):
        self.outfd = None
        self.errfd = None
        self.pid = None

    def open(self, connhost, connuser, connport, gaddr, gport, gsocket):
        if self.outfd is not None:
            return -1

        # Build SSH cmd
        argv = ["ssh", "ssh"]
        if connport:
            argv += ["-p", str(connport)]

        if connuser:
            argv += ['-l', connuser]

        argv += [connhost]

        # Build 'nc' command run on the remote host
        #
        # This ugly thing is a shell script to detect availability of
        # the -q option for 'nc': debian and suse based distros need this
        # flag to ensure the remote nc will exit on EOF, so it will go away
        # when we close the VNC tunnel. If it doesn't go away, subsequent
        # VNC connection attempts will hang.
        #
        # Fedora's 'nc' doesn't have this option, and apparently defaults
        # to the desired behavior.
        #
        if gsocket:
            nc_params = "-U %s" % gsocket
        else:
            nc_params = "%s %s" % (gaddr, gport)

        nc_cmd = (
            """nc -q 2>&1 | grep "requires an argument" >/dev/null;"""
            """if [ $? -eq 0 ] ; then"""
            """   CMD="nc -q 0 %(nc_params)s";"""
            """else"""
            """   CMD="nc %(nc_params)s";"""
            """fi;"""
            """eval "$CMD";""" %
            {'nc_params': nc_params})

        argv.append("sh -c")
        argv.append("'%s'" % nc_cmd)

        argv_str = reduce(lambda x, y: x + " " + y, argv[1:])
        logging.debug("Creating SSH tunnel: %s", argv_str)

        fds = socket.socketpair()
        errorfds = socket.socketpair()

        pid = os.fork()
        if pid == 0:
            fds[0].close()
            errorfds[0].close()

            os.close(0)
            os.close(1)
            os.close(2)
            os.dup(fds[1].fileno())
            os.dup(fds[1].fileno())
            os.dup(errorfds[1].fileno())
            os.execlp(*argv)
            os._exit(1)
        else:
            fds[1].close()
            errorfds[1].close()

        logging.debug("Tunnel PID=%d OUTFD=%d ERRFD=%d",
                      pid, fds[0].fileno(), errorfds[0].fileno())
        errorfds[0].setblocking(0)

        self.outfd = fds[0]
        self.errfd = errorfds[0]
        self.pid = pid

        fd = fds[0].fileno()
        if fd < 0:
            raise SystemError("can't open a new tunnel: fd=%d" % fd)
        return fd

    def close(self):
        if self.outfd is None:
            return

        logging.debug("Shutting down tunnel PID=%d OUTFD=%d ERRFD=%d",
                      self.pid, self.outfd.fileno(),
                      self.errfd.fileno())
        self.outfd.close()
        self.outfd = None
        self.errfd.close()
        self.errfd = None

        os.kill(self.pid, signal.SIGKILL)
        self.pid = None

    def get_err_output(self):
        errout = ""
        while True:
            try:
                new = self.errfd.recv(1024)
            except:
                break

            if not new:
                break

            errout += new

        return errout
