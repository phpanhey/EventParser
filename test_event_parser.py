import unittest
from unittest.mock import Mock, patch

import event_parser


class RausgegangenEventsTests(unittest.TestCase):
    @patch("event_parser.datetime")
    @patch("event_parser.requests.Session")
    def test_parses_current_cards_and_follows_next_page(self, session_class, datetime_class):
        datetime_class.today.return_value.strftime.return_value = "2026-09-08"
        first_page = """
            <div data-testid="eventsearch-results">
              <div data-testid="event-tile-wide">
                <a href="/en/events/example/"><span class="h6 lg:h5">Example event</span></a>
                <p class="text-neutral text-sm truncate">Example venue | Bremen</p>
                <span data-testid="badge-category">Konzerte & Musik</span>
              </div>
            </div>
            <nav aria-label="Seitennavigation"><a aria-label="Next" href="?page=2">Next</a></nav>
        """
        second_page = '<div data-testid="eventsearch-results"></div>'
        responses = [
            Mock(text=first_page, url="https://rausgegangen.de/eventsearch/?page=1"),
            Mock(text=second_page, url="https://rausgegangen.de/eventsearch/?page=2"),
        ]
        for response in responses:
            response.raise_for_status = Mock()

        session = session_class.return_value.__enter__.return_value
        session.get.side_effect = responses

        self.assertEqual(
            event_parser.get_rausgegangen_events(),
            [{
                "title": "Example event",
                "description": "go to url",
                "startdate": "2026-09-08",
                "src": "rausgegangen.de",
                "url": "https://rausgegangen.de/en/events/example/",
                "category": "Konzerte & Musik",
                "address": "Example venue | Bremen",
            }],
        )
        self.assertEqual(session.get.call_count, 2)

    @patch("event_parser.requests.Session")
    def test_returns_events_collected_before_request_failure(self, session_class):
        session = session_class.return_value.__enter__.return_value
        session.get.side_effect = event_parser.requests.ConnectionError()

        self.assertEqual(event_parser.get_rausgegangen_events(), [])


if __name__ == "__main__":
    unittest.main()
