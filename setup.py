# -*- coding: utf-8 -*-
from setuptools import setup, find_packages


def get_long_description():
    with open('README.md', 'r', encoding='utf8') as f:
        return f.read()


setup(
    name='bilix',
    python_requires=">=3.8",
    version='0.6.8',
    author='HFrost0',
    author_email='hhlfrost@gmail.com',
    description='⚡️快如闪电的b站视频下载工具，基于Python现代Async异步特性，高速批量下载整部动漫，电视剧，电影，up投稿等',
    license='Apache-2.0 license',
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    entry_points={
        "console_scripts": "bilix=bilix._cli:main",
    },
    install_requires=[
        "httpx[http2]",
        'anyio',
        'rich',
        'json5',
        'protobuf',
        'click',
        'biliass==1.3.4'
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3 :: Only",
    ],
)
