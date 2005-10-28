##############################################################################
#
# PlonePAS - Adapt PluggableAuthService for use in Plone
# Copyright (C) 2005 Enfold Systems, Kapil Thangavelu, et al
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this
# distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""
$Id$
"""

import types
import sys
import zLOG

PROJECTNAME = 'PlonePAS'
GLOBALS = globals()

PAS_INSIDE_GRUF = True

DEFAULT_CHALLENGE_PROTOCOL = ['http']
DEFAULT_PROTO_MAPPING = {'WebDAV': DEFAULT_CHALLENGE_PROTOCOL,
                         'FTP': DEFAULT_CHALLENGE_PROTOCOL,
                         'XML-RPC': DEFAULT_CHALLENGE_PROTOCOL}

class Logger:

    def __init__(self, name=PROJECTNAME):
        self.name = name

    def log(self, level, msg, *args, **kw):
        exc_info = kw.get("exc_info")

        if exc_info == 1:
            exc_info = sys.exc_info()

        if exc_info == (None, None, None):
            exc_info = None

        # Code and comments below for handling special arguments to
        # format msg are copied from Python's 'logging' module.'

        # The following statement allows passing of a dictionary as a sole
        # argument, so that you can do something like
        #  logging.debug("a %(a)d b %(b)s", {'a':1, 'b':2})
        # Suggested by Stefan Behnel.
        # Note that without the test for args[0], we get a problem because
        # during formatting, we test to see if the arg is present using
        # 'if self.args:'. If the event being logged is e.g. 'Value is %d'
        # and if the passed arg fails 'if self.args:' then no formatting
        # is done. For example, logger.warn('Value is %d', 0) would log
        # 'Value is %d' instead of 'Value is 0'.
        # For the use case of passing a dictionary, this should not be a
        # problem.
        if (args and (len(args) == 1) and args[0]
            and (type(args[0]) == types.DictType)):
            args = args[0]

        # If positional arguments have been provided, its very likely
        # they are for interpolating with the message
        if args:
            msg = msg % args

        self._log(self.name, level, msg, error=exc_info)
        del exc_info

    def _log(self, name, level, msg, error):
        zLOG.LOG(name, level, msg, error)

    def trace(self, msg, *args, **kw):
        self.log(zLOG.TRACE, msg, *args, **kw)

    def debug(self, msg, *args, **kw):
        self.log(zLOG.DEBUG, msg, *args, **kw)

    def info(self, msg, *args, **kw):
        self.log(zLOG.INFO, msg, *args, **kw)

    def warning(self, msg, *args, **kw):
        self.log(zLOG.WARNING, msg, *args, **kw)

    warn = warning

    def error(self, msg, *args, **kw):
        self.log(zLOG.ERROR, msg, *args, **kw)

    def fatal(self, msg, *args, **kw):
        self.log(zLOG.PANIC, msg, *args, **kw)

    critical = fatal

    def exception(self, msg, *args):
        self.error(msg, exc_info=1, *args)

logger = Logger()
