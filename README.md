# arXiv Page Crawler

Crawls a set of information from an [arXiv.org](arxiv.org) article.

* [x] Basic Information
* [x] Abstract Translation
* [x] Articles Download

## Installation

```cmd
pip3 install beautifulsoup4
pip3 install request
pip3 install pyyaml
```

Put your baidu translation API key in `key.yaml`:

```yml
APP_ID: "my app id"
KEY: "my key"
```

## Usage

```cmd
python crawler.py --link [link]
python crawler.py --file [file of links]
python crawler.py --file [file of links] --download
```
