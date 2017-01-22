import os
from setuptools import setup


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name="ignite",
    version="0.1",
    author="Amelia Cordwell",
    description=("A QR code based scavenger hunt game"),
    license="MIT",
    packages=['ignite'],
    long_description=read('README.md')
)
