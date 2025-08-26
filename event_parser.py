import datetime
import http
import json
import http.client
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin

def main():
   
    events = get_rausgegangen_events() + get_familienzeit_events() + get_mix_online_events()        
    write_events_to_json(events)
    


def write_events_to_json(events):
    with open("events.json", "w", encoding="utf-8") as f:
        json.dump(events, f, ensure_ascii=False, indent=4)

def get_rausgegangen_events():
    date = datetime.date.today().strftime("%Y-%m-%d")
    base_url = "https://rausgegangen.de"
    url_prefix = base_url + '/eventsearch/?page='    
    url_postfix = f"&start_date__gte={date}&start_date__lte={date}&city=bremen"
    cntr = 1
    url = url_prefix + str(cntr) + url_postfix
    r = requests.get(url) 
    events = []
    while r.status_code!=404:
        html = r.text
        soup = BeautifulSoup(html, 'html.parser')
        for card in soup.select("div.h-20"):    
            title = card.select_one("h4")
            url = card.select_one("a[href]")
            category = card.select_one(".event-text-pill-outline")
            address_parts = card.select("div.text-sm.opacity-70")
            events.append({
                "title": title.get_text(strip=True) if title else None,
                "description": "go to url",
                "data": date,
                "src": "rausgegangen.de",
                "url": urljoin(base_url, url["href"]) if url else None,
                "category": category.get_text(strip=True) if category else None,
                "address": " ".join(p.get_text(strip=True).lstrip("|").strip() for p in address_parts)
            })
        cntr += 1
        url = url_prefix + str(cntr) + url_postfix
        r = requests.get(url)
    return events


def get_bremen_de_events():
    res = []
    url = "https://login.bremen.de"
    parsed_url = urlparse(url)
    today = datetime.date.today()
    tommorow = today + datetime.timedelta(days=1)

    payloadDict = {
        "is_date_search": 1,
        "dates": {"0": today.strftime("%Y-%m-%d"), "1": tommorow.strftime("%Y-%m-%d")},
    }

    headers = {"Content-Type": "application/json"}

    conn = http.client.HTTPSConnection(parsed_url.hostname)
    conn.request("POST", "/api/event-search/search", json.dumps(payloadDict), headers)
    response = conn.getresponse()

    data = json.loads(response.read().decode("utf-8"))

    for event in data:        
        title = event["title"]
        description = event["description"]
        address = event["address"]["venue"]["address"]   
        startdate = datetime.datetime.fromtimestamp(
            int(event["nextDate"]) / 1000
        ).strftime("%Y-%m-%d %H:%M:%S")
        enddate = startdate
        category = event["categories"][0]["title"]
        url = event["redirectUrl"]

        if category == "Kinder & Jugendliche":
            category = "Familie & Jugend"

        res.append(
            {
                "title": title,
                "description": description,
                "address": address,
                "startdate": startdate,
                "enddate": enddate,
                "category": category,
                "url": url,
                "src": "bremen.de",
            }
        )
    return res


def get_familienzeit_events():

    has_more = True
    today = datetime.date.today().strftime("%Y-%m-%d")
    offset = 0
    res = []

    while has_more:
        conn = http.client.HTTPSConnection(
            urlparse("https://kinderzeit-bremen.de").hostname
        )
        url_path = f"/api/sprocket/calendar/1192/get_calendar_events?limit=10&offset={offset}&dtstart={today}"
        conn.request("GET", url_path)
        response = conn.getresponse()

        data = json.loads(response.read().decode("utf-8"))

        for elem in data["results"]:
            soup = BeautifulSoup(elem, "html.parser")
            title = soup.find("h3").get_text()
            description = (
                soup.find("p", class_="mp-description").find("span").get_text()
            )
            address = soup.find("p", class_="mp-infos mp-location").find("a").get_text()
            url = soup.find("h3").find("a")["href"]

            res.append(
                {
                    "title": title,
                    "description": description,
                    "address": address,
                    "startdate": today,
                    "enddate": today,
                    "category": "Familie & Jugend",
                    "url": url,
                    "src": "familienzeit bremen"
                }
            )
        if data["has_more"] == True:
            offset += 10
        else:
            has_more = False
    return res

def get_mix_online_events():
    res = []
    conn = http.client.HTTPSConnection("www.mix-online.de")
    endpoint = "/v1/data/termine/get_events.php"

    # Make the POST request
    conn.request("POST", endpoint)

    # Get the response
    response = conn.getresponse()
    data = json.loads(response.read().decode("utf-8"))
    for elem in data["rows"]:
        if elem["datum_humanized"] == "HEUTE":
            
            if elem["rubrik"] == "Hits für Kids":
                elem["rubrik"] = "Familie & Jugend"
                
            if elem["rubrik"] == "Kino":
                elem["rubrik"] = "Film"
                
            if elem["rubrik"] == "Bühne":
                elem["rubrik"] = "Theater & Bühne"
                
            res.append(
                {
                    "title": elem["titel"],
                    "description": elem["titel"],
                    "address": elem["verort"],
                    "startdate": elem["datum"],
                    "enddate": elem["datum"],
                    "category": elem["rubrik"],
                    "url": None,
                    "src": "mix-online"
                }
            )     
    return res

if __name__ == "__main__":
    main()
