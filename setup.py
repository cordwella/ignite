import os
from setuptools import setup


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

with open('requirements.txt') as f:
    required = f.read().splitlines()

setup(
    name="ignite",
    version="0.1.0",
    author="Amelia Cordwell",
    description=("A QR code based scavenger hunt game"),
    license="MIT",
    packages=['ignite'],
    long_description=read('README.md'),
    entry_points={
        'console_scripts': [
            'ignite-run = ignite:main',
            'ignite-db-setup = ignite:init_db'
        ]
    },
    install_requires=required,
)
