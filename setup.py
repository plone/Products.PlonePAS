from setuptools import find_packages
from setuptools import setup

import sys


version = "7.0.0"


longdescription = open("README.rst").read()
longdescription += "\n"
longdescription += open("CHANGES.rst").read()

install_requires = [
    "plone.base",
    "plone.i18n",
    "plone.memoize",
    "plone.protect>=2.0.3",
    "plone.session",
    "Products.GenericSetup",
    "Products.PluggableAuthService>=2.0",
    "setuptools",
]

setup(
    name="Products.PlonePAS",
    version=version,
    description="PlonePAS modifies the PluggableAuthService for use by Plone.",
    long_description=longdescription,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Framework :: Plone",
        "Framework :: Plone :: 6.0",
        "Framework :: Plone :: Core",
        "Framework :: Zope",
        "Framework :: Zope :: 5",
        "License :: OSI Approved :: Zope Public License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    keywords="Zope CMF Plone PAS authentication",
    author="Kapil Thangavelu, Wichert Akkerman",
    author_email="plone-developers@lists.sourceforge.net",
    url="https://github.com/plone/Products.PlonePAS",
    license="ZPL",
    packages=find_packages("src"),
    package_dir={"": "src"},
    namespace_packages=["Products"],
    include_package_data=True,
    zip_safe=False,
    install_requires=install_requires,
    extras_require=dict(
        test=[
            "plone.app.testing",
            "plone.testing",
            "plone.app.robotframework",
        ],
    ),
)
