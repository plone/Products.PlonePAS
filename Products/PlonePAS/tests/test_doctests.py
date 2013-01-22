import unittest
from Testing import ZopeTestCase

from zExceptions.ExceptionFormatter import format_exception
from ZPublisher.HTTPResponse import HTTPResponse

from Products.PlonePAS.tests import base


# Silence Plone's handling of exceptions
orig_exception = HTTPResponse.exception
def exception(self, **kw):
    def tag_search(*args):
        return False
    kw['tag_search'] = tag_search
    return orig_exception(self, **kw)


orig_setBody = HTTPResponse.setBody
def setBody(self, *args, **kw):
    kw['is_error'] = 0
    try:
        arg_length = len(args[0])
    except TypeError:
        # The first argument can be None with status: 302 Moved Temporarily.
        # Or you get a 'Products.Five.metaclass.AuthenticatorView object'.
        # Or maybe other exceptions.
        pass
    else:
        if arg_length == 2:
            title, body = args[0]
            args = (body,) + args[1:]
    return orig_setBody(self, *args, **kw)


def _traceback(self, t, v, tb, as_html=1):
    return ''.join(format_exception(t, v, tb, as_html=as_html))

# These are suspicious and hopefully not needed anymore.  The first
# one causes a test failure in Products.CMFPlone redirection.txt when
# those tests are run in combination with PlonePAS.  No test failures
# come up when I comment it out.
#HTTPResponse._error_format = 'text/plain'
HTTPResponse._traceback = _traceback
HTTPResponse.exception = exception
HTTPResponse.setBody = setBody


def test_suite():
    suite = unittest.TestSuite()
    DocFileSuite = ZopeTestCase.FunctionalDocFileSuite
    DocTestSuite = ZopeTestCase.FunctionalDocTestSuite
    tests = (
        ('cookie_auth.txt', base.FunctionalTestCase),
        )

    for fname, klass in tests:
        t = DocFileSuite(fname,
                         test_class=klass,
                         package='Products.PlonePAS.tests')
        suite.addTest(t)
    suite.addTest(DocTestSuite('Products.PlonePAS.utils')),
    return suite
