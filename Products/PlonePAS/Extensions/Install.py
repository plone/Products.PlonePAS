from StringIO import StringIO
from Products.CMFCore.utils import getToolByName
from Products.PlonePAS import config
from Products.Archetypes.Extensions.utils import install_subskin


def configurePlonePAS(portal, out):
    pass


def install(self):
    out = StringIO()
    portal = getToolByName(self, 'portal_url').getPortalObject()

    install_subskin(self, out, config.GLOBALS)
    print >> out, "Install skins."

    configurePlonePAS(portal, out)


    print >> out, "Successfully installed %s." % config.PROJECTNAME
    return out.getvalue()
