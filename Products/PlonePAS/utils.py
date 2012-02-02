from cStringIO import StringIO
from urllib import quote as url_quote
from urllib import unquote as url_unquote

from Products.CMFCore.utils import getToolByName
from Products.PlonePAS.config import IMAGE_SCALE_PARAMS
from Products.PluggableAuthService.interfaces.plugins import IGroupsPlugin

def unique(iterable):
    d = {}
    for i in iterable:
        d[i] = None
    return d.keys()

def getCharset(context):
    """Returns the site default charset, or utf-8.
    """
    properties = getToolByName(context, "portal_properties")
    site_properties = getattr(properties, 'site_properties', None)
    if site_properties is not None:
        return site_properties.getProperty('default_charset')
    return 'utf-8'

def cleanId(id):
    """'url_quote' turns strange chars into '%xx', which is not a valid char
    for ObjectManager. Here we encode '%' into '-' (and '-' into '--' as escaping).
    De-clean is possible; see 'decleanId'.
    Assumes that id can start with non-alpha(numeric), which is true.
    """
    __traceback_info__ = (id,)
    if id:
        # note: we provide the 'safe' param to get '/' encoded
        return url_quote(id, '').replace('-','--').replace('%','-')
    return ''

def decleanId(id):
   """Reverse cleanId."""
   if id:
       id = id.replace('--', '\x00').replace('-', '%').replace('\x00', '-')
       return url_unquote(id)
   return ''

def scale_image(image_file, max_size=None, default_format=None):
    """Scales an image down to at most max_size preserving aspect ratio
    from an input file

        >>> from Products.PlonePAS import config
        >>> import os
        >>> from StringIO import StringIO
        >>> from Products.PlonePAS.utils import scale_image
        >>> from PIL import Image

    Let's make a couple test images and see how it works (all are
    100x100), the gif is palletted mode::

        >>> pas_path = os.path.dirname(config.__file__)
        >>> pjoin = os.path.join
        >>> path = pjoin(pas_path, 'tests', 'images')
        >>> orig_jpg = open(pjoin(path, 'test.jpg'), 'rb')
        >>> orig_png = open(pjoin(path, 'test.png'), 'rb')
        >>> orig_gif = open(pjoin(path, 'test.gif'), 'rb')

    We'll also make some evil non-images, including one which
    masquerades as a jpeg (which would trick OFS.Image)::

        >>> invalid = StringIO('<div>Evil!!!</div>')
        >>> sneaky = StringIO('\377\330<div>Evil!!!</div>')

    OK, let's get to it, first check that our bad images fail:

        >>> scale_image(invalid, (50, 50))
        Traceback (most recent call last):
        ...
        IOError: cannot identify image file
        >>> scale_image(sneaky, (50, 50))
        Traceback (most recent call last):
        ...
        IOError: cannot identify image file

    Now that that's out of the way we check on our real images to make
    sure the format and mode are preserved, that they are scaled, and that they
    return the correct mimetype::

        >>> new_jpg, mimetype = scale_image(orig_jpg, (50, 50))
        >>> img = Image.open(new_jpg)
        >>> img.size
        (50, 50)
        >>> img.format
        'JPEG'
        >>> mimetype
        'image/jpeg'

        >>> new_png, mimetype = scale_image(orig_png, (50, 50))
        >>> img = Image.open(new_png)
        >>> img.size
        (50, 50)
        >>> img.format
        'PNG'
        >>> mimetype
        'image/png'

        >>> new_gif, mimetype = scale_image(orig_gif, (50, 50))
        >>> img = Image.open(new_gif)
        >>> img.size
        (50, 50)
        >>> img.format
        'GIF'
        >>> img.mode
        'P'
        >>> mimetype
        'image/gif'

    We should also preserve the aspect ratio by scaling to the given
    width only unless told not to (we need to reset out files before
    trying again though::

        >>> orig_jpg.seek(0)
        >>> new_jpg, mimetype = scale_image(orig_jpg, (70, 100))
        >>> img = Image.open(new_jpg)
        >>> img.size
        (70, 70)

        >>> orig_jpg.seek(0)
        >>> new_jpg, mimetype = scale_image(orig_jpg, (70, 50))
        >>> img = Image.open(new_jpg)
        >>> img.size
        (50, 50)

    """
    from PIL import Image
    
    if max_size is None:
        max_size = IMAGE_SCALE_PARAMS['scale']
    if default_format is None:
        default_format = IMAGE_SCALE_PARAMS['default_format']
    # Make sure we have ints
    size = (int(max_size[0]), int(max_size[1]))
    # Load up the image, don't try to catch errors, we want to fail miserably
    # on invalid images
    image = Image.open(image_file)
    # When might image.format not be true?
    format = image.format
    mimetype = 'image/%s'%format.lower()
    cur_size = image.size
    # from Archetypes ImageField
    # consider image mode when scaling
    # source images can be mode '1','L,','P','RGB(A)'
    # convert to greyscale or RGBA before scaling
    # preserve palletted mode (but not pallette)
    # for palletted-only image formats, e.g. GIF
    # PNG compression is OK for RGBA thumbnails
    original_mode = image.mode
    if original_mode == '1':
        image = image.convert('L')
    elif original_mode == 'P':
        image = image.convert('RGBA')
    # Rescale in place with an method that will not alter the aspect ratio
    # and will only shrink the image not enlarge it.
    image.thumbnail(size, resample=IMAGE_SCALE_PARAMS['algorithm'])
    # preserve palletted mode for GIF and PNG
    if original_mode == 'P' and format in ('GIF', 'PNG'):
        image = image.convert('P')
    # Save
    new_file = StringIO()
    image.save(new_file, format, quality=IMAGE_SCALE_PARAMS['quality'])
    new_file.seek(0)
    # Return the file data and the new mimetype
    return new_file, mimetype


def getGroupsForPrincipal(principal, plugins, request=None):
    groups = set()
    for iid, plugin in plugins.listPlugins(IGroupsPlugin):
        groups.update(plugin.getGroupsForPrincipal(principal, request))
    return list(groups)


def safe_unicode(value, encoding='utf-8'):
    """Converts a value to unicode, even it is already a unicode string.
    """
    if isinstance(value, unicode):
        return value
    elif isinstance(value, basestring):
        try:
            value = unicode(value, encoding)
        except UnicodeDecodeError:
            value = value.decode('utf-8', 'replace')
    return value


# Imported from Products.CMFCore.MemberdataTool as it has now been removed.
class CleanupTemp:
    """Used to cleanup _v_temps at the end of the request."""

    def __init__(self, tool):
        self._tool = tool

    def __del__(self):
        try:
            del self._tool._v_temps
        except (AttributeError, KeyError):
            # The object has already been deactivated.
            pass
