from setuptools import setup, find_packages


def get_long_description():
    with open('README.md', 'r') as f:
        return f.read()


def get_license():
    with open('LICENSE', 'r') as f:
        return f.read()


setup(
    name='bilix',
    python_requires=">=3.8",
    version='0.3.3.6',
    author='HFrost0',
    author_email='hhlfrost@gmail.com',
    description='⚡️快如闪电的b站视频下载工具，基于Python现代Async异步特性，高速批量下载整部动漫，电视剧，电影，up投稿等',
    license=get_license(),
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    entry_points={
        "console_scripts": "bilix=bilix._cli:main"
    },
    install_requires=[
        "httpx[http2]",
        'rich',
        'json5',
        'protobuf',
    ],
)
