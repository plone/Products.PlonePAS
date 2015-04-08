# -*- coding: utf-8 -*-
from zope.deprecation import deprecation
import logging

logger = logging.getLogger('PlonePAS')

PATTERN = '__PlonePAS_%s__'


def call(self, __name__, *args, **kw):
    return getattr(self, PATTERN % __name__)(*args, **kw)


WRAPPER = '__PlonePAS_is_wrapper_method__'
ADDED = '__PlonePAS_is_added_method__'
ORIG_NAME = '__PlonePAS_original_method_name__'

_marker = dict()


def isWrapperMethod(meth):
    return getattr(meth, WRAPPER, False)


def wrap_method(klass, name, method,
                pattern=PATTERN, add=False, roles=None, deprecated=False):
    """takes a method and set it to a class. Annotates with hints what happened.
    """
    new_name = pattern % name
    if not add:
        old_method = getattr(klass, name)
        if isWrapperMethod(old_method):
            logger.warn(
                'PlonePAS: *NOT* wrapping already wrapped method at '
                '{0}.{1}'.format(
                    klass.__name__, name)
            )

            return
        logger.debug(
            'PlonePAS: Wrapping method at %s.%s',
            klass.__name__, name
        )
        setattr(klass, new_name, old_method)
        setattr(method, ORIG_NAME, new_name)
        setattr(method, WRAPPER, True)
        setattr(method, ADDED, False)
    else:
        logger.debug('PlonePAS: Adding method at %s.%s', klass.__name__, name)
        setattr(method, WRAPPER, False)
        setattr(method, ADDED, True)

    if deprecated:
        setattr(klass, name, deprecation.deprecated(method, deprecated))
    else:
        setattr(klass, name, method)

    if roles is not None:
        roles_attr = '{0}__roles__'.format(name)
        logger.debug(
            'PlonePAS: Setting new permission roles at {0}.{1}'.format(
                klass.__name__, name
            )
        )
        setattr(klass, roles_attr, roles)


def unwrap_method(klass, name):
    # seems to be dead code, nowwhere used nor tested
    old_method = getattr(klass, name)
    if not isWrapperMethod(old_method):
        raise ValueError('Trying to unwrap non-wrapped '
                         'method at %s.%s' % (klass.__name__, name))
    orig_name = getattr(old_method, ORIG_NAME)
    new_method = getattr(klass, orig_name)
    delattr(klass, orig_name)
    setattr(klass, name, new_method)
