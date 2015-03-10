# -*- coding: utf-8 -*-
from setuptools import setup
from setuptools import find_packages

version = '5.0.1.dev0'

install_requires = [
        'Products.CMFCore',
        'Products.CMFDefault',
        'Products.GenericSetup',
        'Products.PluggableAuthService',
        'Zope2 > 2.12.4',
        'plone.i18n',
        'plone.memoize',
        'plone.session',
        'setuptools',
        'zope.deprecation',
      ]

try:
    from collections import OrderedDict  # noqa
except ImportError:
    install_requires.append('ordereddict')

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
    extras_require=dict(
        test=[
            'plone.app.testing',
            'plone.testing',
            'Products.Archetypes',
        ],
        atstorage=[
            'Products.Archetypes',
        ]
    ),
    install_requires=install_requires,
)
