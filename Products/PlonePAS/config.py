PROJECTNAME = 'PlonePAS'
GLOBALS = globals()

PAS_INSIDE_GRUF = True

DEFAULT_CHALLENGE_PROTOCOL = ['http']
DEFAULT_PROTO_MAPPING = {'WebDAV': DEFAULT_CHALLENGE_PROTOCOL,
                         'FTP': DEFAULT_CHALLENGE_PROTOCOL,
                         'XML-RPC': DEFAULT_CHALLENGE_PROTOCOL}

# Settings for member image resize quality
from PIL import Image

PIL_SCALING_ALGO = Image.ANTIALIAS
PIL_QUALITY = 88
MEMBER_IMAGE_SCALE = (75, 100)
IMAGE_SCALE_PARAMS = {'scale': MEMBER_IMAGE_SCALE,
                      'quality': PIL_QUALITY,
                      'algorithm': PIL_SCALING_ALGO,
                      'default_format': 'PNG'}
