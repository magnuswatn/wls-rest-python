import os
import re
import codecs

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

def read_file(filename, encoding='utf8'):
    """Read unicode from given file."""
    with codecs.open(filename, encoding=encoding) as fd:
        return fd.read()

here = os.path.abspath(os.path.dirname(__file__))

module = read_file(os.path.join(here, 'wls_rest_python.py'))
meta = dict(re.findall(r"""__([a-z]+)__ = '([^']+)""", module))

readme = read_file(os.path.join(here, 'README.rst'))
version = meta['version']

setup(
    name='wls-rest-python',
    description='A Python client for the Weblogic REST API',
    long_description=readme,
    version=version,
    license='MIT',
    author='Magnus Watn',
    keywords='weblogic wls rest administration automation',
    url='https://github.com/magnuswatn/wls-rest-python',
    py_modules=['wls_rest_python'],
    install_requires=[
        'requests',
        ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Topic :: System :: Systems Administration',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        ],
)
