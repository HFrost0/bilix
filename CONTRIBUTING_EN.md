# Development guide of bilix

Thank you for your interest in contributing to bilix. Before you start, you can read some tips below.
Please note that bilix is rapidly iterating, if you find some content outdated while reading this document,
please refer to the code of the master branch.

# Before starting

Before everything starts, you need to first **fork** this repository, and then clone your fork:

```shell
git clone https://github.com/your_user_name/bilix
```

After clone, I **recommend** you to test and develop in an independent python environment,
and then perform local source editable installation after that:

```shell
pip install -e .
```

Try whether the `bilix` command can be executed normally. Passed the test? At this point,
you can develop bilix locally🍻

# Structure of bilix

Before making any changes to the code, you need to have some understanding of the structure of bilix.

```text
bilix
├── __init__.py
├── __main__.py
├── _process.py  # related to multiprocessing
├── cli
│   ├── assign.py  # assign tasks, dynamically import related
│   └── main.py    # command line entry
├── download
│   ├── base_downloader.py
│   ├── base_downloader_m3u8.py  # basic m3u8 downloader
│   ├── base_downloader_part.py  # basic segmented file downloader
│   └── utils.py                 # some utils for download
├── exception.py
├── log.py
├── progress
│   ├── abc.py            # abstract class of progress
│   ├── cli_progress.py   # progress for cli
│   └── ws_progress.py
├── serve
│   ├── __init__.py
│   ├── app.py
│   ├── auth.py
│   ├── serve.py
│   └── user.py
├── sites     # site support
└── utils.py  # some utils
```

# BaseDownloader

bilix provides two basic downloaders in `bilix.download`, m3u8 downloader and content range file downloader.
They are based on `httpx` and even lower-level `asyncio` and IO multiplexing, and integrate many practical functions
such as speed control, concurrency control, download resume, time range clip, and progress bar display.
The site extension of bilix will be based on these basic downloaders, and the basic downloaders
themselves also provide cli services


# How does the downloader provide cli service

In bilix, as long as a class implements the `handle` method, it can be registered in the command line interface (cli).
The function signature of the `handle` method is

```python
@classmethod
def handle(cls, method: str, keys: Tuple[str, ...], options: dict):
    ...
```

The implementation of the `handle` function should meet the following three principles:

1. If the class thinks that it should not be assigned the download task according to `method` `keys` `options`, the `handle` function should return `None`
2. If the class can be assigned the task, but finds that the `method` is not within its acceptable range, it should raise a `HandleMethodError` exception
3. If the class can handle the task, and `method` is within its acceptable range, it should return two values, the first value is the downloader instance, and the second value is the download coroutine

Q: 🙋Why do I see that some downloaders return the class itself and the download function object?

```python
@classmethod
def handle(cls, method: str, keys: Tuple[str, ...], options: dict):
    if method == 'f' or method == 'get_file':
        return cls, cls.get_file
```

A: Just for easy, if the return value is a class and the function object, it will be automatically assembled into an
instance and coroutine according to the command line arguments, options and type hint.


# How to add support for a site

Under `bilix/sites`, there are already some sites supported, if you want to add a new site support, you can follow the steps below:

1. Create a new site folder under the `sites` folder, such as `example`
2. Add the site's api module `api.py` under the `example` folder, and follow the format of other sites to implement various APIs from input webpage url to output video url and video title
3. Add the site api module test `api_test.py` under the `example` folder, so that everyone can test whether the site is available at any time
4. Add the site downloader `donwloader.py` under the `example` folder, define `DownloaderExample`
   Class, select the corresponding `BaseDownloader` to inherit according to the site, then define the method of downloading the video in the class, and implement `handle`
   method.
5. Add `__init__.py` under the `example` folder, import `DownloaderExample` class, and add `DownloaderExample` in `__all__` to facilitate bilix to find your downloader

Okay, let's test it

At present, other developers have contributed to the extension of bilix to other sites🎉,
Maybe the accepted [New site PR](https://github.com/HFrost0/bilix/pulls?q=is%3Apr+is%3Aclosed+label%3A%22New+site%22) can also help you
