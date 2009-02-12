from setuptools import setup, find_packages

version = '3.9'

setup(name='Products.PlonePAS',
      version=version,
      description="PlonePAS adapts the PluggableAuthService for use by Plone.",
      long_description="""\
      """,
      classifiers=[
        "Framework :: Plone",
        "Framework :: Zope2",
        "Programming Language :: Python",
      ],
      keywords='Zope CMF Plone PAS authentication',
      author='Kapil Thangavelu, Wichert Akkerman',
      author_email='plone-developers@lists.sourceforge.net',
      url='http://svn.plone.org/svn/collective/Products.PlonePAS/trunk',
      license='ZPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['Products'],
      include_package_data=True,
      zip_safe=False,
      download_url='http://plone.org/products/plonepas',
      install_requires=[
        'setuptools',
        'Products.GenericSetup',
        'plone.memoize',
        'plone.openid',
      ],
)
