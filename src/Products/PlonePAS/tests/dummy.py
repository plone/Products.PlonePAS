# -*- coding: utf-8 -*-
from OFS.SimpleItem import SimpleItem
from ZPublisher.HTTPRequest import FileUpload

TEXT = 'file data'


class FieldStorage(object):
    def __init__(self, file, filename='testfile', headers=None):
        self.file = file
        if headers is None:
            headers = {}
        self.headers = headers
        self.filename = filename


class File(FileUpload):
    '''Dummy upload object
       Used to fake uploaded files.
    '''

    __allow_access_to_unprotected_subobjects__ = 1
    filename = 'dummy.txt'
    data = TEXT
    headers = {}

    def __init__(self, filename=None, data=None, headers=None):
        if filename is not None:
            self.filename = filename
        if data is not None:
            self.data = data
        if headers is not None:
            self.headers = headers

    def seek(self, *args):
        pass

    def tell(self, *args):
        return 1

    def read(self, *args):
        return self.data


class Error(Exception):
    '''Dummy exception'''


class Raiser(SimpleItem):
    '''Raises the stored exception when called'''

    exception = Error

    def __init__(self, exception=None):
        if exception is not None:
            self.exception = exception

    def __call__(self, *args, **kw):
        raise self.exception
