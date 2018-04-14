#!/usr/bin/env python

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

VERSION = '0.0.1'

setup(
    name='test-tornado-chat',
    version=VERSION,
    description='Asynchronous Chat Server for the Tornado Web Framework.',
    author='Eugene Klimov',
    author_email='bloodjazman@gmail.com',
    license="http://www.apache.org/licenses/LICENSE-2.0",
    url='http://github.com/Slach/test-tornado-chat',
    keywords=['Redis', 'Tornado', 'Chat'],
    packages=['test-tornado-chat'],
    long_description=open('README.md', 'rb').read(),
    requires=['tornado', 'tornado-redis'],
)
