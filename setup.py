"""A tiny python command line browser for sterkinekor."""

from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))


try:
    from pypandoc import convert

    read_md = lambda f: convert(f, 'rst')
except ImportError:
    print("warning: pypandoc module not found, could not convert Markdown to RST")
    read_md = lambda f: open(f, 'r').read()

setup(
    name='ster-py',
    version='1.0.0',
    description='A python cli based sterkinekor browser, whatever, it needed to be done.',
    long_description=read_md('README.md'),
    url='https://github.com/spookyUnknownUser/ster-py',
    author='spookyUnknownUser',
    author_email='spookyUnknownUser@users.noreply.github.com@',
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Utilities',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.7',
    ],
    keywords='cli command python sterkinekor browser',
    packages=find_packages(),
    install_requires=['click', 'appdirs', 'clint', 'omdbpy'],
    entry_points={
        'console_scripts': [
            'ster-py=sterpy:main',
        ],
    },
)
