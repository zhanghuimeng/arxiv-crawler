import argparse
import requests
from bs4 import BeautifulSoup
from urllib.request import urlopen

template = u"""
# %s

链接：[%s](%s)

作者：%s

单位：

出版：%s

主题：%s

要点：

英文摘要：%s

摘要：%s
"""

parser = argparse.ArgumentParser()
parser.add_argument("--link", type=str, help="A link")
parser.add_argument("--file", type=str, help="A file of links", default="links.dat")
parser.add_argument("--download", action="store_true")
parser.add_argument("--output", type=str, help="Output of crawlers", default="output.md")
args = parser.parse_args()

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
        html = urlopen(link).read().decode("utf-8")
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

        ch_abstract = ""
        
        f.write(template % (title, link, link, authors, comments, subjects, abstract, ch_abstract))
        print()
