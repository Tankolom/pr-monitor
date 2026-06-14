import re

# Sentiment word lists in lemma / normal form (pymorphy3 normal_form)
POSITIVE_LEMMAS = {
    "активный", "благодарность", "вклад", "востребованный",
    "достижение", "завершиться", "занять", "золото",
    "лидер", "лучший", "медаль", "открытие",
    "победитель", "победа", "поддержка", "получить",
    "призёр", "развивать", "расширение",
    "рекорд", "стартовать", "финалист", "рост",
    "вырасти", "успех", "успешный", "запуск",
    "инновация", "партнёрство", "эффективность",
    "позитив", "награда", "увеличить",
    "strong", "growth", "success", "launch", "positive", "leader",
}

NEGATIVE_LEMMAS = {
    "авария", "арест", "взыскание", "долг",
    "задержать", "иск", "конфликт", "нарушение",
    "обман", "отказ", "провал", "риск",
    "санкция", "сбой", "сорвать", "скандал",
    "кризис", "суд", "штраф", "падение",
    "снижение", "жалоба", "негатив", "проблема",
    "убыток", "банкротство", "расследование",
    "утечка", "обвинение",
    "уголовный", "виновный",
    "failure", "crisis", "lawsuit", "fine", "negative", "problem",
}

# Слова-отрицания: при наличии в 2-словном окне перед тональным словом — инвертируют тональность
NEGATION = {"без", "не", "нет", "никак", "никогда", "ни", "вопреки"}

# Старые словари для fallback без pymorphy3
_POSITIVE_WORDS_FALLBACK = {
    "активно", "благодарность", "вклад", "востребован", "востребована",
    "достижение", "достижения", "завершились", "завершился", "занял",
    "заняла", "золото", "лидером", "лидирует", "лучших", "медаль",
    "медали", "открытие", "победитель", "победители", "поддержка",
    "получил", "получила", "признан", "признана", "призер", "призёр",
    "развивает", "расширение", "рекорд", "стартовали", "финалист",
    "рост", "вырос", "выросли", "успех", "успешно", "лидер", "лучший",
    "победа", "развитие", "запуск", "инновации", "партнерство",
    "эффективность", "позитив", "награда", "увеличил",
    "strong", "growth", "success", "launch", "positive", "leader",
}
_NEGATIVE_WORDS_FALLBACK = {
    "авария", "арест", "взыскание", "долг", "задержан", "иск",
    "конфликт", "нарушение", "обман", "отказ", "провал", "риск",
    "санкции", "сбой", "сорвал", "сорвали", "скандал", "кризис",
    "суд", "штраф", "падение", "снижение", "жалоба", "негатив",
    "проблема", "проблемы", "убыток", "банкротство", "расследование",
    "утечка", "обвинение",
    "failure", "crisis", "lawsuit", "fine", "negative", "problem",
}

_POSITIVE_PHRASES = [
    "признан лидером", "признана лидером", "стал победителем",
    "стала победителем", "занял первое место", "заняла первое место",
    "рост спроса", "рост прибыли", "успешно заверш", "открыли юбилейные",
]
_NEGATIVE_PHRASES = [
    "возбуждено дело", "подал иск", "подали иск",
    "признан банкротом", "утечка данных", "массовые жалобы",
]

# --- lazy NLP backends ---

_morph = None       # pymorphy3.MorphAnalyzer or False
_natasha = None     # dict with natasha tools or False


def _get_morph():
    global _morph
    if _morph is None:
        try:
            import pymorphy3
            _morph = pymorphy3.MorphAnalyzer()
        except ImportError:
            _morph = False
    return None if _morph is False else _morph


def _get_natasha():
    global _natasha
    if _natasha is None:
        try:
            from natasha import Segmenter, NewsEmbedding, NewsNERTagger
            emb = NewsEmbedding()
            _natasha = {
                "segmenter": Segmenter(),
                "ner_tagger": NewsNERTagger(emb),
            }
        except ImportError:
            _natasha = False
    return None if _natasha is False else _natasha


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def detect_language(text: str) -> str:
    sample = text or ""
    cyr = len(re.findall(r"[А-Яа-яЁё]", sample))
    lat = len(re.findall(r"[A-Za-z]", sample))
    if cyr > lat:
        return "ru"
    if lat > 0:
        return "en"
    return "unknown"


def sentiment(text: str) -> tuple[str, float]:
    morph = _get_morph()
    if morph:
        return _sentiment_morph(text, morph)
    return _sentiment_fallback(text)


def _sentiment_morph(text: str, morph) -> tuple[str, float]:
    """Тональность с лемматизацией и обнаружением отрицаний."""
    text_lower = (text or "").lower()
    # Фразовые маркеры остаются без изменений
    positive = sum(1 for p in _POSITIVE_PHRASES if p in text_lower)
    negative = sum(1 for p in _NEGATIVE_PHRASES if p in text_lower)

    raw_words = re.findall(r"[A-Za-zА-Яа-яЁё-]+", text_lower)
    # Лемматизируем только первые 300 слов для скорости
    lemmas = []
    for w in raw_words[:300]:
        parsed = morph.parse(w)
        lemmas.append(parsed[0].normal_form if parsed else w)

    for i, lemma in enumerate(lemmas):
        negated = any(lemmas[j] in NEGATION for j in range(max(0, i - 2), i))
        if lemma in POSITIVE_LEMMAS:
            if negated:
                negative += 1
            else:
                positive += 1
        elif lemma in NEGATIVE_LEMMAS:
            if negated:
                positive += 1
            else:
                negative += 1

    return _score_to_label(positive, negative)


def _sentiment_fallback(text: str) -> tuple[str, float]:
    """Словарный fallback без морфологии."""
    text_lower = (text or "").lower()
    words = re.findall(r"[A-Za-zА-Яа-яЁё-]+", text_lower)
    positive = sum(1 for w in words if w in _POSITIVE_WORDS_FALLBACK)
    negative = sum(1 for w in words if w in _NEGATIVE_WORDS_FALLBACK)
    positive += sum(1 for p in _POSITIVE_PHRASES if p in text_lower)
    negative += sum(1 for p in _NEGATIVE_PHRASES if p in text_lower)
    return _score_to_label(positive, negative)


def _score_to_label(positive: int, negative: int) -> tuple[str, float]:
    total = positive + negative
    if total == 0:
        return "neutral", 0.0
    score = (positive - negative) / total
    if score > 0.2:
        return "positive", round(score, 3)
    if score < -0.2:
        return "negative", round(score, 3)
    return "neutral", round(score, 3)


def extract_entities(text: str) -> list[str]:
    tools = _get_natasha()
    if tools:
        return _extract_entities_natasha(text, tools)
    return _extract_entities_fallback(text)


def _extract_entities_natasha(text: str, tools: dict) -> list[str]:
    """NER через natasha: различает PER, ORG, LOC."""
    try:
        from natasha import Doc
        doc = Doc(text or "")
        doc.segment(tools["segmenter"])
        doc.tag_ner(tools["ner_tagger"])
        seen: list[str] = []
        for span in doc.spans:
            name = span.text.strip()
            if len(name) > 2 and name not in seen:
                seen.append(name)
        # Headlines often contain only a surname or short brand name, which a
        # statistical NER model may skip without enough surrounding context.
        for name in _extract_entities_fallback(text):
            if name not in seen:
                seen.append(name)
        return seen[:20]
    except Exception:
        return _extract_entities_fallback(text)


def _extract_entities_fallback(text: str) -> list[str]:
    """Regex fallback: слова/фразы с заглавной буквы."""
    candidates = re.findall(
        r"\b[А-ЯЁA-Z][A-Za-zА-Яа-яЁё0-9&.-]*(?:\s+[А-ЯЁA-Z][A-Za-zА-Яа-яЁё0-9&.-]*){0,2}",
        text or "",
    )
    seen: list[str] = []
    for item in candidates:
        item = item.strip(" .,-")
        if len(item) > 2 and item not in seen:
            seen.append(item)
    return seen[:20]
