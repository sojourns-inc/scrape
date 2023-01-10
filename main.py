# Python3
from bs4 import BeautifulSoup, Comment
import json
import xmltodict
from urllib.request import Request, urlopen, HTTPError
import requests
from datetime import datetime
import logging


# https://stackoverflow.com/a/67629747
def isolate_text_body(b: BeautifulSoup):
    start_comment = " Start Body "
    end_comment = " End Body "
    to_extract = []
    between_comments = False

    for x in b.recursiveChildGenerator():
        if between_comments and isinstance(x, str):
            if x.strip().__len__() > 0 and "Dosage Chart:" not in x.strip():
                to_extract.append(x.strip())
        if isinstance(x, Comment):
            if start_comment == x:
                between_comments = True
            elif end_comment == x:
                break

    return to_extract


def get_doses(b: BeautifulSoup):
    doses = []
    dosechart_raw_list = b.find_all(attrs={"class": "dosechart"})
    dosechart_table = dosechart_raw_list[0] if len(dosechart_raw_list) > 0 else None
    if dosechart_table is None:
        return doses
    for row in dosechart_table.find_all("tr"):
        dose = {}
        for val in row.find_all("td"):
            if (
                "class" in val.attrs
                and len(val.attrs["class"]) > 0
                and val.attrs["class"][0] == "dosechart-amount"
            ):
                if "repeated" in val.string:
                    dose = {"amount": "rep", "units": "rep"}
                else:
                    if val.string.strip() == "":
                        dose = {"amount": "?", "units": "?"}
                    else:
                        dose_tokenize = val.string.split(" ")
                        dose["amount"] = dose_tokenize[0]
                        dose["units"] = dose_tokenize[1]

            if (
                "class" in val.attrs
                and len(val.attrs["class"]) > 0
                and val.attrs["class"][0] == "dosechart-method"
                and len(val.string) > 1
            ):
                dose["method"] = val.string

            if (
                "class" in val.attrs
                and len(val.attrs["class"]) > 0
                and val.attrs["class"][0] == "dosechart-substance"
                and len(val.string) > 1
            ):
                dose["substance"] = val.string

            if (
                "class" in val.attrs
                and len(val.attrs["class"]) > 0
                and val.attrs["class"][0] == "dosechart-form"
                and len(val.string) > 1
            ):
                dose["form"] = val.string

        doses.append(dose)

    return doses


def get_foot(b: BeautifulSoup):
    extra = {}
    foot_raw_list = b.find_all(attrs={"class": "footdata"})
    foot_table = foot_raw_list[0] if len(foot_raw_list) > 0 else None
    if foot_table is None:
        return extra
    for row in b.find_all(attrs={"class": "footdata"})[0].find_all("tr"):
        for val in row.find_all("td"):
            if val.string is None:
                continue

            if "Published:" in val.string:
                extra["date"] = val.string.split(":")[1].strip()

            if "Gender:" in val.string:
                extra["sex"] = val.string.split(":")[1].strip()

            if "Age at time of experience:" in val.string:
                extra["age_during_exp"] = val.string.split(":")[1].strip()

            if "ExpID:" in val.string:
                extra["exp_id"] = val.string.split(":")[1].strip()
    return extra


def fetch_report(id: str = ""):
    full_url = f"https://upload.erowid.org/experiences/exp.php?ID={id}"
    exp_page = urlopen(full_url)
    soup = BeautifulSoup(exp_page.read(), "lxml")

    try:
        maybe_title = soup.find_all(attrs={"class": "title"})
        maybe_author = soup.find_all(attrs={"class": "author"})
        maybe_drug = soup.find_all(attrs={"class": "substance"})
        maybe_weight = soup.find_all(attrs={"class": "bodyweight-amount"})

        title = maybe_title[0].string
        author, drug, weight, weight_data = None, None, None, None
        if len(maybe_author) > 0:
            author = maybe_author[0]
        if len(maybe_drug) > 0:
            drug = maybe_drug[0].string
        if len(maybe_weight) > 0:
            weight = maybe_weight[0].string
        if weight and weight != "":
            weight_pair = weight.split(" ")
            weight_amount = weight_pair[0] if len(weight_pair) > 1 else None
            weight_units = weight_pair[1] if len(weight_pair) > 1 else None
            weight_data = {
                "amount": weight_amount,
                "units": weight_units,
            }
        author_a = author.find_all("a")
        author_name = author_a[0].string if len(author_a) > 0 else None
        trip = {
            "title": title,
            "author": author_name,
            "drug": drug,
            "weight": weight_data,
            "dosechart": get_doses(soup),
        }

        trip["text"] = isolate_text_body(soup)
        trip["extra"] = get_foot(soup)

        return trip
    except IndexError as e:
        logging.exception(e)
        return {"faulty": full_url}


def fetch_shroomery_report(id: str = ""):
    url = (
        f"https://www.shroomery.org/forums/includes/tooltip/postcontents.php?q=&n={id}"
    )

    payload = {}
    headers = {
        "Cookie": "PHPMINDMEDIA=mncb3d2e1fcj0ce6gpm19fffbg",
        "User-Agent": "PostmanRuntime/7.30.0",
        "From": "hi@sernyl.io",
    }
    try:
        response = requests.request("GET", url, headers=headers, data=payload)
        o = xmltodict.parse(response.text)
        return o
    except HTTPError as e:
        return {"error": dict(e)}


def fetch_shroomery_reports(page: str = ""):
    url = f"https://www.shroomery.org/forums/dosearch.php?forum%5B%5D=f1&words=%28trip+%7C+experience%29+report+-tips&namebox=&replybox=&how=boolean&where=subject&tosearch=main&newerval=&newertype=y&olderval=&oldertype=y&minwords=100&maxwords=&limit=25&sort=r&way=d&page={page}"
    links = []
    payload = {}
    headers = {
        "Cookie": "PHPMINDMEDIA=mncb3d2e1fcj0ce6gpm19fffbg",
        "User-Agent": "PostmanRuntime/7.30.0",
        "From": "hi@sernyl.io",
    }
    links = []
    reports = []
    response = requests.request("GET", url, headers=headers, data=payload)
    soup = BeautifulSoup(response.text, "lxml")
    for a in soup.find_all("a", href=True):
        print("Found the URL:", a["href"])
        links.append(a["href"])

    for link in links:
        if "showflat.php/Number" in link:
            print(link)
            id = str(link.split("/")[-1:][0])

            report = fetch_shroomery_report(id=id)

            reports.append(report)

    return {"count": len(links), "urls": links, "data": reports}


def fetch_reports():
    url = "https://upload.erowid.org/experiences/exp.cgi?Cellar=1&ShowViews=0&Cellar=1&Start=0&Max=50000"
    # url = "file:///Users/emmachine/dev/scrape/exp.cgi"
    page = urlopen(url)
    soup = BeautifulSoup(page.read(), "lxml")
    trips = []
    count = 2000

    for a in soup.find_all("a", href=True):
        print("Found the URL:", a["href"])

        full_url = f"https://upload.erowid.org/experiences/{a['href']}"

        if "exp.php" not in a["href"]:
            continue

        p = urlopen(full_url)
        s = BeautifulSoup(p.read(), "lxml")
        try:
            maybe_title = soup.find_all(attrs={"class": "title"})
            maybe_author = soup.find_all(attrs={"class": "author"})
            maybe_drug = soup.find_all(attrs={"class": "substance"})
            maybe_weight = soup.find_all(attrs={"class": "bodyweight-amount"})

            title = maybe_title[0].string
            author, drug, weight, weight_data = None, None, None, None
            if len(maybe_author) > 0:
                author = maybe_author[0]
            if len(maybe_drug) > 0:
                drug = maybe_drug[0].string
            if len(maybe_weight) > 0:
                weight = maybe_weight[0].string
            if weight:
                weight_data = {
                    "amount": weight.split(" ")[0],
                    "units": weight.split(" ")[1],
                }

            trip = {
                "title": title,
                "author": author.find_all("a")[0].string,
                "drug": drug,
                "weight": weight_data,
                "dosechart": get_doses(soup),
            }

            trip["text"] = isolate_text_body(soup)
            trip["extra"] = get_foot(soup)
        except IndexError as e:
            print(f"faulty: {full_url}")
            continue

        print(json.dumps(trip))
        trips.append(trip)

        print(f"{(len(trips) / count) * 100}% -- das how many percent nigga")

        if len(trips) == count:
            break

    f = open("sample.json", "w+")
    f.write(json.dumps(trips))
    f.close()

    return {"cool": 1}


def wordle_latest():
    now = datetime.now()
    date_time_str = now.strftime("%Y-%m-%d")
    url = f"https://www.nytimes.com/svc/wordle/v2/{date_time_str}.json"

    headers = {
        "Cookie": "nyt-gdpr=0",
        "User-Agent": "PostmanRuntime/7.30.0",
        "Accept": "*/*",
        "Cache-Control": "no-cache",
        "Host": "www.nytimes.com",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
    }

    response = requests.request("GET", url, headers=headers)
    return response.json()
