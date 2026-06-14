import unittest
import sys
import os
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from mention_monitor.collector import (
    build_mention,
    extract_published_at,
    parse_date,
    parse_relative_date,
    query_matches,
)


class TestParseRelativeDate(unittest.TestCase):
    def test_minutes(self):
        result = parse_relative_date("5 минут назад")
        self.assertIsNotNone(result)
        self.assertIn("T", result)

    def test_hours(self):
        result = parse_relative_date("2 часа назад")
        self.assertIsNotNone(result)

    def test_days(self):
        result = parse_relative_date("3 дня назад")
        self.assertIsNotNone(result)

    def test_weeks(self):
        result = parse_relative_date("1 неделю назад")
        self.assertIsNotNone(result)

    def test_months(self):
        result = parse_relative_date("2 месяца назад")
        self.assertIsNotNone(result)

    def test_yo_variant(self):
        # «ё» → «е» нормализация
        result = parse_relative_date("1 минуту назад")
        self.assertIsNotNone(result)

    def test_unrecognized(self):
        self.assertIsNone(parse_relative_date("вчера"))
        self.assertIsNone(parse_relative_date(""))
        self.assertIsNone(parse_relative_date(None))


class TestParseDate(unittest.TestCase):
    def test_iso_with_timezone(self):
        result = parse_date("2026-06-01T10:00:00+03:00")
        self.assertIsNotNone(result)
        self.assertTrue(result.startswith("2026-06-01"))

    def test_iso_utc_z(self):
        result = parse_date("2026-06-01T10:00:00Z")
        self.assertIsNotNone(result)

    def test_rfc2822(self):
        result = parse_date("Mon, 01 Jun 2026 10:00:00 +0300")
        self.assertIsNotNone(result)
        self.assertIn("2026", result)

    def test_none(self):
        self.assertIsNone(parse_date(None))
        self.assertIsNone(parse_date(""))

    def test_relative_via_parse_date(self):
        result = parse_date("10 минут назад")
        self.assertIsNotNone(result)

    def test_garbage(self):
        self.assertIsNone(parse_date("не дата вообще"))


class TestQuotedPhraseMatch(unittest.TestCase):
    """Фраза в кавычках должна совпадать только при словах ПОДРЯД."""

    def test_exact_phrase_matches(self):
        self.assertTrue(
            query_matches('"Русская Европа"', "ЖК Русская Европа в Калининграде новые квартиры")
        )

    def test_phrase_matches_inflected_forms(self):
        # Косвенные падежи фразы должны проходить.
        self.assertTrue(
            query_matches('"Русская Европа"', "Купить квартиру в Русской Европе отзывы")
        )

    def test_scattered_words_do_not_match(self):
        # Главный регресс: «русских ... в Европе» НЕ должно совпадать с «Русская Европа».
        self.assertFalse(
            query_matches('"Русская Европа" интервью', "Интервью о деле русских в Европе и оружии")
        )

    def test_words_in_wrong_order_do_not_match(self):
        self.assertFalse(
            query_matches('"Русская Европа"', "О положении русских в современной Европе")
        )

    def test_phrase_with_extra_term(self):
        self.assertTrue(
            query_matches('"Русская Европа" отзывы', "ЖК Русская Европа отзывы покупателей")
        )

    def test_single_word_phrase_still_matches_anywhere(self):
        self.assertTrue(query_matches('"Филимонов"', "Губернатор Филимонов посетил Вологду"))

    def test_multiword_phrase_consecutive_in_case(self):
        self.assertTrue(
            query_matches('"молодежные игры"', "На молодежных играх выступили спортсмены")
        )


class TestPublicationDatePriority(unittest.TestCase):
    def test_extract_published_at_from_article_meta(self):
        html = """
        <html><head>
        <meta property="article:published_time" content="2019-03-11T12:00:00+03:00">
        </head><body>Архивная публикация</body></html>
        """
        published = extract_published_at(html)
        self.assertIsNotNone(published)
        self.assertTrue(published.startswith("2019-03-11"))

    def test_build_mention_prefers_article_date_over_search_result_date(self):
        item = {
            "url": "https://example.com/archive/aeroflot-story",
            "title": "Аэрофлот запустил маршрут",
            "snippet": "Новость об Аэрофлоте",
            "published_at": "2026-06-10T10:00:00+00:00",
        }
        html = """
        <html><head>
        <meta property="article:published_time" content="2019-03-11T12:00:00+03:00">
        </head><body><article>Старая публикация об Аэрофлоте</article></body></html>
        """
        with tempfile.TemporaryDirectory() as tmp:
            mention = build_mention(
                "Аэрофлот",
                '"Аэрофлот"',
                item,
                html,
                {"raw_dir": tmp},
            )
        self.assertIsNotNone(mention.get("published_at"))
        self.assertTrue(mention["published_at"].startswith("2019-03-11"))


if __name__ == "__main__":
    unittest.main()
