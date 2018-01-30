# -*- coding: utf-8 -*-
from setuptools import setup
from setuptools import find_packages
import sys

version = '6.0.0.dev0'

longdescription = open("README.rst").read()
longdescription += '\n'
longdescription += open("CHANGES.rst").read()

install_requires = [
        'plone.i18n',
        'plone.memoize',
        'plone.protect>=2.0.3',
        'plone.session',
        'Products.CMFCore',
        'Products.GenericSetup',
        'Products.PluggableAuthService',
        'setuptools',
        'six',
        'zope.deprecation',
        'Zope2 >=2.13.22',
    ]

setup(
    name='Products.PlonePAS',
    version=version,
    description="PlonePAS modifies the PluggableAuthService for use by Plone.",
    long_description=longdescription,
    classifiers=[
        "Framework :: Plone",
        "Framework :: Plone :: 5.2",
        "Framework :: Zope2",
        "License :: OSI Approved :: Zope Public License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
    ],
    keywords='Zope CMF Plone PAS authentication',
    author='Kapil Thangavelu, Wichert Akkerman',
    author_email='plone-developers@lists.sourceforge.net',
    url='https://pypi.python.org/pypi/Products.PlonePAS',
    license='ZPL',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    namespace_packages=['Products'],
    include_package_data=True,
    zip_safe=False,
    install_requires=install_requires,
    extras_require=dict(
        test=[
            'plone.app.testing',
            'plone.testing',
        ],
    ),
)
