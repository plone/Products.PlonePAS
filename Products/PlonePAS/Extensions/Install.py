from StringIO import StringIO
from Products.CMFCore.utils import getToolByName


def configurePlonePAS(portal, out):
    pass


def install(self):
    out = StringIO()

    configurePlonePAS(portal, out)

    print >> out, "Successfully installed %s." % config.PROJECTNAME
    return out.getvalue()
