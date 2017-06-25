from distutils.core import setup

setup(
    name="HomeLibraryCatalog",
    version="0.1.0",
    description="Web application for cataloging home books collection",
    author="Vitaly Potyarkin",
    author_email="sio.wtf@gmail.com",
    url="https://github.com/sio/HomeLibraryCatalog",
    packages=["hlc", "hlc.test"],
    package_data={"hlc": ["ui/static/*", "ui/templates/*"]},
    include_package_data=True,
    scripts=["HomeLibraryCatalog.py"],
    license="GPL-3.0",
    install_requires=[
        "lxml>=3.7.3", 
        "cssselect>=1.0.1", 
        "bottle>=0.12.13", 
        "Pillow>=4.0.0"]
    )
