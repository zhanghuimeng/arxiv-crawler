import argparse
import requests
from bs4 import BeautifulSoup
from urllib.request import urlopen
from urllib.parse import quote
import yaml
import hashlib
import random
import json
import re
import dateparser
import datetime
import urllib
import time


def trans_to_zh(key, text):
    time.sleep(1)  # 个人免费版限制QPS=1
    url_template = "http://fanyi-api.baidu.com/api/trans/vip/translate?q={}&from=en&to=zh&appid={}&salt={}&sign={}"
    q = text
    appid = key["APP_ID"]
    salt = ''.join(str(random.choice(range(10))) for _ in range(10))
    key = key["KEY"]

    str1 = appid + q + salt + key
    sign = hashlib.new("md5", str1.encode("utf-8")).hexdigest()

    q = quote(q)  # URL encode
    url = url_template.format(q, appid, salt, sign)
    res_data = urlopen(url)
    res = res_data.read()
    text_zh = json.loads(res)["trans_result"][0]["dst"]
    return text_zh


class Entry:
    str_template = "标题：{0}\n\n标题（机翻）：{1}\n\n链接：[{2}]({2})\n\n作者：{3}\n\n注释：{4}\n\n主题：{5}\n\n摘要：{6}\n\n摘要（机翻）：{7}\n\n"

    def __init__(self, link, title, authors, comments, subjects,
                 abstract, key=None):
        self.link = link
        self.title = title
        self.authors = authors
        self.comments = comments
        self.subjects = subjects
        self.abstract = abstract
        if key:
            self.translate(key)

    def translate(self, key):
        self.title_zh = trans_to_zh(key, self.title)
        self.abstract_zh = trans_to_zh(key, self.abstract)

    def __str__(self):
        return Entry.str_template.format(
            self.title, self.title_zh, self.link, self.authors, self.comments,
            self.subjects, self.abstract, self.abstract_zh)


parser = argparse.ArgumentParser()
parser.add_argument("--download", action="store_true")
parser.add_argument("--output", type=str, help="Output of crawlers", default="output.md")
args = parser.parse_args()

# load baidu API info
with open("key.yaml") as f:
    key = yaml.load(f, Loader=yaml.FullLoader)
    print(key)

# load https://arxiv.org/list/cs.CL/pastweek page, 
# get date range and number of entries
html = urlopen("https://arxiv.org/list/cs.CL/pastweek", timeout=5).read().decode("utf-8", "ignore")
soup = BeautifulSoup(html, features="lxml")
end_date_str = soup.find("div", {"id": "dlpage"}).find("ul").find("li").get_text()
end_date = dateparser.parse(end_date_str).date()
start_date = end_date - datetime.timedelta(days=5)
print("Week {} ~ {}".format(start_date.strftime("%Y/%m/%d"), end_date.strftime("%Y/%m/%d")))
entry_sum_str = soup.find("small").get_text()
search_obj = re.search(r"total of (\d*) entries", entry_sum_str)
if search_obj is None:
    print("Failed to find number of entries")
    exit(1)
entry_sum = int(search_obj.group(1))
print("Number of entries in this week: %d" % entry_sum)

# load https://arxiv.org/list/cs.CL/pastweek?show={entry_sum} page and get list of links
html = urlopen("https://arxiv.org/list/cs.CL/pastweek?show={}".format(entry_sum), timeout=5).read().decode("utf-8", "ignore")
soup = BeautifulSoup(html, features="lxml")
all_entries = []
for single_day_ele in soup.find("div", {"id": "dlpage"}).findAll("dl", recursive=False):
    daily_entries = []
    for ele in single_day_ele.findAll("dt", recursive=False):
        rel_link = ele.find("span", {"class": "list-identifier"}).find("a")["href"]
        abs_link = urllib.parse.urljoin("https://arxiv.org", rel_link)
        daily_entries.append(abs_link)
    daily_entries.reverse()
    print("Daily entries: {}".format(len(daily_entries)))
    all_entries.append(daily_entries)
all_entries.reverse()

with open(args.output, "w", encoding="utf-8") as f:
    for i in range(len(all_entries)):
        date = start_date + datetime.timedelta(days=i)
        # write date as h1
        f.write("# {}\n\n".format(date.strftime("%Y/%m/%d")))
        for j in range(len(all_entries[i])):
            link = all_entries[i][j]
            html = urlopen(link, timeout=5).read().decode("utf-8", "ignore")
            soup = BeautifulSoup(html, features="lxml")
            # get title
            title = soup.find("h1", {"class": "title mathjax"}).get_text()
            title = title.replace("Title:", "").strip()
            print("Title: %s" % title)

            if args.download:
                pdf_link = soup.find("div", {"class": "full-text"}).find_all("ul")[0].find_all("li")[0].find_all("a")[0]["href"]
                pdf_link = urllib.parse.urljoin("https://arxiv.org", pdf_link)
                print("Link: %s" % pdf_link)
                print("Downloading PDF...")
                # stream loading
                r = requests.get(pdf_link, stream=True, timeout=5)
                with open("./data/%s.pdf" % title, "wb") as f2:
                    for chunk in r.iter_content(chunk_size=32):
                        f2.write(chunk)
                continue

            # get authors
            authors = soup.find("div", {"class": "authors"}).get_text()
            authors = authors.replace("Authors:", "").strip()
            # print("Authors: %s" % authors)
            # get comments
            comments = soup.find("td", {"class": "tablecell comments mathjax"})
            if not comments:
                comments = ""
            else:
                comments = comments.get_text()
            # print("Comments: %s" % comments)
            # get subjects
            subjects = soup.find("td", {"class": "tablecell subjects"}).get_text()
            subjects = subjects.strip()
            # print("Subjects: %s" % subjects)
            # get abstract
            abstract = soup.find("blockquote", {"class": "abstract mathjax"}).get_text()
            abstract = abstract.replace("Abstract:", "").strip()
            abstract = abstract.replace("\n", " ")
            # build Entry object
            entry = Entry(link=link, title=title, authors=authors, comments=comments, subjects=subjects, abstract=abstract, key=key)
            # write title as h2
            f.write("## {}\n\n".format(title))
            # write content
            f.write(str(entry))
            f.flush()
