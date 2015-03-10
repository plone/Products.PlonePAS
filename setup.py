# -*- coding: utf-8 -*-
from setuptools import setup
from setuptools import find_packages

version = '5.0.1.dev0'

longdescription = open("README.rst").read()
longdescription += '\n'
longdescription += open("CHANGES.rst").read()

setup(
    name='Products.PlonePAS',
    version=version,
    description="PlonePAS adapts the PluggableAuthService for use by Plone.",
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
    packages=find_packages(exclude=['ez_setup']),
    namespace_packages=['Products'],
    clude_package_data=True,
    zip_safe=False,
    install_requires=[
        'Products.CMFCore',
        'Products.GenericSetup',
        'Products.PluggableAuthService',
        'Zope2 > 2.13.22',
        'plone.i18n',
        'plone.memoize',
        'plone.session',
        'setuptools',
        'zope.deprecation',
    ],
    extras_require=dict(
        test=[
            'plone.app.testing',
            'plone.testing',
        ],
    ),
)
