from setuptools import setup, find_packages

version = '4.0.11'

setup(name='Products.PlonePAS',
      version=version,
      description="PlonePAS adapts the PluggableAuthService for use by Plone.",
      long_description=open("README.txt").read() + "\n" + \
                       open("CHANGES.txt").read(),
      classifiers=[
        "Framework :: Plone",
        "Framework :: Zope2",
      ],
      keywords='Zope CMF Plone PAS authentication',
      author='Kapil Thangavelu, Wichert Akkerman',
      author_email='plone-developers@lists.sourceforge.net',
      url='http://pypi.python.org/pypi/Products.PlonePAS',
      license='ZPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['Products'],
      include_package_data=True,
      zip_safe=False,
      extras_require=dict(
        test=[
            'Products.PloneTestCase',
            'Products.Archetypes',
        ],
        atstorage=[
            'Products.Archetypes',
        ]
      ),
      install_requires=[
        'setuptools',
        'plone.memoize',
        'plone.session',
        'plone.i18n',
        'Products.CMFCore',
        'Products.GenericSetup',
        'Products.PluggableAuthService',
        'Zope2 > 2.12.4',
      ],
)
