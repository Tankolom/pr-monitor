from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import time
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

from .analysis import detect_language, extract_entities, normalize_text, sentiment
from .config import load_config, secret_value
from .billing import account_is_active
from .db import connect, get_account, insert_mention, list_projects, reset_stale_collection_runs, save_source_report
from .fetch import clean_html_fragment, extract_description, extract_title, fetch_url, post_json, strip_html
from .logging_utils import get_logger
from .vk_auth import refresh_vk_access_token

# Глобальный таймер GDELT: не более 1 запроса каждые 5.5 секунд между любыми запусками.
_gdelt_last_request: float = 0.0
_match_morph = None
LOGGER = get_logger("collector")
DATE_REQUIRED_SOURCE_TYPES = {
    "gdelt_news",
    "google_custom_search",
    "google_news",
    "newsdata",
    "serper_google",
    "yandex_search",
}


def _gdelt_rate_limit() -> None:
    global _gdelt_last_request
    elapsed = time.monotonic() - _gdelt_last_request
    if elapsed < 5.5:
        time.sleep(5.5 - elapsed)
    _gdelt_last_request = time.monotonic()


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def parse_relative_date(value: str | None) -> str | None:
    text = (value or "").strip().lower().replace("ё", "е")
    match = re.search(r"(\d+)\s+(минут|час|день|дня|дней|недел|месяц|месяца|месяцев)\w*\s+назад", text)
    if not match:
        return None
    amount = int(match.group(1))
    unit = match.group(2)
    now = datetime.now(timezone.utc).replace(microsecond=0)
    if unit.startswith("минут"):
        dt = now - timedelta(minutes=amount)
    elif unit.startswith("час"):
        dt = now - timedelta(hours=amount)
    elif unit.startswith("д"):
        dt = now - timedelta(days=amount)
    elif unit.startswith("недел"):
        dt = now - timedelta(weeks=amount)
    elif unit.startswith("месяц"):
        dt = now - timedelta(days=amount * 30)
    else:
        return None
    return dt.isoformat()


def parse_date(value: str | None) -> str | None:
    if not value:
        return None
    relative = parse_relative_date(value)
    if relative:
        return relative
    try:
        if len(value) == 16 and value.endswith("Z") and "T" in value:
            return datetime.strptime(value, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc).isoformat()
        if len(value) >= 10 and value[:10].count("-") == 2:
            normalized = value.replace("Z", "+00:00")
            dt = datetime.fromisoformat(normalized)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat()
        dt = parsedate_to_datetime(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat()
    except Exception:
        return None


def google_news_url(query: str, language: str = "ru", region: str = "RU") -> str:
    if " " in query and '"' not in query:
        query = f'"{query}"'
    params = urllib.parse.urlencode({"q": query, "hl": language, "gl": region, "ceid": f"{region}:{language}"})
    return f"https://news.google.com/rss/search?{params}"


def google_custom_search_url(query: str, api_key: str, cx: str) -> str:
    params = urllib.parse.urlencode({"q": query, "key": api_key, "cx": cx, "num": 10})
    return f"https://www.googleapis.com/customsearch/v1?{params}"


def ok_search_url(
    query: str,
    app_key: str,
    service_token: str,
    secret_key: str,
    count: int = 20,
) -> str:
    """Build OK.ru stream.search URL with signed request."""
    params: dict[str, str] = {
        "application_key": app_key,
        "count": str(max(1, min(count, 100))),
        "format": "json",
        "method": "stream.search",
        "q": query.replace('"', ""),
    }
    # Signature: MD5(sorted_params_string + lower(MD5(service_token + secret_key)))
    sorted_str = "".join(f"{k}={v}" for k, v in sorted(params.items()))
    session_secret = hashlib.md5(f"{service_token}{secret_key}".encode("utf-8")).hexdigest().lower()
    sig = hashlib.md5(f"{sorted_str}{session_secret}".encode("utf-8")).hexdigest()
    params["access_token"] = service_token
    params["sig"] = sig
    return f"https://api.ok.ru/fb.do?{urllib.parse.urlencode(params)}"


def iter_ok_items(payload_text: str) -> list[dict]:
    """Parse OK.ru stream.search response."""
    try:
        payload = json.loads(payload_text)
    except Exception:
        return []
    if "error_code" in payload:
        raise RuntimeError(f"OK.ru API error {payload.get('error_code')}: {payload.get('error_msg', '')}")
    items = []
    for entry in payload.get("stream", []):
        # Try different text fields depending on post type
        text = ""
        entities = entry.get("entities", {})
        if isinstance(entities, dict):
            text = clean_html_fragment(
                entities.get("text") or entities.get("message") or ""
            )
        if not text:
            text = clean_html_fragment(entry.get("text") or entry.get("message") or "")
        if not text:
            continue
        author_name = (
            entry.get("author_name")
            or entry.get("author", {}).get("name", "")
            or "OK.ru"
        )
        post_url = entry.get("url") or ""
        if not post_url:
            post_id = entry.get("id", "")
            post_url = f"https://ok.ru/feed/topic/{post_id}" if post_id else "https://ok.ru"
        ts_ms = entry.get("date", 0) or 0
        published_at = (
            datetime.fromtimestamp(ts_ms / 1000, timezone.utc).isoformat()
            if ts_ms > 0 else None
        )
        items.append({
            "title": text[:120],
            "url": post_url,
            "snippet": text[:300],
            "published_at": published_at,
            "source": author_name,
            "likes":    int(entry.get("likes_count") or 0),
            "reposts":  int(entry.get("reshares_count") or 0),
            "comments": int(entry.get("comments_count") or 0),
            "views":    0,
        })
    return items


def vk_search_url(query: str, token: str, version: str = "5.199", count: int = 200, start_from: str = "") -> str:
    params = {
        "q": query.replace('"', ""),
        "count": max(1, min(int(count), 200)),  # VK отдаёт до 200 за запрос
        "extended": 1,
        "access_token": token,
        "v": version,
    }
    if start_from:
        params["start_from"] = start_from
    return f"https://api.vk.com/method/newsfeed.search?{urllib.parse.urlencode(params)}"


def vk_next_from(payload_text: str) -> str:
    """Курсор следующей страницы newsfeed.search (для глубокой пагинации)."""
    try:
        return json.loads(payload_text).get("response", {}).get("next_from", "") or ""
    except (json.JSONDecodeError, AttributeError):
        return ""


def fetch_vk_mentions(query: str, token: str, version: str, target: int, user_agent: str) -> list[dict]:
    """Глубокая пагинация VK newsfeed.search: вместо одного запроса на 50 постов
    идём по страницам (по 200) с курсором next_from, пока не наберём target или
    не кончится выдача. Это главный рычаг охвата — VK обычно крупнейший источник."""
    collected: list[dict] = []
    seen_urls: set[str] = set()
    start_from = ""
    for _ in range(12):  # жёсткий потолок 12 страниц (~2400 постов) на запрос
        url = vk_search_url(query, token, version, count=200, start_from=start_from)
        payload, _ = fetch_url(url, user_agent)
        page = iter_vk_items(payload)
        for item in page:
            if item["url"] not in seen_urls:
                seen_urls.add(item["url"])
                collected.append(item)
        start_from = vk_next_from(payload)
        if len(collected) >= target or not start_from or not page:
            break
        time.sleep(0.34)  # VK: не более ~3 запросов/сек на сервисный токен
    return collected[:target]


def yandex_search_payload(query: str, folder_id: str, page: int = 0) -> dict:
    return {
        "query": {
            "searchType": "SEARCH_TYPE_RU",
            "queryText": query.replace('"', ""),
            "page": str(page),
        },
        "folderId": folder_id,
        "responseFormat": "FORMAT_XML",
    }


def yandex_search_request(query: str, api_key: str, folder_id: str, user_agent: str, page: int = 0) -> str:
    response_text, _ = post_json(
        "https://searchapi.api.cloud.yandex.net/v2/web/search",
        yandex_search_payload(query, folder_id, page),
        user_agent,
        headers={"Authorization": f"Api-Key {api_key}"},
        timeout=25,
    )
    payload = json.loads(response_text)
    if payload.get("rawData"):
        return base64.b64decode(payload["rawData"]).decode("utf-8", errors="replace")
    if payload.get("message"):
        raise RuntimeError(payload["message"])
    raise RuntimeError(response_text[:500])


def serper_search_request(query: str, api_key: str, user_agent: str, country: str = "ru", language: str = "ru") -> str:
    return serper_search_request_limited(query, api_key, user_agent, country=country, language=language, limit=10)


def serper_search_request_limited(
    query: str,
    api_key: str,
    user_agent: str,
    country: str = "ru",
    language: str = "ru",
    limit: int = 10,
    period: str | None = None,
    page: int = 1,
) -> str:
    payload = {
        "q": query.replace('"', ""),
        "gl": country,
        "hl": language,
        "num": max(10, min(limit, 100)),
    }
    if page and page > 1:
        payload["page"] = page
    tbs = serper_tbs(period)
    if tbs:
        payload["tbs"] = tbs
    response_text, _ = post_json(
        "https://google.serper.dev/search",
        payload,
        user_agent,
        headers={"X-API-KEY": api_key},
        timeout=25,
    )
    return response_text


# Площадки, по которым ищем через site:-оператор (Telegram, Dzen, OK, VK-web,
# видео, отзовики, форумы). Поисковики мы уже оплачиваем — это бесплатный способ
# собрать площадки, к firehose которых прямого доступа нет.
# Площадки для site:-поиска — ТОЛЬКО server-rendered, где дата извлекается из HTTP.
# JS-only (dzen, t.me, vk, ok, youtube, 2gis, zoon, instagram…) исключены: их даты
# через HTTP не достать, и они съедают бюджет чтения впустую. VK/OK/Telegram при этом
# покрываются отдельными датированными источниками (VK API, RSSHub-каналы).
RU_PLATFORM_SITES = [
    # блоги и контент-платформы (датируются)
    "vc.ru", "pikabu.ru", "drive2.ru", "habr.com", "livejournal.com", "yaplakal.com",
    "spark.ru", "4pda.to",
    # профильные форумы
    "forumavia.ru", "aviaforum.ru", "forum.awd.ru", "otzyv.ru",
    # отзывы и тревел
    "otzovik.com", "irecommend.ru", "otzyvru.com", "turpravda.com", "tonkosti.ru",
    "tutu.ru", "tripadvisor.ru", "frequentflyers.ru",
    # СМИ и агрегаторы (server-rendered, с датами)
    "lenta.ru", "rbc.ru", "kommersant.ru", "vedomosti.ru", "tass.ru", "ria.ru",
    "interfax.ru", "gazeta.ru", "iz.ru", "rg.ru", "mk.ru", "aif.ru", "kp.ru",
    "fontanka.ru", "regnum.ru", "ura.news", "rtvi.com", "smi2.ru", "secretmag.ru",
    "ato.ru", "aviation-explorer.ru",
]

# Сколько площадок объединять в один поисковый запрос (через OR site:) — компромисс
# между числом платных вызовов и глубиной по каждой площадке.
SITE_SEARCH_BATCH = 6


def site_search_items(config: dict, site: str, query: str, user_agent: str,
                      fetch_limit: int, period: str | None, language: str = "ru") -> list[dict]:
    """Поиск упоминаний на одной площадке через «site:<домен> запрос». Перебирает
    поисковики (Serper -> Yandex -> Google), берёт первый, кто отдал.
    (OR-объединение площадок не используем — Serper/Google по нему возвращает 0.)"""
    q = f"site:{site} {query}"
    serper_key = secret_value(config, "SERPER_API_KEY")
    google_key = secret_value(config, "GOOGLE_SEARCH_API_KEY")
    google_cx = secret_value(config, "GOOGLE_SEARCH_CX")
    yandex_key = secret_value(config, "YANDEX_SEARCH_API_KEY")
    yandex_folder = secret_value(config, "YANDEX_FOLDER_ID")
    providers = []
    if serper_key:
        providers.append(lambda: iter_serper_items(serper_search_request_limited(
            q, serper_key, user_agent, country="ru", language=language, limit=fetch_limit, period=period)))
    if yandex_key and yandex_folder:
        providers.append(lambda: iter_yandex_items(
            yandex_search_request(q, yandex_key, yandex_folder, user_agent)))
    if google_key and google_cx:
        providers.append(lambda: iter_google_custom_items(
            fetch_url(google_custom_search_url(q, google_key, google_cx), user_agent)[0]))
    for fn in providers:
        try:
            items = fn()
            if items:
                return items[:fetch_limit]
        except Exception:
            continue
    return []


# Период сбора -> число дней (один источник правды для всех провайдеров)
PERIOD_DAYS = {"1d": 1, "3d": 3, "7d": 7, "14d": 14, "30d": 30, "60d": 60, "90d": 90}


def period_to_days(period: str | None) -> int:
    return PERIOD_DAYS.get(period or "", 30)


def serper_tbs(period: str | None) -> str | None:
    # У Google (Serper) рекуррентный фильтр только d/w/m/y — берём ближайший охватывающий.
    days = period_to_days(period)
    if days <= 1:
        return "qdr:d"
    if days <= 10:
        return "qdr:w"
    if days <= 45:
        return "qdr:m"
    return "qdr:y"


def gdelt_news_url(query: str, max_records: int = 25, period: str = "30d") -> str:
    clean_query = query.strip() or query
    if " " in clean_query and '"' not in clean_query:
        clean_query = f'"{clean_query}"'
    params = urllib.parse.urlencode(
        {
            "query": clean_query,
            "mode": "artlist",
            "format": "json",
            "sort": "DateDesc",
            "maxrecords": max(10, min(max_records, 250)),
            "timespan": gdelt_timespan(period),
        }
    )
    return f"https://api.gdeltproject.org/api/v2/doc/doc?{params}"


def gdelt_timespan(period: str) -> str:
    days = period_to_days(period)
    if days <= 14:
        return f"{days}d"
    return f"{max(1, round(days / 30))}months"


def newsdata_url(query: str, api_key: str, size: int = 10, country: str = "ru", language: str = "ru") -> str:
    params = urllib.parse.urlencode(
        {
            "apikey": api_key,
            "q": query.replace('"', ""),
            "country": country,
            "language": language,
            # /latest на бесплатном тарифе принимает size не более 10 — иначе HTTP 422.
            "size": max(1, min(size, 10)),
        }
    )
    return f"https://newsdata.io/api/1/latest?{params}"


def source_from_url(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    return parsed.netloc.replace("www.", "") or url


def should_skip_result_url(url: str) -> bool:
    parsed = urllib.parse.urlparse(url or "")
    host = parsed.netloc.lower().replace("www.", "")
    path = parsed.path.lower()
    if host == "yandex.ru" and path.startswith("/images"):
        return True
    if host == "google.com" and path.startswith("/search"):
        return True
    return False


def query_matches(query: str, text: str) -> bool:
    clean_query = query.strip()
    haystack = normalize_match_text(text)
    haystack_words = haystack.split()
    haystack_stems = {_match_token(word) for word in haystack_words}
    if not clean_query:
        return True
    include_phrases, include_words, exclude_phrases, exclude_words = parse_query_terms(clean_query)
    if any(phrase_matches(term, haystack, haystack_stems) for term in exclude_phrases):
        return False
    if any(word and _match_token(word) in haystack_stems for word in exclude_words):
        return False
    if include_phrases and not all(phrase_matches(phrase, haystack, haystack_stems) for phrase in include_phrases):
        return False
    if include_words:
        required = len(include_words)
        matched = sum(1 for word in include_words if _match_token(word) in haystack_stems)
        if required <= 3 and matched < required:
            return False
        if required > 3 and matched < max(3, round(required * 0.7)):
            return False
    return bool(include_phrases or include_words)


def project_matches(project_name: str, text: str) -> bool:
    project_words = normalize_match_text(project_name).split()
    project_stems = [_match_token(word) for word in project_words if len(word) > 3]
    project_stems = list(dict.fromkeys(project_stems))
    if not project_stems:
        return True
    haystack_stems = {_match_token(word) for word in normalize_match_text(text).split()}
    matched = sum(1 for stem in project_stems if stem in haystack_stems)
    if len(project_stems) <= 2:
        return matched == len(project_stems)
    return matched >= min(3, len(project_stems))


def normalize_match_text(value: str | None) -> str:
    normalized = (value or "").lower().replace("ё", "е")
    normalized = re.sub(r"[^0-9a-zа-я]+", " ", normalized, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", normalized).strip()


def _rough_stem(word: str) -> str:
    word = word.lower().replace("ё", "е")
    if len(word) <= 3 or not re.search(r"[а-я]", word):
        return word
    if word.endswith("й") and len(word) >= 4:
        return word[:-1]
    if len(word) <= 5 and word[-1] in "аяыиеоюу":
        return word[:-1]
    for ending in (
        "иями",
        "ями",
        "ами",
        "ого",
        "ему",
        "ыми",
        "ими",
        "ых",
        "их",
        "ая",
        "яя",
        "ое",
        "ее",
        "ые",
        "ие",
        "ой",
        "ей",
        "ом",
        "ем",
        "ам",
        "ям",
        "ах",
        "ях",
        "ов",
        "ев",
        "ий",
        "ый",
        "ой",
        "а",
        "я",
        "ы",
        "и",
        "у",
        "ю",
        "е",
        "о",
    ):
        if word.endswith(ending) and len(word) - len(ending) >= 3:
            return word[: -len(ending)]
    return word


def _get_match_morph():
    global _match_morph
    if _match_morph is None:
        try:
            import pymorphy3
            _match_morph = pymorphy3.MorphAnalyzer()
        except ImportError:
            _match_morph = False
    return None if _match_morph is False else _match_morph


def _match_token(word: str) -> str:
    clean = word.lower().replace("ё", "е")
    if len(clean) <= 3 or not re.search(r"[а-я]", clean):
        return clean
    morph = _get_match_morph()
    if morph:
        try:
            parsed = morph.parse(clean)
            if parsed:
                return parsed[0].normal_form.replace("ё", "е")
        except Exception:
            pass
    return _rough_stem(clean)


def _stem_pos_match(a: str, b: str) -> bool:
    """Совпадение двух стемов с допуском на огрубление окончаний (русск/русско)."""
    if a == b:
        return True
    if len(a) >= 4 and len(b) >= 4:
        return a.startswith(b) or b.startswith(a)
    return False


def phrase_matches(phrase: str, haystack: str, haystack_stems: set[str]) -> bool:
    if not phrase:
        return False
    # Точное вхождение фразы целиком (быстрый путь).
    if phrase in haystack:
        return True
    phrase_words = [word for word in phrase.split() if len(word) >= 3]
    if not phrase_words:
        return False
    phrase_stems = [_match_token(word) for word in phrase_words]
    # Однословная фраза: достаточно наличия стема где угодно.
    if len(phrase_stems) == 1:
        return phrase_stems[0] in haystack_stems
    # Многословная фраза в кавычках должна идти ПОДРЯД — слова друг за другом
    # (с учётом морфологии каждого слова), а не быть разбросаны по тексту.
    haystack_word_stems = [_match_token(word) for word in haystack.split()]
    span = len(phrase_stems)
    for start in range(len(haystack_word_stems) - span + 1):
        window = haystack_word_stems[start:start + span]
        if all(_stem_pos_match(w, p) for w, p in zip(window, phrase_stems)):
            return True
    return False


def parse_query_terms(query: str) -> tuple[list[str], list[str], list[str], list[str]]:
    include_phrases = []
    exclude_phrases = []
    for match in re.finditer(r'(-?)"([^"]+)"', query):
        phrase = normalize_match_text(match.group(2))
        if not phrase:
            continue
        if match.group(1):
            exclude_phrases.append(phrase)
        else:
            include_phrases.append(phrase)

    without_quotes = re.sub(r'-?"[^"]+"', " ", query)
    include_words = []
    exclude_words = []
    for raw in re.split(r"\s+", without_quotes):
        token = raw.strip()
        if not token or token.upper() in {"AND", "OR", "NOT", "И", "ИЛИ", "НЕ"}:
            continue
        is_exclude = token.startswith("-")
        word = normalize_match_text(token[1:] if is_exclude else token)
        if len(word) < 3:
            continue
        if is_exclude:
            exclude_words.append(word)
        else:
            include_words.append(word)
    return include_phrases, include_words, exclude_phrases, exclude_words


def unique_ordered(values: list[str]) -> list[str]:
    seen = set()
    result = []
    for value in values:
        clean = re.sub(r"\s+", " ", value.strip())
        key = clean.lower().replace("ё", "е")
        if not clean or key in seen:
            continue
        seen.add(key)
        result.append(clean)
    return result


def eyo_variants(value: str) -> list[str]:
    variants = [value]
    if "ё" in value.lower():
        variants.append(re.sub("ё", "е", value, flags=re.IGNORECASE))
    return unique_ordered(variants)


def unquote_query(value: str) -> str:
    return re.sub(r'"([^"]+)"', r"\1", value).strip()


def expand_project_queries(project: dict, enabled: bool = True, max_queries: int = 14) -> list[str]:
    base_queries = [q for q in project.get("queries", []) if q and q.strip()]
    if project.get("name"):
        base_queries.insert(0, f'"{project["name"]}"')
    if not enabled:
        return unique_ordered(base_queries)

    candidates = []
    event_words = [
        "новости",
        "официальный сайт",
        "пресс-релиз",
        "интервью",
    ]
    for query in base_queries:
        candidates.extend(eyo_variants(query))
        plain = unquote_query(query)
        candidates.extend(eyo_variants(plain))
        phrases = re.findall(r'"([^"]+)"', query)
        main_phrase = phrases[0] if phrases else plain
        main_phrase = main_phrase.strip()
        if len(main_phrase.split()) >= 2:
            candidates.extend(eyo_variants(f'"{main_phrase}"'))
            for word in event_words:
                candidates.extend(eyo_variants(f'"{main_phrase}" {word}'))
        words = normalize_match_text(plain).split()
        important = [word for word in words if len(word) >= 5]
        if len(important) >= 3:
            candidates.append(" ".join(important[:5]))
    return unique_ordered(candidates)[:max_queries]


def iter_rss_items(xml_text: str) -> list[dict]:
    root = ET.fromstring(xml_text)
    items = []
    for item in root.findall(".//item"):
        source_el = item.find("source")
        items.append(
            {
                "title": (item.findtext("title") or "").strip(),
                "url": (item.findtext("link") or "").strip(),
                "snippet": clean_html_fragment(item.findtext("description") or ""),
                "published_at": parse_date(item.findtext("pubDate")),
                "source": (source_el.text or "").strip() if source_el is not None else None,
            }
        )
    return items


def iter_google_custom_items(payload_text: str) -> list[dict]:
    payload = json.loads(payload_text)
    items = []
    for item in payload.get("items", []):
        items.append(
            {
                "title": item.get("title", ""),
                "url": item.get("link", ""),
                "snippet": item.get("snippet", ""),
                "published_at": None,
                "source": source_from_url(item.get("link", "")),
            }
        )
    return items


def iter_vk_items(payload_text: str) -> list[dict]:
    payload = json.loads(payload_text)
    response = payload.get("response", {})
    profiles = {str(x.get("id")): x for x in response.get("profiles", [])}
    groups = {str(-x.get("id")): x for x in response.get("groups", [])}
    items = []
    for item in response.get("items", []):
        owner_id = str(item.get("owner_id", ""))
        owner = groups.get(owner_id) or profiles.get(owner_id) or {}
        source = owner.get("name") or f"VK {owner_id}"
        text = clean_html_fragment(item.get("text", ""))
        if not text:
            continue
        post_id = item.get("id")
        url = f"https://vk.com/wall{owner_id}_{post_id}" if owner_id and post_id else "https://vk.com"
        items.append(
            {
                "title": text[:120],
                "url": url,
                "snippet": text[:300],
                "published_at": datetime.fromtimestamp(item.get("date", 0), timezone.utc).isoformat() if item.get("date") else None,
                "source": source,
                "likes": int((item.get("likes") or {}).get("count") or 0),
                "reposts": int((item.get("reposts") or {}).get("count") or 0),
                "comments": int((item.get("comments") or {}).get("count") or 0),
                "views": int((item.get("views") or {}).get("count") or 0),
            }
        )
    return items


def iter_yandex_items(xml_text: str) -> list[dict]:
    root = ET.fromstring(xml_text)
    items = []
    for doc in root.findall(".//doc"):
        url = doc.findtext("url") or doc.findtext("domain") or ""
        title = clean_html_fragment(doc.findtext("title") or "")
        passages = [clean_html_fragment(item.text or "") for item in doc.findall(".//passage")]
        snippet = " ".join(part for part in passages if part).strip()
        if not snippet:
            snippet = clean_html_fragment(doc.findtext("headline") or "")
        if not url:
            continue
        items.append(
            {
                "title": title or url,
                "url": url,
                "snippet": snippet,
                "published_at": None,
                "source": source_from_url(url),
            }
        )
    return items


def iter_serper_items(payload_text: str) -> list[dict]:
    payload = json.loads(payload_text)
    items = []
    for item in payload.get("organic", []):
        url = item.get("link", "")
        if not url:
            continue
        items.append(
            {
                "title": item.get("title", "") or url,
                "url": url,
                "snippet": item.get("snippet", ""),
                "published_at": parse_date(item.get("date")),
                "source": source_from_url(url),
            }
        )
    return items


def iter_gdelt_items(payload_text: str) -> list[dict]:
    payload = json.loads(payload_text)
    items = []
    for item in payload.get("articles", []):
        url = item.get("url", "")
        if not url:
            continue
        items.append(
            {
                "title": item.get("title", "") or url,
                "url": url,
                "snippet": item.get("snippet", "") or item.get("title", ""),
                "published_at": parse_date(item.get("seendate")),
                "source": item.get("domain") or source_from_url(url),
                "trusted_match": True,
            }
        )
    return items


def iter_newsdata_items(payload_text: str) -> list[dict]:
    payload = json.loads(payload_text)
    items = []
    for item in payload.get("results", []):
        url = item.get("link", "")
        if not url:
            continue
        items.append(
            {
                "title": item.get("title", "") or url,
                "url": url,
                "snippet": item.get("description", "") or item.get("content", "") or "",
                "published_at": parse_date(item.get("pubDate")),
                "source": item.get("source_name") or source_from_url(url),
                "trusted_match": True,
            }
        )
    return items


def _normalize_url(url: str) -> str:
    """Strip fragment, trailing slash and common tracking params for stable deduplication."""
    import urllib.parse as _up
    try:
        p = _up.urlparse(url)
        qs = _up.parse_qs(p.query, keep_blank_values=True)
        # Drop common tracking params
        for key in ("utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
                    "ref", "from", "source", "via"):
            qs.pop(key, None)
        clean_query = _up.urlencode(sorted(qs.items()), doseq=True)
        normalized = _up.urlunparse((
            p.scheme.lower(), p.netloc.lower().replace("www.", ""),
            p.path.rstrip("/"), p.params, clean_query, "",
        ))
        return normalized or url
    except Exception:
        return url


def content_hash(url: str, title: str) -> str:  # noqa: ARG001  title kept for API compat
    """Hash is URL-only so the same article from different queries stays deduplicated."""
    return hashlib.sha256(_normalize_url(url).encode("utf-8")).hexdigest()


def save_raw(raw_dir: str, digest: str, payload: dict) -> str:
    path = Path(raw_dir) / f"{digest}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(path)


# Браузерный User-Agent: многие сайты (vc.ru и др.) боту отдают заглушку без даты.
BROWSER_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36")

RU_MONTHS = {
    "янв": 1, "фев": 2, "мар": 3, "апр": 4, "мая": 5, "май": 5, "июн": 6,
    "июл": 7, "авг": 8, "сен": 9, "окт": 10, "ноя": 11, "дек": 12,
}

# Ключи дат во встроенном JSON SPA/мета (по приоритету «опубликовано» > «изменено»)
_JSON_DATE_KEYS = (
    "datePublished", "publishedAt", "published_at", "publishDate", "publish_date",
    "date_published", "firstPublishedAt", "publicationDate", "publication_date",
    "datePublish", "dateCreated", "created_at", "createdAt", "publishedDate",
)
# Строковые ISO/RFC значения дат
_DATE_STR_PATTERNS = [
    r'<meta[^>]+(?:property|name|itemprop)=["\'](?:article:published_time|og:published_time|'
    r'mediator_published_time|pubdate|publish-date|publication_date|publishdate|date|'
    r'dc\.date(?:\.issued)?|sailthru\.date|datePublished)["\'][^>]+content=["\']([^"\']+)["\']',
    r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+(?:property|name|itemprop)=["\'](?:article:published_time|datePublished|pubdate)["\']',
    r'<time[^>]+datetime=["\']([^"\']+)["\']',
]


def _unix_to_iso(value) -> str | None:
    """Unix-таймстемп (сек или мс) -> ISO UTC, с проверкой вменяемого диапазона лет."""
    try:
        v = int(value)
    except (TypeError, ValueError):
        return None
    if v > 10 ** 12:          # миллисекунды
        v //= 1000
    if not (10 ** 9 <= v <= 4 * 10 ** 9):   # ~2001..2096
        return None
    return datetime.fromtimestamp(v, timezone.utc).replace(microsecond=0).isoformat()


def _ru_visible_date(text: str) -> str | None:
    """Русская видимая дата вида «1 февраля 2019» -> ISO."""
    m = re.search(r"\b(\d{1,2})\s+([а-яё]{3,8})\.?\s+(\d{4})\b", text, re.IGNORECASE)
    if not m:
        return None
    day, mon_word, year = int(m.group(1)), m.group(2).lower()[:3], int(m.group(3))
    month = RU_MONTHS.get(mon_word)
    if not month or not (1990 <= year <= 2100) or not (1 <= day <= 31):
        return None
    try:
        return datetime(year, month, day, tzinfo=timezone.utc).isoformat()
    except ValueError:
        return None


def _sane(iso: str | None) -> str | None:
    """Отсеиваем явно битые годы."""
    if iso and "1990" <= iso[:4] <= "2099":
        return iso
    return None


def extract_published_at(html: str | None) -> str | None:
    """Достаёт дату публикации из HTML несколькими стратегиями: meta/og/itemprop,
    JSON-LD и встроенный JSON SPA (строковые ISO и unix-таймстемпы), <time datetime>,
    видимая русская дата, относительные («вчера», «N дней назад»). Каждая публикация
    имеет дату — задача найти её, а не пропустить."""
    if not html:
        return None
    head = html[:200000]
    # 1) структурированные строковые даты (meta/time)
    for pattern in _DATE_STR_PATTERNS:
        for m in re.finditer(pattern, head, re.IGNORECASE):
            parsed = _sane(parse_date(m.group(1).strip()))
            if parsed:
                return parsed
    # 2) ключи дат во встроенном JSON: "datePublished":"2026-..." или "date":1780890758
    keys = "|".join(_JSON_DATE_KEYS)
    for m in re.finditer(rf'"(?:{keys})"\s*:\s*"([^"]+)"', head):
        parsed = _sane(parse_date(m.group(1).strip()))
        if parsed:
            return parsed
    for m in re.finditer(rf'"(?:{keys}|date|time)"\s*:\s*(\d{{10,13}})\b', head):
        parsed = _sane(_unix_to_iso(m.group(1)))
        if parsed:
            return parsed
    # 3) видимая русская дата и относительные выражения
    stripped = strip_html(head)
    parsed = _sane(_ru_visible_date(stripped))
    if parsed:
        return parsed
    rel = parse_relative_date(stripped[:400])
    return _sane(rel)


def ai_extract_published_at(config: dict, text: str) -> str | None:
    """Фолбэк: когда дату не удалось вытащить регэкспами, просим ИИ найти ДАТУ ПУБЛИКАЦИИ
    в тексте страницы. Работает только если на странице есть текст (не JS-заглушка)."""
    from .ai_provider import active_provider, ai_complete
    if not active_provider(config) or not text or len(text.strip()) < 200:
        return None
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    system = ("Ты извлекаешь ДАТУ ПУБЛИКАЦИИ материала из текста веб-страницы. "
              "Верни строго одну дату в формате YYYY-MM-DD или слово NONE. "
              "Не путай с датами событий в тексте или датами в комментариях. Никакого другого текста.")
    user = (f"Сегодня {today}. Найди дату публикации этого материала.\n\n"
            f"ТЕКСТ:\n{text[:2500]}")
    try:
        res = ai_complete(config, system, user, max_tokens=12)
    except Exception:
        return None
    if not res.get("ok"):
        return None
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", res.get("text", ""))
    if not m:
        return None
    try:
        dt = datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)), tzinfo=timezone.utc)
    except ValueError:
        return None
    if not (1990 <= dt.year <= 2100) or dt > datetime.now(timezone.utc) + timedelta(days=2):
        return None
    return dt.isoformat()


def build_mention(project: str, query: str, item: dict, article_html: str | None, config: dict, account_id: int | None = None) -> dict:
    title = normalize_text(item.get("title", ""))
    snippet = normalize_text(item.get("snippet", ""))
    extracted_text = strip_html(article_html or "")[:12000] if article_html else ""
    text = extracted_text if len(extracted_text) > 80 and extracted_text != "Google News" else snippet
    combined = normalize_text(" ".join([title, snippet, text]))
    # Дата: подтверждение с самой страницы важнее даты из агрегатора/поисковой выдачи.
    # Это защищает от кейсов, когда свежая выдача ссылается на старый материал.
    published = extract_published_at(article_html) or item.get("published_at")
    if not published and extracted_text:
        published = ai_extract_published_at(config, extracted_text)
    label, score = sentiment(combined)
    language = detect_language(combined)
    digest = content_hash(item["url"], title)
    raw_path = save_raw(
        config["raw_dir"],
        digest,
        {
            "project": project,
            "query": query,
            "rss_item": item,
            "article_html": article_html,
            "collected_at": utc_now(),
        },
    )
    return {
        "account_id": account_id,
        "project": project,
        "query": query,
        "title": title or item["url"],
        "snippet": snippet,
        "text": text,
        "url": item["url"],
        "source": item.get("source"),
        "published_at": published,
        "collected_at": utc_now(),
        "sentiment": label,
        "sentiment_score": score,
        "language": language,
        "entities": extract_entities(combined),
        "raw_path": raw_path,
        "content_hash": digest,
        "likes": int(item.get("likes") or 0),
        "reposts": int(item.get("reposts") or 0),
        "comments": int(item.get("comments") or 0),
        "views": int(item.get("views") or 0),
    }


def requires_confirmed_published_at(source_type: str, item: dict) -> bool:
    if item.get("skip_match"):
        return True
    return source_type in DATE_REQUIRED_SOURCE_TYPES


def build_web_page_item(url: str, markup: str) -> dict:
    text = strip_html(markup)
    return {
        "title": extract_title(markup, url),
        "url": url,
        "snippet": extract_description(markup) or text[:280],
        "published_at": None,
        "source": source_from_url(url),
    }


def depth_fetch_limit(depth: str | None, default: int) -> int:
    # Сколько брать с каждого поискового источника на один запрос. Подняли потолки —
    # поисковики (Яндекс/Serper/GDELT/NewsData) отдают десятки-сотни, а не топ-10.
    return {
        "fast": 25,
        "standard": 60,
        "deep": 150,
    }.get(depth or "", default)


def depth_page_read_limit(depth: str | None) -> int:
    # Бюджет чтения страниц — теперь используется и для извлечения даты публикации
    # у результатов site:-поиска (без даты их нельзя проверить на принадлежность периоду).
    return {
        "fast": 80,
        "standard": 250,
        "deep": 500,
    }.get(depth or "", 250)


def depth_search_pages(depth: str | None) -> int:
    """Сколько страниц выдачи запрашивать у пагинируемых поисковиков (Яндекс/Serper)."""
    return {"fast": 2, "standard": 5, "deep": 10}.get(depth or "", 5)


def vk_fetch_target(depth: str | None) -> int:
    """Целевое число постов VK на запрос — VK богат и поддерживает глубокую пагинацию,
    поэтому берём кратно больше, чем у поисковиков (там потолок выдачи ~100-250)."""
    return {"fast": 150, "standard": 600, "deep": 1500}.get(depth or "", 600)


def collect_once(
    config_path: str = "config.json",
    fetch_pages: bool = True,
    source_types: list[str] | None = None,
    period: str = "30d",
    depth: str = "standard",
    project_name: str | None = None,
    expand_queries: bool = True,
) -> dict:
    config = load_config(config_path)
    allowed_source_types = set(source_types) if source_types is not None else None
    fetch_limit = depth_fetch_limit(depth, int(config.get("fetch_limit_per_query", 25)))
    page_read_limit = int(config.get("page_read_limit_per_run", depth_page_read_limit(depth)))
    max_queries = int(config.get("max_queries_per_project", 24))
    search_pages = depth_search_pages(depth)   # глубина пагинации Яндекс/Serper
    vk_target = vk_fetch_target(depth)          # целевой объём VK на запрос
    # Окно периода: всё с датой публикации старше отсекаем (с запасом в 1 день),
    # чтобы поисковые источники не тащили старые страницы (напр. статью 2019 года).
    period_cutoff = (datetime.now(timezone.utc) - timedelta(days=period_to_days(period) + 1)).replace(microsecond=0).isoformat()
    conn = connect(config["database"])
    reset_stale_collection_runs(conn)
    started = utc_now()
    run = conn.execute(
        "INSERT INTO collection_runs (started_at, status) VALUES (?, ?)",
        (started, "running"),
    )
    conn.commit()
    run_id = run.lastrowid
    found = 0
    inserted = 0
    error = None
    page_cache = {}
    source_cache = {}
    disabled_sources = set()
    seen_urls = set()
    page_reads = 0
    source_stats: dict[str, dict] = {}

    def _src_bucket(source: dict) -> dict:
        label = source.get("name") or source.get("url") or source["type"]
        bucket = source_stats.get(label)
        if bucket is None:
            bucket = {
                "label": label,
                "type": source["type"],
                "attempts": 0,
                "found": 0,
                "inserted": 0,
                "errors": 0,
                "disabled": False,
                "last_error": None,
            }
            source_stats[label] = bucket
        return bucket

    active_accounts: dict[int, bool] = {}
    try:
        for project in list_projects(conn):
            if project_name and project_name != "all" and project.get("name") != project_name:
                continue
            project_account_id = project.get("account_id")
            # пропускаем проекты неактивных аккаунтов (просрочка/заморозка/отмена)
            if project_account_id is not None:
                if project_account_id not in active_accounts:
                    active_accounts[project_account_id] = account_is_active(get_account(conn, project_account_id))
                if not active_accounts[project_account_id]:
                    continue
            search_queries = expand_project_queries(project, enabled=expand_queries, max_queries=max_queries)
            for query in search_queries:
                for source in config["sources"]:
                    if not source.get("enabled", True):
                        continue
                    if allowed_source_types is not None and source["type"] not in allowed_source_types:
                        continue
                    source_key = source.get("url") or source.get("name") or source["type"]
                    if source_key in disabled_sources:
                        continue
                    cur_src = _src_bucket(source)
                    cur_src["attempts"] += 1
                    if source["type"] == "google_news":
                        url = google_news_url(
                            query,
                            language=source.get("language") or project.get("language", "ru"),
                            region=source.get("region") or project.get("region", "RU"),
                        )
                        try:
                            rss_xml, _ = fetch_url(url, config["user_agent"])
                            items = iter_rss_items(rss_xml)[:fetch_limit]
                            for item in items:
                                item["trusted_match"] = True
                        except Exception as exc:
                            LOGGER.warning("source error: %s %s: %s", source.get("name"), query, exc)
                            cur_src["errors"] += 1
                            cur_src["last_error"] = str(exc)[:200]
                            if "429" in str(exc) or "403" in str(exc):
                                disabled_sources.add(source_key)
                                cur_src["disabled"] = True
                            continue
                    elif source["type"] == "google_custom_search":
                        api_key = secret_value(config, source.get("api_key_env", "GOOGLE_SEARCH_API_KEY"))
                        cx = secret_value(config, source.get("cx_env", "GOOGLE_SEARCH_CX"))
                        if not api_key or not cx:
                            continue
                        url = google_custom_search_url(query, api_key, cx)
                        try:
                            payload, _ = fetch_url(url, config["user_agent"])
                            items = iter_google_custom_items(payload)[:fetch_limit]
                            for item in items:
                                item["trusted_match"] = True
                        except Exception as exc:
                            LOGGER.warning("source error: %s %s: %s", source.get("name"), query, exc)
                            cur_src["errors"] += 1
                            cur_src["last_error"] = str(exc)[:200]
                            if "429" in str(exc) or "403" in str(exc):
                                disabled_sources.add(source_key)
                                cur_src["disabled"] = True
                            continue
                    elif source["type"] == "ok_search":
                        ok_query = f"site:ok.ru {query}"
                        serper_key = secret_value(config, "SERPER_API_KEY")
                        google_key = secret_value(config, "GOOGLE_SEARCH_API_KEY")
                        google_cx = secret_value(config, "GOOGLE_SEARCH_CX")
                        yandex_key = secret_value(config, "YANDEX_SEARCH_API_KEY")
                        yandex_folder = secret_value(config, "YANDEX_FOLDER_ID")
                        # Приоритет: прямой API Одноклассников (если заданы ключи приложения OK) —
                        # без посредников и с полным доступом к публичной ленте. Если ключей нет,
                        # ищем через поисковики: Yandex (оплачен, поддерживает site:), Google, Serper.
                        ok_app = secret_value(config, "OK_APPLICATION_KEY")
                        ok_token = secret_value(config, "OK_SERVICE_TOKEN")
                        ok_secret = secret_value(config, "OK_SECRET_KEY")
                        ok_providers = []
                        if ok_app and ok_token and ok_secret:
                            ok_providers.append(("ok_api", lambda: iter_ok_items(
                                fetch_url(ok_search_url(query, ok_app, ok_token, ok_secret, count=fetch_limit),
                                          config["user_agent"])[0])[:fetch_limit]))
                        if yandex_key and yandex_folder:
                            ok_providers.append(("yandex", lambda: iter_yandex_items(
                                yandex_search_request(ok_query, yandex_key, yandex_folder, config["user_agent"]))[:fetch_limit]))
                        if google_key and google_cx:
                            ok_providers.append(("google", lambda: iter_google_custom_items(
                                fetch_url(google_custom_search_url(ok_query, google_key, google_cx), config["user_agent"])[0])[:fetch_limit]))
                        if serper_key:
                            ok_providers.append(("serper", lambda: iter_serper_items(
                                serper_search_request_limited(ok_query, serper_key, config["user_agent"],
                                    country="ru", language=project.get("language", "ru"),
                                    limit=fetch_limit, period=period))[:fetch_limit]))
                        if not ok_providers:
                            continue
                        items = []
                        last_exc = None
                        for _pname, _fn in ok_providers:
                            try:
                                items = _fn()
                                if items:
                                    break
                            except Exception as exc:
                                last_exc = exc
                                LOGGER.warning("ok_search via %s failed (%s): %s", _pname, query, exc)
                                continue
                        if not items:
                            if last_exc is not None:
                                cur_src["errors"] += 1
                                cur_src["last_error"] = str(last_exc)[:200]
                            continue
                        for item in items:
                            item["trusted_match"] = True
                    elif source["type"] == "vk_search":
                        token = secret_value(config, "VK_SERVICE_TOKEN")
                        if not token:
                            token, _ = refresh_vk_access_token(config)
                        if not token:
                            continue
                        try:
                            items = fetch_vk_mentions(
                                query, token, source.get("api_version", "5.199"),
                                target=vk_target, user_agent=config["user_agent"],
                            )
                            for item in items:
                                item["trusted_match"] = True
                        except Exception as exc:
                            LOGGER.warning("source error: %s %s: %s", source.get("name"), query, exc)
                            cur_src["errors"] += 1
                            cur_src["last_error"] = str(exc)[:200]
                            if "429" in str(exc) or "403" in str(exc):
                                disabled_sources.add(source_key)
                                cur_src["disabled"] = True
                            continue
                    elif source["type"] == "yandex_search":
                        api_key = secret_value(config, source.get("api_key_env", "YANDEX_SEARCH_API_KEY"))
                        folder_id = secret_value(config, source.get("folder_id_env", "YANDEX_FOLDER_ID"))
                        if not api_key or not folder_id:
                            continue
                        try:
                            items = []
                            for _pg in range(search_pages):  # глубина пагинации зависит от выбранной глубины
                                xml_text = yandex_search_request(query, api_key, folder_id, config["user_agent"], page=_pg)
                                page_items = iter_yandex_items(xml_text)
                                if not page_items:
                                    break
                                items.extend(page_items)
                                if len(items) >= fetch_limit:
                                    break
                            items = items[:fetch_limit]
                            for item in items:
                                item["trusted_match"] = True
                        except Exception as exc:
                            LOGGER.warning("source error: %s %s: %s", source.get("name"), query, exc)
                            cur_src["errors"] += 1
                            cur_src["last_error"] = str(exc)[:200]
                            if "429" in str(exc) or "403" in str(exc):
                                disabled_sources.add(source_key)
                                cur_src["disabled"] = True
                            continue
                    elif source["type"] == "serper_google":
                        api_key = secret_value(config, source.get("api_key_env", "SERPER_API_KEY"))
                        if not api_key:
                            continue
                        try:
                            items = []
                            seen_serper = set()
                            # Serper отдаёт до 100 на страницу — для больших лимитов идём по страницам.
                            for _sp in range(1, max(1, (fetch_limit + 99) // 100) + 1):
                                payload = serper_search_request_limited(
                                    query,
                                    api_key,
                                    config["user_agent"],
                                    country=source.get("country", "ru"),
                                    language=source.get("language") or project.get("language", "ru"),
                                    limit=min(fetch_limit, 100),
                                    period=period,
                                    page=_sp,
                                )
                                page_items = iter_serper_items(payload)
                                new = [it for it in page_items if it.get("url") and it["url"] not in seen_serper]
                                for it in new:
                                    seen_serper.add(it["url"])
                                items.extend(new)
                                if len(items) >= fetch_limit or not page_items:
                                    break
                            items = items[:fetch_limit]
                            for item in items:
                                item["trusted_match"] = True
                        except Exception as exc:
                            LOGGER.warning("source error: %s %s: %s", source.get("name"), query, exc)
                            cur_src["errors"] += 1
                            cur_src["last_error"] = str(exc)[:200]
                            if "429" in str(exc) or "403" in str(exc):
                                disabled_sources.add(source_key)
                                cur_src["disabled"] = True
                            continue
                    elif source["type"] == "gdelt_news":
                        url = gdelt_news_url(query, max_records=fetch_limit, period=period)
                        items = []
                        gdelt_failed = False
                        for _attempt in range(2):
                            try:
                                _gdelt_rate_limit()
                                payload, _ = fetch_url(url, config["user_agent"], timeout=25)
                                items = iter_gdelt_items(payload)[:fetch_limit]
                                break
                            except Exception as exc:
                                # GDELT строго лимитирует (1 запрос / 5 сек) — на 429 ждём и повторяем
                                if "429" in str(exc) and _attempt == 0:
                                    time.sleep(6)
                                    continue
                                LOGGER.warning("source error: %s %s: %s", source.get("name"), query, exc)
                                cur_src["errors"] += 1
                                cur_src["last_error"] = str(exc)[:200]
                                if "403" in str(exc):
                                    disabled_sources.add(source_key)
                                    cur_src["disabled"] = True
                                gdelt_failed = True
                                break
                        if gdelt_failed:
                            continue
                    elif source["type"] == "newsdata":
                        api_key = secret_value(config, source.get("api_key_env", "NEWSDATA_API_KEY"))
                        if not api_key:
                            continue
                        url = newsdata_url(
                            query,
                            api_key,
                            size=fetch_limit,
                            country=source.get("country", "ru"),
                            language=source.get("language") or project.get("language", "ru"),
                        )
                        try:
                            payload, _ = fetch_url(url, config["user_agent"], timeout=25)
                            items = iter_newsdata_items(payload)[:fetch_limit]
                        except Exception as exc:
                            LOGGER.warning("source error: %s %s: %s", source.get("name"), query, exc)
                            cur_src["errors"] += 1
                            cur_src["last_error"] = str(exc)[:200]
                            if "429" in str(exc) or "403" in str(exc):
                                disabled_sources.add(source_key)
                                cur_src["disabled"] = True
                            continue
                    elif source["type"] == "site_search":
                        # Поиск по server-rendered площадкам через site:<domain>: форумы,
                        # блоги, отзовики, СМИ. Гоним ОДИН раз за срез (по основному запросу),
                        # по одной площадке за вызов — иначе слишком много платных запросов.
                        items = []
                        if search_queries and query == search_queries[0]:
                            sites = source.get("sites") or RU_PLATFORM_SITES
                            # без кавычек: site:домен Аэрофлот даёт кратно больше, чем точная фраза
                            site_query = unquote_query(query) or query
                            seen_ss = set()
                            for _site in sites:
                                try:
                                    for it in site_search_items(config, _site, site_query, config["user_agent"],
                                                                fetch_limit, period, project.get("language", "ru")):
                                        u = it.get("url")
                                        if u and u not in seen_ss:
                                            seen_ss.add(u)
                                            it["trusted_match"] = True
                                            # site:<домен> "<запрос>" уже гарантирует тему — не режем
                                            # по сниппету; чистоту обеспечит ИИ-фильтр релевантности.
                                            it["skip_match"] = True
                                            items.append(it)
                                except Exception as exc:
                                    cur_src["errors"] += 1
                                    cur_src["last_error"] = str(exc)[:200]
                    elif source["type"] == "rss":
                        url = source["url"]
                        try:
                            if url not in source_cache:
                                rss_xml, _ = fetch_url(url, config["user_agent"], timeout=7)
                                source_cache[url] = iter_rss_items(rss_xml)
                            items = source_cache[url][:fetch_limit * 4]
                        except Exception as exc:
                            LOGGER.warning("source error: %s %s: %s", source.get("name"), query, exc)
                            cur_src["errors"] += 1
                            cur_src["last_error"] = str(exc)[:200]
                            if "429" in str(exc) or "403" in str(exc):
                                disabled_sources.add(source_key)
                                cur_src["disabled"] = True
                            continue
                    elif source["type"] == "web_pages":
                        if not fetch_pages:
                            continue
                        for page_url in project.get("control_urls", []):
                            if page_reads >= page_read_limit:
                                break
                            try:
                                if page_url not in page_cache:
                                    markup, content_type = fetch_url(page_url, config["user_agent"], timeout=12)
                                    page_reads += 1
                                    if "html" not in content_type and "text" not in content_type:
                                        continue
                                    page_cache[page_url] = (build_web_page_item(page_url, markup), markup)
                                item, markup = page_cache[page_url]
                                mention = build_mention(project["name"], query, item, markup, config, project_account_id)
                                combined = " ".join([mention["title"], mention.get("snippet") or "", mention.get("text") or ""])
                                if not query_matches(query, combined):
                                    continue
                                found += 1
                                cur_src["found"] += 1
                                if insert_mention(conn, mention):
                                    inserted += 1
                                    cur_src["inserted"] += 1
                            except Exception as exc:
                                LOGGER.warning("page error: %s: %s", page_url, exc)
                            time.sleep(0.2)
                        continue
                    else:
                        continue

                    for item in items:
                        if not item.get("url"):
                            continue
                        if should_skip_result_url(item["url"]):
                            continue
                        normalized_url = item["url"].split("#", 1)[0].rstrip("/")
                        if normalized_url in seen_urls:
                            continue
                        rough_text = " ".join(
                            str(part or "") for part in [item.get("title"), item.get("snippet"), item.get("source")]
                        )
                        if not item.get("skip_match") and not project_matches(project["name"], rough_text):
                            continue
                        if not item.get("trusted_match") and not query_matches(query, rough_text):
                            continue
                        seen_urls.add(normalized_url)
                        found += 1
                        cur_src["found"] += 1
                        article_html = None
                        # Для поисковой/агрегаторной выдачи стараемся всегда подтвердить дату
                        # по самой странице. Иначе в свежий период легко пролезает ссылка на
                        # старый материал, которую агрегатор просто переиндексировал сегодня.
                        require_confirmed_date = requires_confirmed_published_at(source["type"], item)
                        need_date = require_confirmed_date
                        if (fetch_pages or need_date) and page_reads < page_read_limit:
                            try:
                                # Браузерный UA: боту многие сайты отдают заглушку без даты/текста.
                                article_html, content_type = fetch_url(item["url"], BROWSER_UA, timeout=10)
                                page_reads += 1
                                if "html" not in content_type and "text" not in content_type:
                                    article_html = None
                            except Exception:
                                article_html = None

                        mention = build_mention(project["name"], query, item, article_html, config, project_account_id)
                        pub = mention.get("published_at")
                        # Отсекаем публикации старше окна периода (напр. статью 2019 года в недельной выборке).
                        if pub and pub < period_cutoff:
                            cur_src["found"] -= 1
                            found -= 1
                            continue
                        # Для агрегаторов и site:-поиска дата публикации должна быть
                        # подтверждена. Иначе свежая ссылка легко тащит в выдачу старый
                        # материал, который был найден сегодня, но опубликован годы назад.
                        if require_confirmed_date and not pub:
                            cur_src["found"] -= 1
                            found -= 1
                            continue
                        combined = " ".join([mention["title"], mention.get("snippet") or "", mention.get("text") or ""])
                        if not item.get("skip_match") and not project_matches(project["name"], combined):
                            continue
                        # Always verify query relevance on full text — trusted sources may return noise
                        if not item.get("skip_match") and not query_matches(query, combined):
                            continue
                        if insert_mention(conn, mention):
                            inserted += 1
                            cur_src["inserted"] += 1
                        time.sleep(0.2)

        status = "finished"
    except Exception as exc:
        status = "failed"
        error = str(exc)
    finally:
        for attempt in range(3):
            try:
                conn.execute(
                    "UPDATE collection_runs SET finished_at = ?, status = ?, found = ?, inserted = ?, error = ? WHERE id = ?",
                    (utc_now(), status, found, inserted, error, run_id),
                )
                conn.commit()
                break
            except Exception:
                if attempt == 2:
                    raise
                time.sleep(0.8)
        conn.close()

    # Отчёт о работе источников за этот срез: включаем все включённые источники,
    # даже те, что ничего не дали — чтобы было видно, кто молчит.
    try:
        enabled_sources = [
            s for s in config.get("sources", [])
            if s.get("enabled", True)
            and (allowed_source_types is None or s["type"] in allowed_source_types)
        ]
        report_sources = []
        for s in enabled_sources:
            label = s.get("name") or s.get("url") or s["type"]
            bucket = source_stats.get(label) or {
                "label": label, "type": s["type"], "attempts": 0,
                "found": 0, "inserted": 0, "errors": 0, "disabled": False, "last_error": None,
            }
            report_sources.append(bucket)
        report = {
            "run_id": run_id,
            "started_at": started,
            "finished_at": utc_now(),
            "status": status,
            "total_found": found,
            "total_inserted": inserted,
            "sources": report_sources,
        }
        report_conn = connect(config["database"])
        try:
            save_source_report(report_conn, run_id, report)
        finally:
            report_conn.close()
    except Exception as exc:  # отчёт не должен ронять сбор
        LOGGER.warning("Source report skipped: %s", exc)

    audit = None
    # После успешного среза с новыми публикациями запускаем ИИ-аудит тональности.
    if status == "finished" and inserted > 0 and config.get("ai", {}).get("audit_enabled", True):
        try:
            from .ai_audit import run_collection_audit

            audit = run_collection_audit(config_path, run_id=run_id, since_iso=started)
        except Exception as exc:  # аудит не должен ронять сбор
            LOGGER.warning("AI audit skipped: %s", exc)

    return {"status": status, "found": found, "inserted": inserted, "error": error, "audit": audit}
