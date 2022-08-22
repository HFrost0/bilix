# -*- coding: utf-8 -*-
from pathlib import Path

from setuptools import setup, find_packages


def get_long_description():
    with open('README.md', 'r', encoding='utf8') as f:
        return f.read()


def get_version() -> str:
    with open('bilix/__version__.py', 'r', encoding='utf8') as f:
        for line in f.readlines():
            if line.startswith("__version__"):
                delim = '"' if '"' in line else "'"
                return line.split(delim)[1]
    raise RuntimeError("Unable to find version string.")


def get_packages(package):
    """
    Return root package and all sub-packages.
    """
    return [str(path.parent) for path in Path(package).glob("**/__init__.py")]


setup(
    name='bilix',
    python_requires=">=3.8",
    version=get_version(),
    author='HFrost0',
    author_email='hhlfrost@gmail.com',
    description='⚡️快如闪电的b站视频下载工具，基于Python现代Async异步特性，高速批量下载整部动漫，电视剧，电影，up投稿等',
    license='Apache-2.0 license',
    url='https://github.com/HFrost0/bilix',
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    packages=get_packages('bilix'),
    include_package_data=True,
    entry_points={
        "console_scripts": "bilix=bilix.__main__:main",
    },
    install_requires=[
        "httpx[http2]>=0.22.0",
        'anyio',
        'aiofiles>=0.8.0',
        'rich',
        'json5',
        'click>=8.0.3',
        'm3u8',
        'bs4',
        'pyexecjs',
        'pycryptodome',
        'protobuf>=4.21.1',
        'biliass==1.3.5'
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3 :: Only",
    ],
)
