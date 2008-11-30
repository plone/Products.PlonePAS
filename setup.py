from setuptools import setup, find_packages

version = '4.0'

setup(name='Products.PlonePAS',
      version=version,
      description="PlonePAS adapts the PluggableAuthService for use by Plone.",
      long_description="""\
      """,
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
      install_requires=[
        'setuptools',
        'plone.memoize',
      ],
)
