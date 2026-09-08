import datetime
import http
import json
import http.client
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin
from datetime import datetime

def main():
    events = get_rausgegangen_events() + get_fomo_events() + get_familienzeit_events()
    write_events_to_json(events)

def write_events_to_json(events):
    with open("events.json", "w", encoding="utf-8") as f:
        json.dump(events, f, ensure_ascii=False, indent=4)

def get_rausgegangen_events():
    date = datetime.today().strftime("%Y-%m-%d")
    base_url = "https://rausgegangen.de"
    events = []
    url = f"{base_url}/eventsearch/?start_date__gte={date}&start_date__lte={date}&city=bremen"
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; EventParser/1.0)",
        "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
    }

    with requests.Session() as session:
        while url:
            try:
                response = session.get(url, headers=headers, timeout=30)
                response.raise_for_status()
            except requests.RequestException:
                break

            html = response.text
            soup = BeautifulSoup(html, 'html.parser')
            for card in soup.select("[data-testid='eventsearch-results'] [data-testid='event-tile-wide']"):
                event_link = card.select_one("a[href]")
                if not event_link:
                    continue

                title_el = card.select_one("span.h6")
                category_el = card.select_one("[data-testid='badge-category']")
                address_el = card.select_one("p.text-neutral.text-sm.truncate")
                events.append({
                    "title": title_el.get_text(strip=True) if title_el else None,
                    "description": "go to url",
                    "startdate": date,
                    "src": "rausgegangen.de",
                    "url": urljoin(base_url, event_link["href"]),
                    "category": category_el.get_text(strip=True) if category_el else None,
                    "address": address_el.get_text(strip=True) if address_el else None,
                })

            next_page = soup.select_one("nav[aria-label='Seitennavigation'] a[aria-label='Next'][href]")
            url = urljoin(response.url, next_page["href"]) if next_page else None
    return events


def get_bremen_de_events():
    res = []
    url = "https://login.bremen.de"
    parsed_url = urlparse(url)
    today = datetime.today()
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
    today = datetime.today().strftime("%Y-%m-%d")
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

def get_fomo_events():
    url = "https://fomobremen.info"

    parsed_url = urlparse(url)
    payloadDict = {
        "operationName": "FetchEvents",
        "variables": {
            "orderBy": "BEGINS_ON",
            "direction": "ASC",
            "limit": 99
        },
        "query": "query FetchEvents($orderBy: EventOrderBy, $direction: SortDirection, $page: Int, $limit: Int) { events(orderBy: $orderBy, direction: $direction, page: $page, limit: $limit) { total elements { id uuid url local title description beginsOn endsOn status visibility insertedAt language picture { url __typename } publishAt physicalAddress { ...AdressFragment __typename } organizerActor { ...ActorFragment __typename } attributedTo { ...ActorFragment __typename } category tags { ...TagFragment __typename } options { ...EventOptions __typename } __typename } __typename } } fragment AdressFragment on Address { id description geom street locality postalCode region country type url originId timezone __typename } fragment TagFragment on Tag { id slug title __typename } fragment EventOptions on EventOptions { maximumAttendeeCapacity remainingAttendeeCapacity showRemainingAttendeeCapacity anonymousParticipation showStartTime showEndTime timezone offers { price priceCurrency url __typename } participationConditions { title content url __typename } attendees program commentModeration showParticipationPrice hideOrganizerWhenGroupEvent isOnline __typename } fragment ActorFragment on Actor { id avatar { url __typename } type preferredUsername name domain summary url __typename }"
    }


    headers = {"Content-Type": "application/json"}

    conn = http.client.HTTPSConnection(parsed_url.hostname)
    conn.request("POST", "/api", json.dumps(payloadDict), headers)
    response = conn.getresponse()

    data = json.loads(response.read().decode("utf-8"))
    today_date = datetime.today().strftime('%Y-%m-%d')
    all_events = data['data']['events']['elements']
    upcoming_events = [e for e in all_events if today_date in e["beginsOn"]]
    res = []
    for elem in upcoming_events:
        res.append(
            {
                    "title": elem["title"],
                    "description": elem["description"],
                    "address": (pa := elem.get("physicalAddress")) and pa.get("description"),
                    "startdate": today_date,
                    "enddate": today_date,
                    "category": "Alternativ",
                    "url": elem["url"],
                    "src": "fomo bremen"
            }
        )
    return res

if __name__ == "__main__":
    main()
