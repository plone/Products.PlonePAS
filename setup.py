# -*- coding: utf-8 -*-
from setuptools import setup
from setuptools import find_packages

version = '5.0.2'

longdescription = open("README.rst").read()
longdescription += '\n'
longdescription += open("CHANGES.rst").read()

setup(
    name='Products.PlonePAS',
    version=version,
    description="PlonePAS modifies the PluggableAuthService for use by Plone.",
    long_description=longdescription,
    classifiers=[
        "Framework :: Plone",
        "Framework :: Zope2",
    ],
    keywords='Zope CMF Plone PAS authentication',
    author='Kapil Thangavelu, Wichert Akkerman',
    author_email='plone-developers@lists.sourceforge.net',
    url='http://pypi.python.org/pypi/Products.PlonePAS',
    license='ZPL',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    namespace_packages=['Products'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'Products.CMFCore',
        'Products.GenericSetup',
        'Products.PluggableAuthService',
        'Zope2 >=2.13.22',
        'plone.i18n',
        'plone.memoize',
        'plone.session',
        'setuptools',
        'zope.deprecation',
        'plone.protect'
    ],
    extras_require=dict(
        test=[
            'plone.app.testing',
            'plone.testing',
        ],
    ),
)
