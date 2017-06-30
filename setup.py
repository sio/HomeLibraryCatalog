try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
    name="HomeLibraryCatalog",
    version="0.1.1-git",
    description="Web application for cataloging home books collection",
    url="https://github.com/sio/HomeLibraryCatalog",
    author="Vitaly Potyarkin",
    author_email="sio.wtf@gmail.com",
    license="GPL-3.0",
    platforms="any",
    packages=["hlc", "hlc.test"],
    scripts=["HomeLibraryCatalog.py"],
    package_data={"hlc": ["ui/static/*", "ui/templates/*"]},
    include_package_data=True,
    install_requires=[
        "lxml>=3.7.3", 
        "cssselect>=1.0.1", 
        "bottle>=0.12.13", 
        "Pillow>=4.0.0"],
    python_requires=">=3.3",
    zip_safe=False,
    )
