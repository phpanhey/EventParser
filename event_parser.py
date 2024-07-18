import datetime
import http
import json
import http.client
from urllib.parse import urlparse
from bs4 import BeautifulSoup


def main():
    events = get_bremen_de_events() + get_familienzeit_events()    
    write_events_to_json(events)


def write_events_to_json(events):
    with open("events.json", "w", encoding="utf-8") as f:
        json.dump(events, f, ensure_ascii=False, indent=4)


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

        if category == "Kinder & Jugend":
            category = "Familien & Jugendaktivitäten"

        res.append(
            {
                "title": title,
                "description": description,
                "address": address,
                "startdate": startdate,
                "enddate": enddate,
                "category": category,
                "url": url,
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
                    "category": "Familien & Jugendaktivitäten",
                    "url": url,
                }
            )
        if data["has_more"] == True:
            offset += 10
        else:
            has_more = False
    return res


if __name__ == "__main__":
    main()
