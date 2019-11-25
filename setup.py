# -*- coding: utf-8 -*-
from setuptools import setup
from setuptools import find_packages
import sys

version = '6.0.3'

longdescription = open("README.rst").read()
longdescription += '\n'
longdescription += open("CHANGES.rst").read()

install_requires = [
        'DateTime',
        'plone.i18n',
        'plone.memoize',
        'plone.protect>=2.0.3',
        'plone.registry',
        'plone.session',
        'Products.CMFCore',
        'Products.GenericSetup',
        'Products.PluggableAuthService>=2.0b2.dev0',
        'setuptools',
        'six',
        'zope.component',
        'zope.deprecation',
        'Zope',
    ]

setup(
    name='Products.PlonePAS',
    version=version,
    description="PlonePAS modifies the PluggableAuthService for use by Plone.",
    long_description=longdescription,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Framework :: Plone",
        "Framework :: Plone :: 5.2",
        "Framework :: Zope2",
        "Framework :: Zope :: 4",
        "License :: OSI Approved :: Zope Public License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
    keywords='Zope CMF Plone PAS authentication',
    author='Kapil Thangavelu, Wichert Akkerman',
    author_email='plone-developers@lists.sourceforge.net',
    url='https://pypi.org/project/Products.PlonePAS',
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
            'plone.app.robotframework',
        ],
    ),
)
