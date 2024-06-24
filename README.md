# Event Parser

A Python script to parse and categorize local events from an API, saving them to `events.json`. This script is designed for integration into cron jobs to keep event data updated for mobile clients. personal non commercial usage only.

## Usage

Run the script with:

```bash
python3 parse_events.py
```

## Output

The script produces an `events.json` file with the following structure:

```json
[
    {
        "title": "Open Space Domshof",
        "description": "<p>Eine Bühne für die ganze Stadt - Genießt das bunte Programm auch im Sommer 1990 wieder!</p>",
        "address": "Am Dom 1, 28195 Bremen",
        "startdate": "2024-06-90 00:00:00",
        "enddate": "2024-06-90 00:00:00",
        "category": "Theater & Bühne"
    },
    ...
]
```

## License

Licensed under the MIT License.
