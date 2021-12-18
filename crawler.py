import argparse
import requests
from bs4 import BeautifulSoup
from urllib.request import urlopen
from urllib.parse import quote
import yaml
import hashlib
import random
import json

template = u"""
# %s

链接：[%s](%s)

作者：%s

单位：

出版：%s

主题：%s

英文摘要：%s

摘要：%s
"""

def get_ch_abstract(key, abstract):
    url_template = "http://api.fanyi.baidu.com/api/trans/vip/translate?q=%s&from=en&to=zh&appid=%s&salt=%s&sign=%s"
    q = abstract
    appid = key["APP_ID"]
    salt = ''.join(str(random.choice(range(10))) for _ in range(10))
    key = key["KEY"]

    str1 = appid + q + salt + key
    sign = hashlib.new("md5", str1.encode("utf-8")).hexdigest()
    # print(sign)

    q = quote(q)
    url = url_template % (q, appid, salt, sign)
    # print(url)
    res_data = urlopen(url)
    res = res_data.read()
    ch_abstract = json.loads(res)["trans_result"][0]["dst"]
    # print(ch_abstract)
    return ch_abstract

parser = argparse.ArgumentParser()
parser.add_argument("--link", type=str, help="A link")
parser.add_argument("--file", type=str, help="A file of links", default="links.dat")
parser.add_argument("--download", action="store_true")
parser.add_argument("--output", type=str, help="Output of crawlers", default="output.md")
args = parser.parse_args()

with open("key.yaml") as f:
    key = yaml.load(f, Loader=yaml.FullLoader)
    print(key)

links = []
if args.link:
    links.append(args.link)
if args.file:
    with open(args.file) as f:
        for line in f:
            if line.strip() != "":
                links.append(line.strip())

with open(args.output, "w", encoding="utf-8") as f:
    for link in links:
        html = urlopen(link, timeout=5).read().decode("utf-8", "ignore")
        soup = BeautifulSoup(html, features="lxml")

        title = soup.find("h1", {"class": "title mathjax"}).get_text()
        title = title.replace("Title:", "").strip()
        print("Title: %s" % title)

        if args.download:
            pdf_link = soup.find("div", {"class": "full-text"}).find_all("ul")[0].find_all("li")[0].find_all("a")[0]["href"]
            pdf_link = "https://arxiv.org" + pdf_link
            print("Link: %s" % pdf_link)
            print("Downloading PDF...")
            r = requests.get(pdf_link, stream=True)    # stream loading
            with open("./data/%s.pdf" % title, "wb") as f2:
                for chunk in r.iter_content(chunk_size=32):
                    f2.write(chunk)
            continue

        authors = soup.find("div", {"class": "authors"}).get_text()
        authors = authors.replace("Authors:", "").strip()
        print("Authors: %s" % authors)

        comments = soup.find("td", {"class": "tablecell comments mathjax"})
        if not comments:
            comments = ""
        else:
            comments = comments.get_text()  
        print("Comments: %s" % comments)

        subjects = soup.find("td", {"class": "tablecell subjects"}).get_text()
        subjects = subjects.strip()
        print("Subjects: %s" % subjects)

        abstract = soup.find("blockquote", {"class": "abstract mathjax"}).get_text()
        abstract = abstract.replace("Abstract:", "").strip()
        abstract = abstract.replace("\n", " ")
        # print("Abstract: %s" % abstract)

        ch_abstract = get_ch_abstract(key, abstract)
        
        f.write(template % (title, link, link, authors, comments, subjects, abstract, ch_abstract))
        print()
