import datetime
import http
import json
import http.client
from urllib.parse import urlparse


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
        
        res.append(
            {
                "title": title,
                "description": description,
                "address": address,
                "startdate": startdate,
                "enddate": enddate,
                "category": category,
            }
        )
    return res


def get_familienzeit_events():
    return []


if __name__ == "__main__":
    main()
