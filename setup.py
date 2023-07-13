from pathlib import Path
from setuptools import find_packages
from setuptools import setup


version = "8.0.2"

long_description = (
    f"{Path('README.rst').read_text()}\n{Path('CHANGES.rst').read_text()}"
)

install_requires = [
    "AuthEncoding",
    "BTrees",
    "Pillow",
    "plone.base",
    "plone.i18n",
    "plone.memoize",
    "plone.protect>=2.0.3",
    "plone.registry",
    "plone.session",
    "Products.BTreeFolder2",
    "Products.GenericSetup",
    "Products.PluggableAuthService>=2.0",
    "setuptools",
]

setup(
    name="Products.PlonePAS",
    version=version,
    description="PlonePAS modifies the PluggableAuthService for use by Plone.",
    long_description=long_description,
    long_description_content_type="text/x-rst",
    # Get more strings from
    # https://pypi.org/classifiers/
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
    python_requires=">=3.8",
    install_requires=install_requires,
    extras_require=dict(
        test=[
            "plone.app.testing",
            "plone.app.contenttypes[test]",
            "plone.testing",
            "Products.PluginRegistry",
        ],
    ),
)
