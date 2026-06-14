import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from mention_monitor.analysis import (
    normalize_text,
    detect_language,
    sentiment,
    extract_entities,
)


class TestNormalizeText(unittest.TestCase):
    def test_collapses_whitespace(self):
        self.assertEqual(normalize_text("hello   world"), "hello world")

    def test_strips_edges(self):
        self.assertEqual(normalize_text("  hi  "), "hi")

    def test_none_safe(self):
        self.assertEqual(normalize_text(None), "")


class TestDetectLanguage(unittest.TestCase):
    def test_russian(self):
        self.assertEqual(detect_language("Губернатор Вологодской области"), "ru")

    def test_english(self):
        self.assertEqual(detect_language("The governor signed the agreement"), "en")

    def test_empty(self):
        self.assertEqual(detect_language(""), "unknown")


class TestSentiment(unittest.TestCase):
    def test_positive(self):
        label, score = sentiment("Губернатор получил награду за достижения и успех")
        self.assertEqual(label, "positive")
        self.assertGreater(score, 0)

    def test_negative(self):
        label, score = sentiment("Возбуждено уголовное дело, суд признал виновным")
        self.assertEqual(label, "negative")
        self.assertLess(score, 0)

    def test_neutral(self):
        label, score = sentiment("Пресс-конференция состоится в пятницу")
        self.assertEqual(label, "neutral")

    def test_empty(self):
        label, score = sentiment("")
        self.assertEqual(label, "neutral")
        self.assertEqual(score, 0.0)

    def test_negation_flips_positive(self):
        # «без» перед «успех» должно снижать позитивный сигнал
        _, score_positive = sentiment("успех проекта подтверждён")
        _, score_negated = sentiment("без успеха проект завершился")
        # negated должен быть менее позитивным (или негативным)
        self.assertLessEqual(score_negated, score_positive)

    def test_positive_phrase(self):
        label, _ = sentiment("Спортсмен занял первое место на соревнованиях")
        self.assertEqual(label, "positive")

    def test_negative_phrase(self):
        label, _ = sentiment("Возбуждено дело по факту нарушения")
        self.assertEqual(label, "negative")


class TestExtractEntities(unittest.TestCase):
    def test_returns_list(self):
        result = extract_entities("Министерство образования России объявило")
        self.assertIsInstance(result, list)

    def test_finds_capitalized(self):
        result = extract_entities("Филимонов посетил Вологду")
        names = [e.lower() for e in result]
        self.assertTrue(any("филимонов" in n for n in names))

    def test_empty(self):
        self.assertEqual(extract_entities(""), [])

    def test_max_20(self):
        text = " ".join(f"Персона{i}" for i in range(50))
        self.assertLessEqual(len(extract_entities(text)), 20)


if __name__ == "__main__":
    unittest.main()
