from distutils.core import setup

setup(
    name="HomeLibraryCatalog",
    version="0.1.0",
    description="Web application for cataloging home books collection",
    author="Vitaly Potyarkin",
    author_email="sio.wtf@gmail.com",
    url="https://github.com/sio/HomeLibraryCatalog",
    packages=["hlc", "hlc.test"],
    license="GPL-3.0",
    install_requires=["lxml", "cssselect", "bottle", "Pillow"]
    )
