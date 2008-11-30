import logging

logger = logging.getLogger('PlonePAS')


PATTERN = '__PlonePAS_%s__'
def call(self, __name__, *args, **kw):
    return getattr(self, PATTERN % __name__)(*args, **kw)

WRAPPER = '__PlonePAS_is_wrapper_method__'
ORIG_NAME = '__PlonePAS_original_method_name__'
def isWrapperMethod(meth):
    return getattr(meth, WRAPPER, False)

def wrap_method(klass, name, method, pattern=PATTERN):
    old_method = getattr(klass, name)
    if isWrapperMethod(old_method):
        logger.info('PlonePAS: *NOT* wrapping already wrapped method at %s.%s',
            klass.__name__, name)
        return
    else:
        logger.info('PlonePAS: Wrapping method at %s.%s', klass.__name__, name)
    new_name = pattern % name
    setattr(klass, new_name, old_method)
    setattr(method, ORIG_NAME, new_name)
    setattr(method, WRAPPER, True)
    setattr(klass, name, method)

def unwrap_method(klass, name):
    old_method = getattr(klass, name)
    if not isWrapperMethod(old_method):
        raise ValueError, ('Trying to unwrap non-wrapped '
                           'method at %s.%s' % (klass.__name__, name))
    orig_name = getattr(old_method, ORIG_NAME)
    new_method = getattr(klass, orig_name)
    delattr(klass, orig_name)
    setattr(klass, name, new_method)
