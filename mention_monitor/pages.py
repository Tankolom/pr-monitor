from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from urllib.parse import parse_qs, quote, urlencode, urlparse

from .agent import analyze_project
from .charts import (
    daily_chart,
    mention_trend_chart,
    metrics_catalog,
    source_mix_chart,
    tone_stack,
)
from .ai_provider import active_provider, ai_complete, provider_label
from .claude_api import (
    AVAILABLE_MODELS as CLAUDE_MODELS,
    DEFAULT_MODEL as CLAUDE_DEFAULT_MODEL,
    claude_config,
    claude_status,
    generate_claude_analysis,
    generate_claude_chat,
)
from .yandex_gpt_api import (
    AVAILABLE_MODELS as YANDEX_GPT_MODELS,
    DEFAULT_MODEL as YANDEX_GPT_DEFAULT_MODEL,
    generate_yandex_gpt_analysis,
    generate_yandex_gpt_chat,
    yandex_gpt_config,
    yandex_gpt_status,
)
from .collector import (
    google_custom_search_url,
    iter_google_custom_items,
    iter_serper_items,
    iter_vk_items,
    iter_yandex_items,
    serper_search_request,
    vk_search_url,
    yandex_search_request,
)
from .config import load_config, load_secrets, save_config, save_secrets, secret_value
from .db import (
    _project_unique_name,
    account_quota_state,
    account_usage,
    connect,
    count_irrelevant,
    count_pending_sentiment,
    create_email_verification_token,
    create_project_row,
    create_user,
    dashboard_stats,
    delete_project_row,
    get_account,
    get_project_by_name,
    get_user_by_email,
    latest_ai_audit,
    latest_mentions,
    latest_source_report,
    list_accounts,
    list_payments,
    list_projects,
    list_users,
    normalize_email,
    record_payment,
    update_account,
    update_project_row,
    update_user,
    update_user_password,
    uses_default_admin_password,
)
from .fetch import fetch_url, strip_html
from .helpers import (
    SOURCE_HINTS,
    VK_REDIRECT_URI,
    account_id_of,
    bars,
    blank_brand_profile,
    citation_panel,
    clean_query,
    collect_source_options,
    commercial_metrics_panel,
    compact_number,
    complete_period_rows,
    create_project,
    default_from_iso,
    default_project_name,
    depth_options,
    display_date,
    display_datetime,
    display_period,
    duplicate_groups,
    esc,
    first_int,
    first_param,
    first_sentence,
    i18n_assets,
    _language_switcher_html,
    metric_card,
    nav_html,
    normalize_project_filter,
    parse_dt,
    pct,
    period_growth,
    period_options,
    project_by_name,
    project_is_visible,
    project_options,
    project_summary_cards,
    publication_feed_card,
    query_performance_panel,
    query_href,
    render_ai_text,
    report_query,
    sentiment_ru,
    source_label,
    story_groups,
    today_iso,
    user_role_label,
    visible_projects,
)
from .ollama import (
    DEFAULT_BASE_URL,
    DEFAULT_MODEL,
    generate_ollama_analysis,
    generate_ollama_chat,
    ollama_config,
    ollama_status,
)
from .mailer import build_public_url, send_verification_email, smtp_status
from .styles import STYLE
from .vk_auth import begin_vk_id_connection

AUTOFILL_EXCLUDED_DOMAINS = {
    "google.com",
    "google.ru",
    "news.google.com",
    "yandex.ru",
    "ya.ru",
    "dzen.ru",
    "vk.com",
    "vk.ru",
    "ok.ru",
    "t.me",
    "telegram.me",
    "youtube.com",
    "youtu.be",
    "rutube.ru",
    "instagram.com",
    "facebook.com",
    "x.com",
    "twitter.com",
    "wikipedia.org",
    "consultant.ru",
    "garant.ru",
    "2gis.ru",
    "rusprofile.ru",
    "myfin.by",
    "brobank.ru",
    "banki.ru",
    "naufor.ru",
    "cbr.ru",
    "eurocredit.ru",
    "bankiros.ru",
    "sravni.ru",
    "zoon.ru",
    "flamp.ru",
    "yell.ru",
    "orgpage.ru",
    "spr.ru",
    "list-org.com",
    "cataloxy.ru",
}

AUTH_STYLE = """
.auth-shell{min-height:100vh;display:grid;grid-template-columns:minmax(320px,1.05fr) minmax(360px,.95fr);gap:24px;padding:32px;background:
radial-gradient(circle at top left,rgba(40,69,122,.18),transparent 34%),
radial-gradient(circle at top right,rgba(73,165,184,.14),transparent 32%),
linear-gradient(180deg,#f5f7fb,#eef3f8)}
.auth-panel,.auth-card{border-radius:28px;border:1px solid rgba(255,255,255,.92);background:rgba(255,255,255,.74);backdrop-filter:blur(18px) saturate(160%);box-shadow:0 16px 40px rgba(40,69,122,.10),inset 0 1px 0 rgba(255,255,255,.92)}
.auth-panel{padding:40px;display:flex;flex-direction:column;justify-content:space-between;min-height:calc(100vh - 64px)}
.auth-brand{display:flex;align-items:center;gap:16px;margin-bottom:28px}.auth-logo{width:68px;height:68px;border-radius:22px;background:#17181b;color:#fff;display:grid;place-items:center;font-size:28px;font-weight:800;letter-spacing:.04em;box-shadow:inset 0 1px 0 rgba(255,255,255,.18)}
.auth-kicker{font-size:13px;letter-spacing:.12em;text-transform:uppercase;color:#9b6c36;font-weight:700;margin:0 0 12px}.auth-title{font-size:clamp(36px,4vw,56px);line-height:.98;letter-spacing:-.04em;color:#1d1d1f;font-weight:700;margin:0 0 18px}.auth-copy{max-width:560px;color:#5b6270;font-size:18px;line-height:1.55;margin:0}
.auth-points{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px;margin-top:32px}.auth-point{padding:20px;border-radius:22px;background:rgba(255,255,255,.58);border:1px solid rgba(232,236,243,.9)}.auth-point b{display:block;font-size:18px;color:#1d1d1f;margin-bottom:6px}.auth-point span{color:#667085;font-size:14px;line-height:1.45}
.auth-footer{display:flex;gap:12px;align-items:center;color:#7d8595;font-size:14px;margin-top:28px}
.auth-card{width:min(480px,100%);padding:32px;align-self:center;justify-self:center}.auth-card h1{margin:0 0 10px;color:#1d1d1f;font-size:32px;letter-spacing:-.03em}.auth-card p{margin:0 0 22px;color:#667085;line-height:1.55}
.auth-card .field{margin-bottom:16px}.auth-card .input{height:56px;border-radius:18px;font-size:17px;padding:0 18px}.auth-card .btn{height:56px;border-radius:18px;font-size:17px;font-weight:700}
.auth-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}.auth-links{display:flex;flex-wrap:wrap;gap:12px;margin-top:18px}.auth-links a{color:#28457A;font-weight:600;text-decoration:none}.auth-links a:hover{text-decoration:underline}
.auth-alert{margin:0 0 18px;padding:14px 16px;border-radius:16px;border:1px solid rgba(192,73,61,.16);background:#fff2f0;color:#9c2a24;font-weight:600}
.auth-info{margin:0 0 18px;padding:14px 16px;border-radius:16px;border:1px solid rgba(40,69,122,.12);background:#f5f9ff;color:#28457A}
.auth-note{margin-top:16px;color:#8a8a90;font-size:14px;line-height:1.45}
@media (max-width:1080px){.auth-shell{grid-template-columns:1fr;padding:20px}.auth-panel{min-height:auto;padding:28px}.auth-points{grid-template-columns:1fr}.auth-card{width:min(560px,100%)}}"""

CYR_TO_LAT = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e", "ж": "zh",
    "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m", "н": "n", "о": "o",
    "п": "p", "р": "r", "с": "s", "т": "t", "у": "u", "ф": "f", "х": "h", "ц": "ts",
    "ч": "ch", "ш": "sh", "щ": "sch", "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu",
    "я": "ya",
}


def _project_tokens(name: str) -> list[str]:
    return [token for token in re.findall(r"[A-Za-zА-Яа-яЁё0-9]+", (name or "").lower()) if len(token) >= 3]


def _latinized_tokens(name: str) -> list[str]:
    variants: list[str] = []
    for token in _project_tokens(name):
        latin = "".join(CYR_TO_LAT.get(ch, ch) for ch in token.lower())
        if len(latin) >= 3 and latin not in variants:
            variants.append(latin)
    return variants


def _base_domain(raw_url: str) -> str:
    host = (urlparse(raw_url or "").netloc or "").lower().strip()
    if host.startswith("www."):
        host = host[4:]
    return host


def _looks_like_official_domain(domain: str) -> bool:
    if not domain:
        return False
    if domain in AUTOFILL_EXCLUDED_DOMAINS:
        return False
    return not any(domain == blocked or domain.endswith("." + blocked) for blocked in AUTOFILL_EXCLUDED_DOMAINS)


def _score_autofill_candidate(
    project_name: str,
    item: dict,
    query: str,
    index: int,
    city: str = "",
    industry: str = "",
) -> tuple[int, str]:
    domain = _base_domain(item.get("url", ""))
    if not _looks_like_official_domain(domain):
        return -100, domain
    url = item.get("url", "")
    text = " ".join([item.get("title", ""), item.get("snippet", ""), domain]).lower()
    tokens = _project_tokens(project_name)
    latin_tokens = _latinized_tokens(project_name)
    city_tokens = _project_tokens(city)
    industry_tokens = _project_tokens(industry)
    domain_hits = sum(1 for token in (tokens + latin_tokens) if token in domain)
    has_official = "официаль" in text or "official" in text
    path = (urlparse(url).path or "/").strip()
    rootish_url = path in {"", "/"} or (path.count("/") <= 2 and len(path) <= 32)
    score = 0
    if index == 0:
        score += 5
    if has_official:
        score += 8
    if project_name and project_name.lower() in text:
        score += 8
    token_hits = sum(1 for token in tokens if token in text)
    score += token_hits * 2
    score += domain_hits * 4
    score += sum(1 for token in city_tokens if token in text) * 3
    score += sum(1 for token in industry_tokens if token in text) * 2
    if query.lower().find("официальный сайт") >= 0:
        score += 2
    if domain.endswith(".ru") or domain.endswith(".рф") or domain.endswith(".kz"):
        score += 1
    if rootish_url:
        score += 4
    if not has_official and not domain_hits:
        score -= 8
    if any(marker in url.lower() for marker in ["/document/", "/docs/", "/law/", "/legal/", "/news/"]):
        score -= 5
    if not rootish_url:
        score -= 3
    return score, domain


def _is_confident_website(
    project_name: str,
    best: dict,
    city: str = "",
    industry: str = "",
) -> bool:
    tokens = _project_tokens(project_name)
    best_title = (best.get("title", "") or "").lower()
    best_text = " ".join([best.get("title", ""), best.get("snippet", ""), best.get("domain", "")]).lower()
    best_has_official = "официаль" in best_text or "official" in best_text
    best_domain_hits = sum(1 for token in (tokens + _latinized_tokens(project_name)) if token in best["domain"])
    best_city_hits = sum(1 for token in _project_tokens(city) if token in best_text)
    best_industry_hits = sum(1 for token in _project_tokens(industry) if token in best_text)
    exact_name_in_title = bool(project_name and project_name.lower() in best_title)
    best_path = (urlparse(best.get("url", "")).path or "/").strip()
    rootish_url = best_path in {"", "/"} or (best_path.count("/") <= 2 and len(best_path) <= 32)
    context_ready = bool(city or industry or len(tokens) > 1 or best_domain_hits > 0 or best_has_official)
    context_confirmed = True
    if len(tokens) <= 1 and (city or industry):
        context_confirmed = (best_city_hits + best_industry_hits) > 0 or best_domain_hits > 0 or best_has_official
    if len(tokens) <= 1 and not (city or industry):
        return best["score"] >= 12 and rootish_url and (best_has_official or best_domain_hits > 0)
    if len(tokens) <= 1:
        if industry and best_industry_hits == 0:
            return False
        return context_ready and context_confirmed and best["score"] >= 12 and rootish_url and (best_has_official or best_domain_hits > 0)
    return context_ready and context_confirmed and best["score"] >= 10 and (
        best_has_official or best_domain_hits > 0 or exact_name_in_title
    )


def _suggest_relevance_hint(project_name: str, industry: str = "", city: str = "") -> str:
    if not project_name:
        return ""
    hint = f"«{project_name}»"
    if industry:
        hint += f" — {industry}"
    if city:
        hint += f", {city}"
    hint += ". Релевантны только публикации именно об этом бренде, проекте или организации."
    hint += f" НЕ релевантны упоминания слова «{project_name}» в другом контексте, если речь идёт не об этом объекте."
    return hint


def _parse_json_object(text: str) -> dict | None:
    """Достаёт первый JSON-объект из ответа ИИ (терпимо к markdown-обёртке)."""
    if not text:
        return None
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:]
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start == -1 or end <= start:
        return None
    try:
        parsed = json.loads(cleaned[start:end + 1])
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        return None


def _ai_extract_brand_profile(config: dict, name: str, context_text: str) -> dict:
    """Через ИИ извлекает карточку бренда (сфера, город, телефон, адрес, соцсети, синонимы)
    из текста сайта и сниппетов поиска. Возвращает {} при сбое или отсутствии ИИ."""
    if not active_provider(config) or not context_text.strip():
        return {}
    system = (
        "Ты помощник, который извлекает карточку бренда из текста официального сайта и "
        "результатов поиска. Возвращай строго JSON без текста вне JSON. Не выдумывай — "
        "если данных нет, оставляй пустую строку или пустой массив."
    )
    user = (
        f"Бренд/проект: «{name}».\n"
        "Верни строго JSON с полями:\n"
        '{"industry":"сфера деятельности 2-6 слов","city":"город или регион",'
        '"phone":"основной телефон","address":"физический адрес",'
        '"social_links":["ссылки на соцсети/мессенджеры: vk, t.me, instagram, youtube, ok и т.п."],'
        '"aliases":["альтернативные названия, сокращения, написание латиницей"]}\n\n'
        f"КОНТЕКСТ (текст сайта и сниппеты):\n{context_text[:6000]}"
    )
    result = ai_complete(config, system, user, max_tokens=700)
    if not result.get("ok"):
        return {}
    data = _parse_json_object(result.get("text", "")) or {}
    out: dict = {}
    for key in ("industry", "city", "phone", "address"):
        val = data.get(key)
        if isinstance(val, str) and val.strip():
            out[key] = val.strip()
    links = data.get("social_links")
    if isinstance(links, list):
        out["social_links"] = [str(x).strip() for x in links if str(x).strip()][:8]
    aliases = data.get("aliases")
    if isinstance(aliases, list):
        out["aliases"] = [str(x).strip() for x in aliases if str(x).strip()][:6]
    return out


def project_autofill(config_path: str, project_name: str, city: str = "", industry: str = "") -> dict:
    config = load_config(config_path)
    user_agent = config.get("user_agent", "MentionMonitorMVP/0.1")
    name = (project_name or "").strip()
    if not name:
        return {"ok": False, "error": "Укажите название проекта."}

    city = (city or "").strip()
    industry = (industry or "").strip()
    search_variants = [
        f'"{name}" официальный сайт',
        f'"{name}"',
        f'{name} официальный сайт',
    ]
    if city:
        search_variants.insert(1, f'"{name}" "{city}" официальный сайт')
        search_variants.append(f'"{name}" "{city}"')
    if industry:
        search_variants.append(f'"{name}" "{industry}"')
    provider_errors: list[str] = []
    candidates: list[dict] = []

    def collect_items(provider_name: str, query: str) -> list[dict]:
        try:
            if provider_name == "serper":
                api_key = secret_value(config, "SERPER_API_KEY")
                if not api_key:
                    return []
                payload = serper_search_request(query, api_key, user_agent)
                return iter_serper_items(payload)
            if provider_name == "yandex":
                api_key = secret_value(config, "YANDEX_SEARCH_API_KEY")
                folder_id = secret_value(config, "YANDEX_FOLDER_ID")
                if not api_key or not folder_id:
                    return []
                payload = yandex_search_request(query, api_key, folder_id, user_agent)
                return iter_yandex_items(payload)
            if provider_name == "google":
                api_key = secret_value(config, "GOOGLE_SEARCH_API_KEY")
                cx = secret_value(config, "GOOGLE_SEARCH_CX")
                if not api_key or not cx:
                    return []
                payload, _ = fetch_url(google_custom_search_url(query, api_key, cx), user_agent, timeout=20)
                return iter_google_custom_items(payload)
        except Exception as exc:
            provider_errors.append(f"{provider_name}: {exc}")
        return []

    enabled_types = {source.get("type") for source in config.get("sources", []) if source.get("enabled", True)}
    provider_chain: list[tuple[str, str]] = []
    if "serper_google" in enabled_types:
        provider_chain.append(("serper", "Google через Serper"))
    if "yandex_search" in enabled_types:
        provider_chain.append(("yandex", "Yandex Search API"))
    if "google_custom_search" in enabled_types:
        provider_chain.append(("google", "Google Programmable Search"))
    if not provider_chain:
        return {"ok": False, "error": "Сначала включите хотя бы один поисковый источник: Serper, Яндекс или Google."}

    chosen_provider = ""
    for provider_key, provider_label in provider_chain:
        for query in search_variants:
            items = collect_items(provider_key, query)
            if not items:
                continue
            chosen_provider = provider_label
            for idx, item in enumerate(items[:8]):
                score, domain = _score_autofill_candidate(name, item, query, idx, city=city, industry=industry)
                if score < 0:
                    continue
                candidates.append({
                    "score": score,
                    "domain": domain,
                    "title": item.get("title", ""),
                    "snippet": item.get("snippet", ""),
                    "url": item.get("url", ""),
                    "query": query,
                })
        if candidates:
            break

    if not candidates:
        detail = provider_errors[0] if provider_errors else "Не удалось найти подходящий официальный сайт."
        return {"ok": False, "error": detail}

    candidates.sort(key=lambda item: (-item["score"], len(item["domain"]), item["domain"]))
    best = candidates[0]
    confident_website = _is_confident_website(name, best, city=city, industry=industry)
    domain = best["domain"] if confident_website else ""
    alias = domain.split(".")[0] if domain and "." in domain else domain
    queries = [f'"{name}"']
    if domain and domain not in queries:
        queries.append(domain)
    if alias and alias.lower() != name.lower():
        queries.append(alias)
    if len(name.split()) == 1 and alias and alias.lower() != name.lower():
        queries.append(f'"{name}" "{alias}"')
    queries.append(f'"{name}" официальный сайт')
    deduped_queries: list[str] = []
    for item in queries:
        clean = item.strip()
        if clean and clean not in deduped_queries:
            deduped_queries.append(clean)

    aliases = [alias] if alias and alias.lower() != name.lower() else []

    # ИИ-обогащение: тянем текст официального сайта + сниппеты и просим ИИ извлечь
    # сферу/город/телефон/адрес/соцсети/синонимы — чтобы заполнить профиль целиком.
    ai_profile: dict = {}
    site_text = ""
    site_url = best.get("url", "") if domain else ""
    if site_url:
        try:
            markup, ctype = fetch_url(site_url, user_agent, timeout=12)
            if "html" in ctype or "text" in ctype:
                site_text = strip_html(markup)[:5000]
        except Exception:
            site_text = ""
    context_parts = [site_text] + [
        f"{c.get('title','')} — {c.get('snippet','')}" for c in candidates[:5]
    ]
    context_text = "\n".join(p for p in context_parts if p.strip())
    try:
        ai_profile = _ai_extract_brand_profile(config, name, context_text)
    except Exception:
        ai_profile = {}

    # ИИ-синонимы добавляем к доменному alias (без дублей, без самого названия)
    for extra in ai_profile.get("aliases", []):
        if extra and extra.lower() != name.lower() and extra not in aliases:
            aliases.append(extra)

    # город/сфера от ИИ используем для более точной подсказки релевантности
    eff_city = city or ai_profile.get("city", "")
    eff_industry = industry or ai_profile.get("industry", "")

    return {
        "ok": True,
        "provider": chosen_provider,
        "website": domain,
        "website_url": site_url,
        "website_title": best.get("title", ""),
        "aliases": aliases,
        "queries": deduped_queries,
        "industry": ai_profile.get("industry", ""),
        "city": ai_profile.get("city", ""),
        "phone": ai_profile.get("phone", ""),
        "address": ai_profile.get("address", ""),
        "social_links": ai_profile.get("social_links", []),
        "ai_enriched": bool(ai_profile),
        "relevance_hint": _suggest_relevance_hint(name, industry=eff_industry, city=eff_city),
    }

def insights_block(stats: dict, pos: int, neu: int, neg: int) -> str:
    top_source = stats["by_source"][0]["source"] if stats["by_source"] else "нет данных"
    top_day_row = max(stats["daily"], key=lambda row: row["n"]) if stats["daily"] else None
    top_day = display_period(str(top_day_row["day"]), "day", str(top_day_row["day"])) if top_day_row else "нет данных"
    top_day_count = top_day_row["n"] if top_day_row else 0
    risk = "Негатива нет" if neg == 0 else f"Негатив: {neg}"
    total = stats["total"]
    unique_sources = stats.get("unique_sources", 0)
    source_share = pct(stats["by_source"][0]["n"], total) if stats["by_source"] and total else 0
    tone_label = "спокойный" if neg == 0 else "требует внимания"
    tone_value = "0%" if neg == 0 else f"{pct(neg, total)}%"
    return f"""
    <div class="card insight-board viz-wide">
      <div class="chart-title"><h3>Короткие выводы</h3><span>оперативные сигналы по выборке</span></div>
      <div class="insight-stream">
        <div class="signal-card">
          <div class="signal-icon">⌂</div>
          <div><span>центр распространения</span><b>{esc(top_source)}</b><p>{source_share}% публикаций у лидера, всего {unique_sources} источников.</p></div>
        </div>
        <div class="signal-card hot">
          <div class="signal-icon">↟</div>
          <div><span>пик активности</span><b>{esc(top_day)}</b><p>{top_day_count} публикаций в самый активный период.</p></div>
        </div>
        <div class="signal-card calm">
          <div class="signal-icon">✓</div>
          <div><span>репутационный фон</span><b>{esc(tone_label)}</b><p>{esc(risk)} · доля негатива {tone_value}.</p></div>
        </div>
      </div>
    </div>
    """


def agent_query(project: str, sentiment_filter: str = "all", search: str = "", collected_from: str = "", collected_to: str = "") -> str:
    parts = []
    if project:
        parts.append(f"project={quote(project)}")
    if sentiment_filter and sentiment_filter != "all":
        parts.append(f"sentiment={quote(sentiment_filter)}")
    if search:
        parts.append(f"q={quote(search)}")
    if collected_from:
        parts.append(f"collected_from={quote(collected_from)}")
    if collected_to:
        parts.append(f"collected_to={quote(collected_to)}")
    return ("?" + "&".join(parts)) if parts else ""


def risk_class(level: str) -> str:
    if level == "Высокий":
        return "risk-high"
    if level == "Средний":
        return "risk-mid"
    return "risk-low"


def agent_summary_panel(analysis: dict, href: str) -> str:
    current = analysis["current"]
    previous = analysis["previous"]
    risk = analysis["risk"]
    current_start = display_date(analysis["filters"].get("current_start"))
    current_end = display_date(analysis["filters"].get("current_end"))
    themes = "".join(f"<span class='agent-tag'>{esc(item['word'])} · {item['n']}</span>" for item in analysis["themes"][:8])
    recommendations = "".join(f"<li>{esc(item)}</li>" for item in analysis["recommendations"][:4])
    return f"""
    <div class="card viz-wide agent-focus">
      <div class="chart-title">
        <h3>Что важно сейчас</h3>
        <span>ИИ-аналитик смотрит текущий срез, ретро-данные и контекст проекта</span>
      </div>
      <div class="agent-hero">
        <div class="agent-card">
          <h4>Короткий вывод</h4>
          <p>За период {esc(current_start)} — {esc(current_end)}: {current['total']} упоминаний, {current['unique_sources']} источников. К предыдущему сопоставимому периоду: {esc(analysis['growth']['mentions'])} по упоминаниям и {esc(analysis['growth']['sources'])} по источникам.</p>
          <div class="agent-grid">
            <div><div class="k">Упоминания</div><div class="agent-score">{current['total']}</div></div>
            <div><div class="k">Источники</div><div class="agent-score">{current['unique_sources']}</div></div>
            <div><div class="k">Негатив</div><div class="agent-score">{current['negative_share']}%</div></div>
            <div><div class="k">Риск</div><span class="metric-state {risk_class(risk['level'])}">{esc(risk['level'])}</span><p style="margin-top:8px">{esc(risk['reason'])}</p></div>
          </div>
        </div>
        <div class="agent-card">
          <h4>Следующие действия</h4>
          <ol class="agent-list">{recommendations or '<li>Данных пока мало: запустите сбор по проекту.</li>'}</ol>
          <div class="agent-tags">{themes or '<span class="muted">Темы появятся после сбора публикаций.</span>'}</div>
          <p style="margin-top:12px"><a class="btn" href="{esc(href)}">Открыть полный разбор</a></p>
        </div>
      </div>
      <div class="coverage-note">Ретро: предыдущий период {esc(analysis['filters']['previous_start'])} — {esc(analysis['filters']['previous_end'])}, было {previous['total']} упоминаний. В истории проекта: {analysis['context']['history_total']} публикаций и {analysis['context']['history_sources']} источников.</div>
    </div>
    """


def render_agent_page(config_path: str, query_params: dict, user: dict) -> str:
    config = load_config(config_path)
    requested_project = first_param(query_params, "project", default_project_name(config, user, "all"))
    project = normalize_project_filter(config, user, requested_project)
    sentiment_filter = first_param(query_params, "sentiment", "all")
    search = first_param(query_params, "q")
    collected_from = first_param(query_params, "collected_from")
    collected_to = first_param(query_params, "collected_to")
    run_ai = first_param(query_params, "run_ai") == "1"
    ask_ai = first_param(query_params, "ask_ai") == "1"
    chat_question = first_param(query_params, "question")
    if project == "__no_access__":
        return render_topics(config_path, "Создайте первый проект, чтобы аналитик получил контекст.", query_params, user)

    conn = connect(config["database"])
    analysis = analyze_project(
        conn,
        config,
        project,
        sentiment=sentiment_filter,
        search=search,
        collected_from=collected_from,
        collected_to=collected_to,
        account_id=account_id_of(user),
    )
    conn.close()
    ollama_settings = ollama_config(config)
    cl_settings = claude_config(config)
    yg_settings = yandex_gpt_config(config)
    # Claude takes priority; YandexGPT is next; Ollama is fallback
    _use_claude = cl_settings["enabled"]
    _use_yandex_gpt = yg_settings["enabled"] and not _use_claude
    _use_ollama = ollama_settings["enabled"] and not _use_claude and not _use_yandex_gpt
    _any_ai = _use_claude or _use_yandex_gpt or _use_ollama
    if _use_claude:
        provider_title = f"ИИ-аналитик · Claude {esc(cl_settings['model'])}"
    elif _use_yandex_gpt:
        provider_title = f"ИИ-аналитик · YandexGPT {esc(yg_settings['model'])}"
    elif _use_ollama:
        provider_title = f"Локальная ИИ · Ollama {esc(ollama_settings['model'])}"
    else:
        provider_title = "ИИ-аналитик"
    ai_href = "/agent" + agent_query(project, sentiment_filter, search, collected_from, collected_to)
    ai_href += ("&" if "?" in ai_href else "?") + "run_ai=1"
    chat_result = None
    if _use_claude and ask_ai:
        chat_result = generate_claude_chat(config, analysis, chat_question)
    elif _use_yandex_gpt and ask_ai:
        chat_result = generate_yandex_gpt_chat(config, analysis, chat_question)
    elif _use_ollama and ask_ai:
        chat_result = generate_ollama_chat(config, analysis, chat_question)
    if not _any_ai:
        ai_body = (
            "<p class='hint'>ИИ-анализ не подключён. Добавьте API-ключ Claude или YandexGPT в настройках, или запустите бесплатную локальную Ollama.</p>"
            "<div class='bar' style='margin:12px 0 0'>"
            "<a class='btn' href='/settings#ai'>Подключить Claude API</a>"
            "<a class='btn light' href='/settings#ai'>Подключить YandexGPT</a>"
            "<a class='btn light' href='/settings#ai'>Подключить Ollama</a>"
            "</div>"
        )
        ai_status = "ИИ не подключён"
    elif not run_ai:
        if _use_claude:
            provider_label = f"Claude · {esc(cl_settings['model'])}"
            test_link = "<a class='btn light' href='/claude-test'>Проверить Claude API</a>"
        elif _use_yandex_gpt:
            provider_label = f"YandexGPT · {esc(yg_settings['model'])}"
            test_link = "<a class='btn light' href='/yandex-gpt-test'>Проверить YandexGPT</a>"
        else:
            provider_label = f"Ollama · {esc(ollama_settings['model'])}"
            test_link = "<a class='btn light' href='/ollama-test'>Проверить Ollama</a>"
        ai_body = (
            "<p class='hint'>ИИ не запускается автоматически — нажмите кнопку, когда нужен текстовый разбор текущей выборки.</p>"
            f"<div class='bar' style='margin:12px 0 0'><a class='btn' href='{esc(ai_href)}'>Запустить ИИ-анализ</a>{test_link}</div>"
        )
        ai_status = f"готово к ручному запуску · {provider_label}"
    else:
        if _use_claude:
            ai_result = generate_claude_analysis(config, analysis)
            provider_name = "Claude"
            test_link = "<a class='btn light' href='/claude-test'>Проверить Claude API</a>"
        elif _use_yandex_gpt:
            ai_result = generate_yandex_gpt_analysis(config, analysis)
            provider_name = "YandexGPT"
            test_link = "<a class='btn light' href='/yandex-gpt-test'>Проверить YandexGPT</a>"
        else:
            ai_result = generate_ollama_analysis(config, analysis)
            provider_name = "Ollama"
            test_link = "<a class='btn light' href='/ollama-test'>Проверить Ollama</a>"
        if ai_result["ok"]:
            usage_note = ""
            if ai_result.get("usage"):
                u = ai_result["usage"]
                usage_note = f" · {u['input']}+{u['output']} tokens"
            ai_body = f"<div class='ai-answer'>{render_ai_text(ai_result['text'])}</div>"
            ai_status = f"{provider_name} · {esc(ai_result.get('model', ''))}{usage_note}"
        else:
            ai_body = (
                f"<p class='hint'>{esc(ai_result['message'])}</p>"
                f"<div class='bar' style='margin:12px 0 0'>"
                f"<a class='btn' href='{esc(ai_href)}'>Повторить запуск</a>"
                f"{test_link}"
                f"<a class='btn light' href='/settings#ai'>Настройки ИИ</a>"
                f"</div>"
            )
            ai_status = f"{provider_name} включён, но ответ не получен"

    if chat_result and chat_result["ok"]:
        chat_answer = (
            f"<div class='ai-question'>{esc(chat_question)}</div>"
            f"<div class='ai-answer'>{render_ai_text(chat_result['text'])}</div>"
        )
    elif chat_result:
        chat_answer = f"<div class='ai-answer'><p class='hint'>{esc(chat_result['message'])}</p></div>"
    else:
        chat_answer = (
            "<div class='ai-answer'><p class='hint'>Задайте вопрос по выборке: например, почему выросли упоминания, какие источники дают основной вклад, есть ли риск дублей или какие сюжеты стоит проверить.</p></div>"
        )

    nav = nav_html("agent", user)
    current = analysis["current"]
    previous = analysis["previous"]
    risk = analysis["risk"]
    source_rows = "".join(
        f"<div class='row'><span>{esc(row['source'])}</span><b>{row['n']}</b></div>" for row in current["top_sources"]
    )
    query_rows = "".join(
        f"<div class='row'><span>{esc(row['query'])}</span><b>{row['n']}</b></div>" for row in current["top_queries"]
    )
    theme_tags = "".join(f"<span class='agent-tag'>{esc(item['word'])} · {item['n']}</span>" for item in analysis["themes"])
    recs = "".join(f"<li>{esc(item)}</li>" for item in analysis["recommendations"])
    evidence_rows = ""
    for item in current["latest"]:
        evidence_rows += (
            "<tr>"
            f"<td><span class='pill {esc(item['sentiment'])}'>{esc(sentiment_ru(item['sentiment']))}</span></td>"
            f"<td><a href='{esc(item['url'])}' target='_blank' rel='noopener'>{esc(item['title'])}</a><div class='snippet'>{esc(item.get('snippet') or '')}</div></td>"
            f"<td>{esc(item.get('source') or 'unknown')}</td>"
            f"<td>{esc(item.get('date_value') or '')}</td>"
            "</tr>"
        )
    query_list = "".join(f"<li>{esc(item)}</li>" for item in analysis["context"]["queries"][:12])

    return f"""<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>ИИ-анализ</title>
  <link rel="icon" type="image/svg+xml" href="/icon.svg">
  <link rel="apple-touch-icon" href="/icon.svg">
  <link rel="manifest" href="/manifest.json">
  <meta name="theme-color" content="#147487">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-title" content="PR Monitor">
  <style>{STYLE}</style>{i18n_assets()}
</head>
<body>
  <header class="top">
    <h1>ИИ-анализ выборки</h1>
    <p>Агент смотрит текущий срез, предыдущий сопоставимый период и всю историю проекта.</p>
    {nav}
  </header>
  <main class="wrap">
    <form class="agent-toolbar" method="get" action="/agent">
      <select class="select" name="project">{project_options(config, project, user)}</select>
      <input class="input" name="q" placeholder="Поиск внутри выборки" value="{esc(search)}">
      <input class="input" type="date" name="collected_from" value="{esc(collected_from)}">
      <input class="input" type="date" name="collected_to" value="{esc(collected_to)}">
      <select class="select" name="sentiment">
        <option value="all" {"selected" if sentiment_filter == "all" else ""}>вся тональность</option>
        <option value="positive" {"selected" if sentiment_filter == "positive" else ""}>позитив</option>
        <option value="neutral" {"selected" if sentiment_filter == "neutral" else ""}>нейтрально</option>
        <option value="negative" {"selected" if sentiment_filter == "negative" else ""}>негатив</option>
      </select>
      <button class="btn" type="submit">Обновить анализ</button>
      <a class="btn light" href="/?project={quote(project)}">На дашборд</a>
    </form>
    <section class="card agent-focus" style="margin-bottom:14px">
      <div class="chart-title"><h3>{provider_title}</h3><span>{ai_status}</span></div>
      {ai_body}
      <div class="ai-chat">
        <form class="ai-chat-panel" method="get" action="/agent">
          <h4>Спросить по выборке</h4>
          <input type="hidden" name="project" value="{esc(project)}">
          <input type="hidden" name="q" value="{esc(search)}">
          <input type="hidden" name="collected_from" value="{esc(collected_from)}">
          <input type="hidden" name="collected_to" value="{esc(collected_to)}">
          <input type="hidden" name="sentiment" value="{esc(sentiment_filter)}">
          <input type="hidden" name="ask_ai" value="1">
          <textarea id="aiQuestion" class="textarea" name="question" placeholder="Например: какие источники дали основной рост и есть ли риск дублей?">{esc(chat_question)}</textarea>
          <div class="ai-suggestions">
            <button type="button" onclick="document.getElementById('aiQuestion').value='Какие источники дали основной вклад и что это значит?'">источники</button>
            <button type="button" onclick="document.getElementById('aiQuestion').value='Есть ли признаки дублей, перепечаток или перекоса выборки?'">дубли</button>
            <button type="button" onclick="document.getElementById('aiQuestion').value='Какие сюжеты видны в последних публикациях?'">сюжеты</button>
            <button type="button" onclick="document.getElementById('aiQuestion').value='Что проверить дальше, чтобы улучшить качество мониторинга?'">следующие шаги</button>
          </div>
          <div class="bar" style="margin:12px 0 0"><button class="btn" type="submit">Спросить ИИ</button></div>
        </form>
        <div class="ai-chat-panel">
          <h4>Ответ аналитика</h4>
          {chat_answer}
        </div>
      </div>
    </section>
    <section class="card">
      <div class="chart-title"><h3>{esc(project)}</h3><span>{esc(display_date(analysis['filters']['current_start']))} — {esc(display_date(analysis['filters']['current_end']))}</span></div>
      <div class="agent-grid">
        {metric_card("Упоминания", current["total"], f"предыдущий период: {previous['total']} · {analysis['growth']['mentions']}")}
        {metric_card("Источники", current["unique_sources"], f"предыдущий период: {previous['unique_sources']} · {analysis['growth']['sources']}")}
        {metric_card("Негатив", f"{current['negative_share']}%", f"{current['negative']} публикаций")}
        {metric_card("Риск", risk["level"], risk["reason"])}
      </div>
      <div class="coverage-note">История проекта: {analysis['context']['history_total']} публикаций, {analysis['context']['history_sources']} источников, период {esc(display_date(analysis['context']['history_first_day']))} — {esc(display_date(analysis['context']['history_last_day']))}. Концентрация главного источника: {risk['source_concentration']}%.</div>
    </section>
    <section class="agent-evidence">
      <div class="card"><h3>Рекомендации агента</h3><ol class="agent-list">{recs or '<li>Недостаточно данных для рекомендаций.</li>'}</ol></div>
      <div class="card"><h3>Темы и формулировки</h3><div class="agent-tags">{theme_tags or '<span class="muted">Темы появятся после сбора.</span>'}</div></div>
      <div class="card"><h3>Топ источников</h3>{source_rows or '<span class="muted">нет данных</span>'}</div>
      <div class="card"><h3>Какие запросы сработали</h3>{query_rows or '<span class="muted">нет данных</span>'}</div>
    </section>
    <section class="card" style="margin-top:14px">
      <h3>Контекст проекта, который видит агент</h3>
      <ol class="agent-list">{query_list or '<li>Запросы не заданы.</li>'}</ol>
    </section>
    <section style="margin-top:14px">
      <table>
        <thead><tr><th>Тональность</th><th>Публикация</th><th>Источник</th><th>Дата</th></tr></thead>
        <tbody>{evidence_rows or '<tr><td colspan="4">Нет публикаций в выбранной выборке.</td></tr>'}</tbody>
      </table>
    </section>
  </main>
</body>
</html>"""


def _ai_audit_card(audit: dict | None, project: str = "all") -> str:
    """Карточка ИИ-проверки качества данных (тональность + релевантность) для дашборда."""
    ru_label = {"positive": "позитив", "neutral": "нейтрально", "negative": "негатив"}
    if not audit:
        return (
            "<div class='card'><div class='chart-title'><h3>ИИ-проверка качества данных</h3>"
            "<span>после среза</span></div>"
            "<p class='hint'>После первого среза ИИ перепроверит публикации: уточнит "
            "тональность и исключит из статистики случайные совпадения, не относящиеся к "
            "объекту мониторинга — цифры на дашборде станут отражать экспертную оценку ИИ, "
            "а не только словарный алгоритм и поиск по ключевым словам.</p></div>"
        )
    status = audit.get("status")
    if status != "ok":
        msg = audit.get("message") or "Проверка не выполнена."
        return (
            "<div class='card'><div class='chart-title'><h3>ИИ-проверка качества данных</h3>"
            "<span>после среза</span></div>"
            f"<p class='hint'>{esc(msg)}</p></div>"
        )
    # Проектная фильтрация: показываем только публикации текущего проекта
    details = audit.get("details") or []
    scoped = bool(project and project != "all" and details)
    verdict = audit.get("verdict") or ""
    if scoped:
        rows_p = [d for d in details if d.get("project") == project]
        if not rows_p:
            return (
                "<div class='card'><div class='chart-title'><h3>ИИ-проверка качества данных</h3>"
                f"<span>проект: {esc(project)}</span></div>"
                "<p class='hint'>В последнем срезе не было новых публикаций по этому проекту — "
                "проверять нечего. Запустите срез или выберите «Все проекты».</p></div>"
            )
        # Тональность нерелевантных публикаций не входит в статистику проекта,
        # поэтому "проверено/уточнено" считаем только по релевантным.
        relevant_rows = [d for d in rows_p if d.get("relevant", True)]
        checked = len(relevant_rows)
        changes = [d for d in relevant_rows if d.get("changed")]
        excluded_items = [d for d in rows_p if not d.get("relevant", True)]
        verdict = ""  # глобальный вердикт неприменим к одному проекту
    elif details:
        # Пересчитываем из подробностей — так старые сохранённые аудиты тоже
        # отображаются корректно (без необходимости перезапускать ИИ-проверку).
        relevant_details = [d for d in details if d.get("relevant", True)]
        checked = len(relevant_details)
        changes = [d for d in relevant_details if d.get("changed")]
        excluded_items = [d for d in details if not d.get("relevant", True)]
    else:
        checked = audit.get("checked") or 0
        changes = audit.get("mismatches") or []
        excluded_items = []
    corrected = len(changes)
    excluded = len(excluded_items)
    accent = "#1f9d57" if (corrected == 0 and excluded == 0) else "#2a6df4"
    change_rows = "".join(
        f"<div class='row'><span>{esc((m.get('title') or '')[:80])}</span>"
        f"<b>{esc(ru_label.get(m.get('rule'), m.get('rule') or ''))} → "
        f"{esc(ru_label.get(m.get('ai'), m.get('ai') or ''))}</b></div>"
        for m in changes[:8]
    )
    excluded_rows = "".join(
        f"<div class='row'><span>{esc((m.get('title') or '')[:80])}</span>"
        f"<b class='muted'>{esc(m.get('source') or '')}</b></div>"
        for m in excluded_items[:8]
    )
    provider = esc(str(audit.get("provider") or "ИИ"))
    verdict = esc(verdict)
    scope_label = f"проект: {esc(project)}" if scoped else "все проекты"
    metrics_html = (
        f'<div style="display:flex;gap:28px;flex-wrap:wrap;margin:4px 0 8px">'
        f'<div><div style="font-size:30px;font-weight:700;color:{accent}">{corrected}</div>'
        f'<div class="muted">оценок тональности уточнено из {checked} проверенных</div></div>'
        + (
            f'<div><div style="font-size:30px;font-weight:700;color:#b8860b">{excluded}</div>'
            f'<div class="muted">исключено как нерелевантные</div></div>'
            if excluded else ""
        )
        + "</div>"
    )
    details_html = ""
    if change_rows:
        details_html += (
            f'<details style="margin-top:4px"><summary style="cursor:pointer;color:#2a6df4;font-weight:600">'
            f'Показать исправленные оценки ({corrected})</summary><div style="margin-top:8px">{change_rows}</div></details>'
        )
    if excluded_rows:
        details_html += (
            f'<details style="margin-top:4px"><summary style="cursor:pointer;color:#b8860b;font-weight:600">'
            f'Показать исключённые как нерелевантные ({excluded})</summary><div style="margin-top:8px">{excluded_rows}</div></details>'
        )
    if not details_html:
        details_html = '<div class="coverage-note">ИИ подтвердил все авто-оценки и релевантность выборки — коррекция не потребовалась.</div>'
    return f"""
      <div class="card">
        <div class="chart-title"><h3>ИИ-проверка качества данных</h3><span>после среза · {provider} · {scope_label}</span></div>
        {metrics_html}
        {f'<p class="hint" style="margin:6px 0 10px">{verdict}</p>' if verdict else ''}
        {details_html}
      </div>
    """


def render_dashboard(config_path: str, query_params: dict, user: dict) -> str:
    config = load_config(config_path)
    available_projects = visible_projects(config, user)
    dashboard_lang_options = "".join(
        [
            '<option value="ru">Русский</option>',
            '<option value="en">Английский</option>',
        ]
    )
    dashboard_region_options = "".join(
        [
            '<option value="RU">Россия</option>',
            '<option value="KZ">Казахстан</option>',
            '<option value="GLOBAL">Весь мир</option>',
        ]
    )
    if not available_projects:
        nav = nav_html("dashboard", user)
        return f"""<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Мониторинг упоминаний</title>
  <link rel="icon" type="image/svg+xml" href="/icon.svg">
  <link rel="apple-touch-icon" href="/icon.svg">
  <link rel="manifest" href="/manifest.json">
  <meta name="theme-color" content="#147487">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-title" content="PR Monitor">
  <style>{STYLE}</style>{i18n_assets()}
</head>
<body>
  <header class="top">
    <h1>PR Monitor</h1>
    <p>Дашборд появится здесь, как только мы создадим первый проект мониторинга и добавим в него поисковые запросы.</p>
    {nav}
  </header>
  <main class="wrap">
    <section class="workspace-hero workspace-hero-single">
      <div class="hero-main hero-solo">
        <div class="eyebrow">Дашборд проекта</div>
        <h2>Пока нет данных для показа</h2>
        <p class="muted">Сначала нужно создать проект, задать, что искать, и только потом запускать срез новостей.</p>
        <div class="hero-actions">
          <a class="btn" href="/topics">Создать первый проект</a>
          <a class="btn light" href="/settings#sources">Проверить источники</a>
        </div>
        <section class="quick-project" open>
          <summary>Создать проект прямо здесь</summary>
          <form class="quick-project-form" method="post" action="/dashboard-project">
            <div class="field">
              <label>Название проекта</label>
              <input class="input" name="project_name" placeholder="Например, Brand X" value="">
            </div>
            <div class="field">
              <label>Что искать</label>
              <textarea class="textarea" name="queries" placeholder='"Название компании"\nФИО спикера\nпродукт или событие'></textarea>
            </div>
            <div class="quick-project-actions">
              <div class="field">
                <label>Язык проекта</label>
                <select class="select" name="language">{dashboard_lang_options}</select>
              </div>
              <div class="field">
                <label>Рынок / регион</label>
                <select class="select" name="region">{dashboard_region_options}</select>
              </div>
              <button class="btn" type="submit">Создать и открыть</button>
            </div>
          </form>
          <p class="hint">Для нового проекта можно оставить одно название — сервис сам создаст первый поисковый запрос.</p>
        </section>
      </div>
    </section>
    <section class="metric-grid">
      {metric_card("Упоминания", 0, "появятся после первого сбора")}
      {metric_card("Источники", 0, "подключатся по проекту")}
      {metric_card("Динамика", "Без данных", "нужен хотя бы один запуск")}
      {metric_card("Риск", "Нет данных", "репутационный фон")}
      {metric_card("Позитив", "0%", "0 публикаций")}
      {metric_card("Негатив", "0%", "0 публикаций")}
    </section>
  </main>
</body>
</html>"""
    conn = connect(config["database"])
    account_id = account_id_of(user)
    requested_project = first_param(query_params, "project", default_project_name(config, user, "all"))
    project_filter = normalize_project_filter(config, user, requested_project)
    sentiment_filter = first_param(query_params, "sentiment", "all")
    search = first_param(query_params, "q")
    collected_from = first_param(query_params, "collected_from")
    collected_to = first_param(query_params, "collected_to")
    if not collected_from and not collected_to:
        collected_from = default_from_iso(90)
        collected_to = today_iso()
    trend_bucket = first_param(query_params, "trend_bucket", "month")
    if trend_bucket not in {"day", "week", "month"}:
        trend_bucket = "month"
    trend_months = first_int(query_params, "trend_months", 3, {1, 3, 6, 12})
    daily_days = first_int(query_params, "daily_days", 90, {7, 14, 30, 60, 90})
    daily_bucket = first_param(query_params, "daily_bucket", "day")
    if daily_bucket not in {"day", "week", "month"}:
        daily_bucket = "day"
    feed_page = first_int(query_params, "feed_page", 1)
    if feed_page < 1:
        feed_page = 1
    stats = dashboard_stats(
        conn,
        sentiment=sentiment_filter,
        search=search,
        collected_from=collected_from,
        collected_to=collected_to,
        project=project_filter,
        trend_bucket=trend_bucket,
        trend_months=trend_months,
        daily_days=daily_days,
        daily_bucket=daily_bucket,
        account_id=account_id,
    )
    stats["daily"] = complete_period_rows(stats.get("daily", []), "day", daily_bucket, collected_from, collected_to)
    stats["trend"] = complete_period_rows(stats.get("trend", []), "period", trend_bucket, collected_from, collected_to)
    mentions = latest_mentions(
        conn,
        limit=5000,
        sentiment=sentiment_filter,
        search=search,
        collected_from=collected_from,
        collected_to=collected_to,
        project=project_filter,
        account_id=account_id,
    )
    analysis = analyze_project(
        conn,
        config,
        project_filter,
        sentiment=sentiment_filter,
        search=search,
        collected_from=collected_from,
        collected_to=collected_to,
        account_id=account_id,
    )
    ai_audit = latest_ai_audit(conn)
    quota_state = account_quota_state(conn, account_id)
    conn.close()

    last_run = stats["last_run"]
    run_text = "сбор еще не запускался"
    if last_run:
        status_label = {
            "running": "сбор выполняется",
            "finished": "сбор завершён",
            "failed": "ошибка сбора",
        }.get(last_run["status"], last_run["status"])
        run_text = f"{status_label}: найдено {last_run['found']}, новых {last_run['inserted']}"

    audit_html = _ai_audit_card(ai_audit, project_filter)

    feed_limit = 20
    feed_total = len(mentions)
    feed_pages = max(1, (feed_total + feed_limit - 1) // feed_limit)
    feed_page = min(feed_page, feed_pages)
    feed_start = (feed_page - 1) * feed_limit
    feed_end = min(feed_start + feed_limit, feed_total)
    feed_cards = "".join(publication_feed_card(item) for item in mentions[feed_start:feed_end])
    feed_nav_params = {
        "project": project_filter,
        "q": search,
        "collected_from": collected_from,
        "collected_to": collected_to,
        "sentiment": sentiment_filter,
        "trend_bucket": trend_bucket,
        "trend_months": trend_months,
        "daily_days": daily_days,
        "daily_bucket": daily_bucket,
    }
    prev_href = query_href("/", {**feed_nav_params, "feed_page": max(1, feed_page - 1)})
    next_href = query_href("/", {**feed_nav_params, "feed_page": min(feed_pages, feed_page + 1)})
    prev_cls = "feed-page-btn" + (" disabled" if feed_page <= 1 else "")
    next_cls = "feed-page-btn" + (" disabled" if feed_page >= feed_pages else "")
    feed_note = (
        f"Показаны {feed_start + 1}-{feed_end} из {feed_total}."
        if feed_total
        else "Пока нет данных по выбранному фильтру."
    )
    feed_pager = f"""
      <div class="feed-footer">
        <div class="feed-limit-note">{esc(feed_note)}</div>
        <div class="feed-pages">
          <a class="{prev_cls}" href="{esc(prev_href)}#feed">Предыдущие 20</a>
          <span class="feed-page-current">страница {feed_page} из {feed_pages}</span>
          <a class="{next_cls}" href="{esc(next_href)}#feed">Следующие 20</a>
        </div>
      </div>
    """

    by_source = "".join(f"<div class='row'><span>{esc(r['source'])}</span><b>{r['n']}</b></div>" for r in stats["by_source"])
    allowed_project_names = {project.get("name") for project in visible_projects(config, user)}
    by_project = "".join(
        f"<div class='row'><span>{esc(r['project'])}</span><b>{r['n']}</b></div>"
        for r in stats["by_project"]
        if user["role"] == "admin" or r["project"] in allowed_project_names
    )
    daily = "".join(f"<div class='row'><span>{esc(display_period(str(r['day']), 'day', str(r['day'])))}</span><b>{r['n']}</b></div>" for r in stats["daily"])
    pos = stats["by_sentiment"].get("positive", 0)
    neg = stats["by_sentiment"].get("negative", 0)
    neu = stats["by_sentiment"].get("neutral", 0)
    total = stats["total"]
    unique_sources = stats.get("unique_sources", 0)
    positive_share = f"{pct(pos, total)}%"
    negative_share = f"{pct(neg, total)}%"
    coverage_quality = f"{min(100, pct(unique_sources, max(total, 1)))}%"
    report_href = "/report" + report_query(sentiment_filter, search, collected_from, collected_to, project_filter)
    api_href = "/api/mentions" + report_query(sentiment_filter, search, collected_from, collected_to, project_filter)
    agent_href = "/agent" + agent_query(project_filter, sentiment_filter, search, collected_from, collected_to)
    nav = nav_html("dashboard", user, report_href)
    if len(available_projects) <= 1 and user["role"] != "admin":
        project_switcher = f"""
          <div class="project-picker project-picker-single">
            <div class="project-current">
              <span>Текущий проект</span>
              <b>{esc(project_filter)}</b>
            </div>
            <a class="btn project-open-btn" href="/topics?project={quote(project_filter)}">Настроить проект</a>
          </div>
        """
    else:
        project_switcher = f"""
          <form class="project-picker" method="get" action="/">
            <label class="project-select-wrap">
              <span>Выберите проект</span>
              <select class="select" name="project">{project_options(config, project_filter, user)}</select>
            </label>
            <button class="btn project-open-btn" type="submit">Открыть проект</button>
          </form>
        """
    dashboard_quick_project = f"""
      <details class="quick-project">
        <summary>Создать проект прямо здесь</summary>
        <form class="quick-project-form" method="post" action="/dashboard-project">
          <div class="field">
            <label>Название проекта</label>
            <input class="input" name="project_name" placeholder="Например, Brand X" value="">
          </div>
          <div class="field">
            <label>Что искать</label>
            <textarea class="textarea" name="queries" placeholder='"Название компании"\nФИО спикера\nпродукт или событие'></textarea>
          </div>
          <div class="quick-project-actions">
            <div class="field">
              <label>Язык проекта</label>
              <select class="select" name="language">{dashboard_lang_options}</select>
            </div>
            <div class="field">
              <label>Рынок / регион</label>
              <select class="select" name="region">{dashboard_region_options}</select>
            </div>
            <button class="btn" type="submit">Создать и открыть</button>
          </div>
        </form>
        <p class="hint">Создайте проект и сразу задайте язык мониторинга и рынок, на котором будем искать упоминания.</p>
      </details>
    """
    risk_level = analysis["risk"]["level"]
    growth_label = analysis["growth"]["mentions"]
    chart_params = {
        "project": project_filter,
        "q": search,
        "collected_from": collected_from,
        "collected_to": collected_to,
        "sentiment": sentiment_filter,
        "trend_bucket": trend_bucket,
        "trend_months": str(trend_months),
        "daily_days": str(daily_days),
        "daily_bucket": daily_bucket,
    }
    def feed_filter_href(**overrides) -> str:
        params = dict(chart_params)
        params.update(overrides)
        params.pop("feed_page", None)
        return query_href("/", params) + "#feed"

    by_source = "".join(
        f"<div class='row'><a href='{esc(feed_filter_href(q=r['source']))}'>{esc(r['source'])}</a><b>{r['n']}</b></div>"
        for r in stats["by_source"]
    )

    # Операционный контекст в шапке: тариф + использование квот + статус сбора.
    from . import billing
    _qa = quota_state["account"] or {}
    _qd = quota_state["dimensions"]
    def _lim(v):
        return "∞" if v is None else str(v)
    plan_key = _qa.get("plan", "trial")
    hero_chips = (
        f'<span class="chip"><span>Тариф</span> «{esc(billing.plan_title(plan_key))}»</span>'
        f'<span class="chip"><span>проекты</span> {_qd["projects"]["used"]}/{_lim(_qd["projects"]["limit"])}</span>'
        f'<span class="chip"><span>запросы</span> {_qd["queries"]["used"]}/{_lim(_qd["queries"]["limit"])}</span>'
        f'<span class="chip"><span>сбор:</span> {esc(run_text)}</span>'
    )
    if plan_key != "enterprise":
        hero_chips += '<a class="chip" href="/upgrade" style="text-decoration:none">Повысить тариф ↗</a>'
    hero_meta = f'<div class="meta hero-meta">{hero_chips}</div>'

    return f"""<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Мониторинг упоминаний</title>
  <link rel="icon" type="image/svg+xml" href="/icon.svg">
  <link rel="apple-touch-icon" href="/icon.svg">
  <link rel="manifest" href="/manifest.json">
  <meta name="theme-color" content="#147487">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-title" content="PR Monitor">
  <style>{STYLE}</style>{i18n_assets()}
</head>
<body>
  <header class="top">
    <h1>PR Monitor</h1>
    <p>Премиальная панель для мониторинга СМИ: упоминания, динамика, тональность, перепечатки и ИИ-анализ по истории проекта.</p>
    {nav}
  </header>
  <main class="wrap">
    <section class="workspace-hero workspace-hero-single">
      <div class="hero-main hero-solo">
        <div class="eyebrow">Командный центр проекта</div>
        <h2>{esc(project_filter)}</h2>
        {hero_meta}
        <div class="hero-actions">
          {project_switcher}
          <a class="btn" href="{esc(agent_href)}">Разобрать с ИИ</a>
          <a class="btn light" href="/topics">Новый проект</a>
        </div>
        {dashboard_quick_project}
      </div>
    </section>
    <form id="filters" class="bar filter-bar" method="get" action="/" data-scroll-target="filters">
      <input type="hidden" name="project" value="{esc(project_filter)}">
      <input type="hidden" name="daily_days" value="{esc(daily_days)}">
      <input type="hidden" name="daily_bucket" value="{esc(daily_bucket)}">
      <input type="hidden" name="trend_bucket" value="{esc(trend_bucket)}">
      <input type="hidden" name="trend_months" value="{esc(trend_months)}">
      <input class="input" name="q" placeholder="Поиск внутри выборки" value="{esc(search)}">
      <label class="muted">Сбор с</label>
      <input class="input" type="date" name="collected_from" value="{esc(collected_from)}">
      <label class="muted">по</label>
      <input class="input" type="date" name="collected_to" value="{esc(collected_to)}">
      <select class="select" name="sentiment">
        <option value="all" {"selected" if sentiment_filter == "all" else ""}>вся тональность</option>
        <option value="positive" {"selected" if sentiment_filter == "positive" else ""}>позитив</option>
        <option value="neutral" {"selected" if sentiment_filter == "neutral" else ""}>нейтрально</option>
        <option value="negative" {"selected" if sentiment_filter == "negative" else ""}>негатив</option>
      </select>
      <button class="btn" type="submit">Показать</button>
      <a class="btn secondary" href="{esc(report_href)}">Excel</a>
      <a class="muted api-link" href="{esc(api_href)}" target="_blank" rel="noopener" title="Машинно-читаемые данные выборки (JSON) для интеграций — CRM, BI, боты. Те же фильтры, что на экране.">API (JSON) для интеграций ↗</a>
    </form>
    <section class="metric-grid">
      {metric_card("Упоминания", total, "в выбранном фильтре", feed_filter_href(sentiment="all"))}
      {metric_card("Источники", unique_sources, "уникальные площадки")}
      {metric_card("Динамика", growth_label, "к прошлому периоду")}
      {metric_card("Риск", risk_level, "репутационный фон")}
      {metric_card("Позитив", positive_share, f"{pos} публикаций", feed_filter_href(sentiment="positive"))}
      {metric_card("Негатив", negative_share, f"{neg} публикаций", feed_filter_href(sentiment="negative"))}
    </section>
    <form id="collect" class="collect-panel" method="post" action="/collect">
      <input type="hidden" name="mode" value="news_slice">
      <input type="hidden" name="project" value="{esc(project_filter)}">
      <div class="source-picker-head">
        <div><b>Сбор упоминаний</b><span>последний запуск: {esc(run_text)}</span></div>
        <span>Яндекс · Google/Serper · Google News · GDELT · RSS</span>
      </div>
      <div class="collect-body">
        <div class="collect-controls">
          <button class="btn collect-submit" type="submit">Собрать упоминания</button>
          <label class="collect-field"><span>Период <span class="help-dot" data-tip="За какой срок искать публикации — от 24 часов до 90 дней. Меньше период — свежее и быстрее, больше — шире охват.">?</span></span><select class="select" name="period">{period_options()}</select></label>
          <label class="collect-field"><span>Глубина <span class="help-dot" data-tip="Насколько тщательно собирать: быстрый — поверхностно и быстро, стандартный — баланс охвата и скорости (рекомендуется), глубокий — максимально полно, но дольше.">?</span></span><select class="select" name="depth">{depth_options()}</select></label>
        </div>
        <div class="collect-options">
          <label class="check-control"><input type="checkbox" name="expand_queries" value="1" checked><span>Расширять поисковые формулировки</span> <span class="help-dot" data-tip="К запросам добавятся варианты: точная фраза, форма с городом, «новости/отзывы», варианты написания. Шире охват и меньше пропусков. Выключить — искать строго по введённому.">?</span></label>
          <label class="check-control"><input type="checkbox" name="fetch_pages" value="1"><span>Читать страницы полностью</span> <span class="help-dot" data-tip="Анализировать полный текст найденных статей, а не только заголовок и сниппет. Точнее тональность и релевантность, но сбор идёт дольше.">?</span></label>
        </div>
        <div class="collect-status" id="collect-status" aria-live="polite">
          <span class="collect-status-icon" aria-hidden="true"></span>
          <div><b id="collect-status-title">Готов к запуску</b><span id="collect-status-text">После запуска здесь появится ход выполнения и результат.</span></div>
        </div>
      </div>
    </form>
    <section class="viz-grid">
      {agent_summary_panel(analysis, agent_href)}
    </section>
    <section style="margin-bottom:14px">
      {audit_html}
    </section>
    <div class="premium-section-title" id="analytics">
      <div><h2>Аналитические панели</h2><p>Динамика, источники, тональность, цитируемость и рабочие PR-метрики.</p></div>
    </div>
    <section class="viz-grid">
      {mention_trend_chart(stats.get("trend", []), trend_bucket, trend_months, chart_params)}
      {tone_stack(pos, neu, neg, chart_params)}
      {bars("Топ источников", stats["by_source"], "source", "n", href_key="source", query_params=chart_params)}
      {daily_chart(stats["daily"], daily_days, daily_bucket, chart_params)}
      {query_performance_panel(stats.get("by_query", []), chart_params)}
      {source_mix_chart(mentions, chart_params)}
      {citation_panel(mentions)}
      {commercial_metrics_panel(stats, mentions)}
    </section>
    <div class="premium-section-title">
      <div><h2 id="feed">Лента публикаций</h2><p>Доказательная база, из которой строятся графики и выводы.</p></div>
    </div>
    <section class="layout">
      <div class="publication-feed">
        {feed_cards or '<div class="card">Пока нет данных. Нажмите «Собрать упоминания».</div>'}
        {feed_pager}
      </div>
      <aside class="side">
        <div class="card"><h3>Топ источников</h3><div class="list">{by_source or '<span class="muted">нет данных</span>'}</div></div>
        <div class="card" style="margin-top:14px"><h3>Проекты</h3><div class="list">{by_project or '<span class="muted">нет данных</span>'}</div></div>
        <div class="card" style="margin-top:14px"><h3>Динамика</h3><div class="list">{daily or '<span class="muted">нет данных</span>'}</div></div>
      </aside>
    </section>
  </main>
  <script>
  document.querySelectorAll('form[data-scroll-target]').forEach(function(form) {{
    form.addEventListener('submit', function() {{
      sessionStorage.setItem('scrollTarget', form.dataset.scrollTarget || '');
    }});
  }});
  window.addEventListener('DOMContentLoaded', function() {{
    const target = sessionStorage.getItem('scrollTarget');
    if (!target) return;
    sessionStorage.removeItem('scrollTarget');
    const element = document.getElementById(target);
    if (element) setTimeout(function() {{ element.scrollIntoView({{block:'start'}}); }}, 80);
  }});
  (function() {{
    const form = document.getElementById('collect');
    if (!form) return;
    const t = function(value) {{
      return window.__uiT ? window.__uiT(value) : value;
    }};
    const button = form.querySelector('.collect-submit');
    const status = document.getElementById('collect-status');
    const title = document.getElementById('collect-status-title');
    const text = document.getElementById('collect-status-text');
    let timer = null;

    function show(state, heading, detail) {{
      status.className = 'collect-status ' + state;
      title.textContent = heading;
      text.textContent = detail;
      button.disabled = state === 'running';
      button.textContent = state === 'running' ? t('Идёт сбор…') : t('Собрать упоминания');
    }}
    function elapsed(iso) {{
      if (!iso) return '';
      const seconds = Math.max(0, Math.round((Date.now() - new Date(iso).getTime()) / 1000));
      const minutes = Math.floor(seconds / 60);
      return minutes ? minutes + ' мин ' + (seconds % 60) + ' сек' : seconds + ' сек';
    }}
    async function poll() {{
      try {{
        const response = await fetch('/api/collection-status', {{headers: {{'Accept':'application/json'}}, cache:'no-store'}});
        const data = await response.json();
        if (data.status === 'running' || data.status === 'starting') {{
          show('running', t('Собираем публикации'), t('Проект: ') + (data.project || '{esc(project_filter)}') + ' · ' + t('прошло ') + elapsed(data.started_at));
          timer = setTimeout(poll, 2000);
          return;
        }}
        if (data.status === 'finished') {{
          const zeroHint = data.found === 0 ? (' ' + t('Проверьте написание названия и поисковые фразы проекта.')) : '';
          show('success', t('Сбор завершён'), t('Найдено: ') + data.found + t(' · добавлено новых: ') + data.inserted + '.' + zeroHint);
          setTimeout(function() {{ location.reload(); }}, 1800);
          return;
        }}
        if (data.status === 'failed') {{
          show('error', t('Сбор завершился с ошибкой'), data.error || t('Не удалось получить данные от источников.'));
          return;
        }}
        show('idle', t('Готов к запуску'), t('После запуска здесь появится ход выполнения и результат.'));
      }} catch (error) {{
        show('error', t('Не удалось проверить состояние'), t('Обновите страницу и попробуйте ещё раз.'));
      }}
    }}
    form.addEventListener('submit', async function(event) {{
      event.preventDefault();
      if (button.disabled) return;
      show('running', t('Запускаем сбор'), t('Подготавливаем источники и поисковые запросы.'));
      try {{
        const response = await fetch('/collect', {{
          method: 'POST',
          headers: {{'Accept':'application/json'}},
          body: new FormData(form)
        }});
        const data = await response.json();
        if (!response.ok || data.status === 'failed') {{
          show('error', t('Не удалось запустить сбор'), data.error || t('Сервер не принял задачу.'));
          return;
        }}
        poll();
      }} catch (error) {{
        show('error', t('Не удалось запустить сбор'), t('Проверьте соединение и попробуйте снова.'));
      }}
    }});
    fetch('/api/collection-status', {{headers: {{'Accept':'application/json'}}, cache:'no-store'}})
      .then(function(response) {{ return response.json(); }})
      .then(function(data) {{ if (data.status === 'running' || data.status === 'starting') poll(); }})
      .catch(function() {{}});
  }})();
  </script>
</body>
</html>"""


def source_enabled(config: dict, source_type: str) -> bool:
    return any(source.get("type") == source_type and source.get("enabled", True) for source in config.get("sources", []))


def set_source_enabled(config: dict, source_type: str, enabled: bool) -> None:
    for source in config.get("sources", []):
        if source.get("type") == source_type:
            source["enabled"] = enabled


def get_web_pages(config: dict) -> list[str]:
    for source in config.get("sources", []):
        if source.get("type") == "web_pages":
            return source.setdefault("urls", [])
    config.setdefault("sources", []).append({"name": "Открытые страницы и каталоги", "type": "web_pages", "enabled": True, "urls": []})
    return config["sources"][-1]["urls"]


def get_rss_sources(config: dict) -> list[dict]:
    return [source for source in config.get("sources", []) if source.get("type") == "rss"]


def _quota_panel(state: dict) -> str:
    """Компактная карточка с тарифом и использованием квот (проекты/запросы/пользователи)."""
    from . import billing
    account = state.get("account") or {}
    plan = account.get("plan", "trial")
    labels = {"projects": "Проекты", "queries": "Запросы", "users": "Пользователи"}
    cells = ""
    for dim in ("projects", "queries", "users"):
        d = state["dimensions"][dim]
        limit_txt = "∞" if d["limit"] is None else str(d["limit"])
        ratio = d["ratio"]
        color = "#1f9d57"
        if d["reached"]:
            color = "#c0392b"
        elif ratio >= 0.8:
            color = "#b8860b"
        cells += (
            f'<div style="flex:1;min-width:120px">'
            f'<div class="muted" style="font-size:12px">{labels[dim]}</div>'
            f'<div style="font-size:20px;font-weight:700;color:{color}">{d["used"]} / {limit_txt}</div>'
            f'</div>'
        )
    days = billing.account_days_left(account)
    status_label = billing.ACCOUNT_STATUSES.get(account.get("status", "trial"), account.get("status", ""))
    tail = f" · осталось дней: {days}" if days is not None else ""
    upgrade = '<a class="btn light" href="/upgrade" style="align-self:center">Повысить тариф</a>' if plan != "enterprise" else ''
    return (
        '<div class="card" style="margin-bottom:18px">'
        f'<div class="chart-title"><h3>Тариф «{esc(billing.plan_title(plan))}»</h3>'
        f'<span>{esc(status_label)}{esc(tail)}</span></div>'
        f'<div style="display:flex;gap:20px;flex-wrap:wrap;margin-top:6px;align-items:center">{cells}{upgrade}</div>'
        '</div>'
    )


def render_topics(config_path: str, message: str = "", query_params: dict | None = None, user: dict | None = None) -> str:
    config = load_config(config_path)
    query_params = query_params or {}
    selected_name = normalize_project_filter(
        config,
        user,
        first_param(query_params, "project", default_project_name(config, user, "")),
    )
    project = project_by_name(config, selected_name, user)
    selected_name = project.get("name", "")
    queries = "\n".join(project.get("queries", []))
    control_urls = "\n".join(project.get("control_urls", []))
    brand = project.get("brand") or {}
    brand_social_links = "\n".join(brand.get("social_links", []))
    project_language = project.get("language") or "ru"
    project_region = project.get("region") or "RU"
    language_options = "".join(
        f'<option value="{value}" {"selected" if project_language == value else ""}>{label}</option>'
        for value, label in (
            ("ru", "Русский"),
            ("en", "Английский"),
        )
    )
    region_options = "".join(
        f'<option value="{value}" {"selected" if project_region == value else ""}>{label}</option>'
        for value, label in (
            ("RU", "Россия"),
            ("KZ", "Казахстан"),
            ("GLOBAL", "Весь мир"),
        )
    )
    sched_enabled = bool(project.get("schedule_enabled"))
    sched_interval = project.get("schedule_interval_hours") or 3
    _interval_labels = {3: "каждые 3 часа", 6: "каждые 6 часов", 12: "каждые 12 часов",
                        24: "раз в сутки", 48: "раз в 2 суток"}
    schedule_options = "".join(
        f'<option value="{h}" {"selected" if sched_interval == h else ""}>{_interval_labels[h]}</option>'
        for h in (3, 6, 12, 24, 48)
    )
    last_collected = project.get("last_collected_at")
    last_collected_txt = ("последний автосбор: " + display_datetime(last_collected)) if last_collected else "автосбор ещё не запускался"
    _qconn = connect(config["database"])
    try:
        quota_state = account_quota_state(_qconn, account_id_of(user))
    finally:
        _qconn.close()
    quota_html = _quota_panel(quota_state)
    nav = nav_html("topics", user)
    owner_field = ""
    if user and user["role"] == "admin":
        users_for_owner = []
        conn = connect(config["database"])
        try:
            users_for_owner = list_users(conn)
        finally:
            conn.close()
        owner_options = "".join(
            f'<option value="{esc(row["username"])}" {"selected" if project.get("owner") == row["username"] else ""}>{esc(row["username"])} · {esc(user_role_label(row))}</option>'
            for row in users_for_owner
            if row["is_active"]
        )
        owner_field = f"""
            <div class="field">
              <label>Владелец проекта</label>
              <select class="select" name="owner" style="width:100%;box-sizing:border-box">{owner_options}</select>
            </div>
        """
    return f"""<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Темы мониторинга</title>
  <link rel="icon" type="image/svg+xml" href="/icon.svg">
  <link rel="apple-touch-icon" href="/icon.svg">
  <link rel="manifest" href="/manifest.json">
  <meta name="theme-color" content="#147487">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-title" content="PR Monitor">
  <style>{STYLE}</style>{i18n_assets()}
</head>
<body>
  <header class="top">
    <h1>Темы мониторинга</h1>
    <p>Здесь создаются и ведутся проекты мониторинга: запросы сохраняются, к ним можно вернуться и продолжить статистику.</p>
    {nav}
  </header>
  <main class="wrap">
    {f'<div class="card" style="margin-bottom:18px"><b>{esc(message)}</b></div>' if message else ''}
    {quota_html}
    <div class="pagehead">
      <div><h2>Проекты и поисковые запросы</h2><p>Выберите проект слева, отредактируйте запросы и запускайте срез на дашборде по этому же проекту.</p></div>
      <a class="btn light" href="/?project={quote(selected_name)}">Открыть статистику проекта</a>
    </div>
    <section class="split">
      <aside class="card side-nav">
        <a href="#projects">Сохраненные проекты</a>
        <a href="#project">Текущий проект</a>
        <a href="#brand">Профиль бренда</a>
        <a href="#queries">Запросы для анализа</a>
        <a href="#control-urls">Контрольные URL</a>
        <a href="#schedule">Автосбор</a>
        <a href="#tips">Подсказки</a>
        <div class="project-list" id="projects">
          {project_summary_cards(config, selected_name, user)}
        </div>
        <form method="post" action="/topics" style="margin-top:14px">
          <input type="hidden" name="action" value="create">
          <button class="btn light" type="submit" style="width:100%">Новый проект</button>
        </form>
      </aside>
      <div>
        <form method="post" action="/topics">
          <input type="hidden" name="action" value="save">
          <input type="hidden" name="original_project_name" value="{esc(selected_name)}">
          <div class="provider" id="project">
            <div class="provider-head"><div><h3>Проект</h3><small>Название проекта связывает запросы, упоминания, графики и отчеты.</small></div><span class="chip">сохранен</span></div>
            <div class="field">
              <label>Название проекта <span class="help-dot" data-tip="Это рабочее название внутри кабинета. По нему сохраняется история запусков, графики и выгрузки.">?</span></label>
              <input id="projectNameInput" class="input" name="project_name" value="{esc(project.get('name', ''))}" placeholder="Например: Георгий Филимонов" style="width:100%;box-sizing:border-box">
            </div>
            <div class="settings-overview" style="margin:0 0 14px">
              <div class="field" style="margin:0">
                <label>Язык проекта <span class="help-dot" data-tip="Нужен для англоязычных проектов и внешней продажи. Влияет на язык интерфейса проекта, подсказок и будущих шаблонов.">?</span></label>
                <select class="select" name="language" style="width:100%;box-sizing:border-box">{language_options}</select>
              </div>
              <div class="field" style="margin:0">
                <label>Рынок / регион <span class="help-dot" data-tip="Базовый рынок проекта. Нужен для международных кейсов, локализации и дальнейшего расширения источников.">?</span></label>
                <select class="select" name="region" style="width:100%;box-sizing:border-box">{region_options}</select>
              </div>
            </div>
            {owner_field}
            <div class="bar" style="margin:0">
              <a class="btn light" href="/?project={quote(selected_name)}">Смотреть статистику</a>
              <button class="btn" type="submit">Сохранить проект</button>
            </div>
          </div>
          <div class="provider" id="brand" style="margin-top:18px">
            <div class="provider-head"><div><h3>Профиль бренда</h3><small>Эти данные не идут в поиск напрямую, но помогают платформе и ИИ точнее находить и фильтровать публикации именно о вашем бренде.</small></div></div>
            <input type="hidden" name="brand_form" value="1">
            <div class="field">
              <label>Сайт <span class="help-dot" data-tip="Один домен, без https:// и www — например: smartoffice39.ru. Используется как точный маркер бренда.">?</span></label>
              <input id="brandWebsiteInput" class="input" name="brand_website" value="{esc(brand.get('website', ''))}" data-original-value="{esc(brand.get('website', ''))}" placeholder="smartoffice39.ru" style="width:100%;box-sizing:border-box">
            </div>
            <div class="field">
              <label>Город / регион <span class="help-dot" data-tip="Одно значение — город или регион, где работает бренд. Используется при формировании поисковых запросов.">?</span></label>
              <input id="brandCityInput" class="input" name="brand_city" value="{esc(brand.get('city', ''))}" data-original-value="{esc(brand.get('city', ''))}" placeholder="Калининград" style="width:100%;box-sizing:border-box">
            </div>
            <div class="field">
              <label>Сфера деятельности <span class="help-dot" data-tip="Коротко, одной фразой — например: коворкинг и аренда офисов. Особенно важно, если название бренда — обычное слово («Сфера», «Горизонт», «Расцвет»): поможет ИИ отличать ваш бренд от случайных совпадений слова.">?</span></label>
              <input id="brandIndustryInput" class="input" name="brand_industry" value="{esc(brand.get('industry', ''))}" data-original-value="{esc(brand.get('industry', ''))}" placeholder="Коворкинг и аренда офисов" style="width:100%;box-sizing:border-box">
            </div>
            <div class="field">
              <label>Альтернативные названия <span class="help-dot" data-tip="Через запятую: сокращения, варианты написания, домен без зоны и т.п. Например: смарт-офис сфера, smartoffice39">?</span></label>
              <input id="brandAliasesInput" class="input" name="brand_aliases" value="{esc(brand.get('aliases', ''))}" data-original-value="{esc(brand.get('aliases', ''))}" placeholder="смарт-офис сфера, smartoffice39" style="width:100%;box-sizing:border-box">
            </div>
            <div class="field">
              <label>Телефон <span class="help-dot" data-tip="Через запятую, если их несколько. Помогает находить репосты и упоминания без названия бренда.">?</span></label>
              <input id="brandPhoneInput" class="input" name="brand_phone" value="{esc(brand.get('phone', ''))}" data-original-value="{esc(brand.get('phone', ''))}" placeholder="+7 4012 360555" style="width:100%;box-sizing:border-box">
            </div>
            <div class="field">
              <label>Адрес <span class="help-dot" data-tip="Один физический адрес — офис, точка продаж. Используется как уточняющий ориентир, не как запрос.">?</span></label>
              <input id="brandAddressInput" class="input" name="brand_address" value="{esc(brand.get('address', ''))}" data-original-value="{esc(brand.get('address', ''))}" placeholder="г. Калининград, ул. Генерал-лейтенанта Озерова, 17Б" style="width:100%;box-sizing:border-box">
            </div>
            <div class="field">
              <label>Соцсети и каналы бренда <span class="help-dot" data-tip="Официальные группы/страницы — каждая ссылка с новой строки. Помогают не путать публикации бренда с чужими.">?</span></label>
              <textarea id="brandSocialInput" class="textarea" name="brand_social_links" data-original-value="{esc(brand_social_links)}" placeholder="https://vk.com/smartoffice39&#10;https://t.me/smartoffice39" style="min-height:90px">{esc(brand_social_links)}</textarea>
            </div>
            <div class="field">
              <label>Подсказка для ИИ-фильтра релевантности <span class="help-dot" data-tip="Свободный текст для ИИ: что считать релевантным, а что нет. Особенно важно, если название — обычное слово. Можно оставить пустым и заполнить черновик кнопкой ниже.">?</span></label>
              <textarea id="relevanceHintInput" class="textarea" name="relevance_hint" data-original-value="{esc(project.get('relevance_hint', ''))}" placeholder="«Название» — это [сфера деятельности] в [город]. Релевантны только публикации об этом объекте. НЕ релевантны упоминания слова «название» в обычном словарном значении." style="min-height:110px">{esc(project.get('relevance_hint', ''))}</textarea>
            </div>
            <div class="query-suggest-box">
              <button id="autofillBrandButton" class="btn light" type="button" onclick="autofillBrandProfile()">Заполнить профиль из интернета</button>
              <button class="btn light" type="button" onclick="suggestFromBrandProfile()">Сгенерировать запросы и подсказку из профиля</button>
              <span class="muted" id="autofillBrandStatus">ИИ найдёт официальный сайт и заполнит профиль: сфера, город, телефон, адрес, соцсети, синонимы. Пустые поля — заполнятся, введённое вручную не затрётся.</span>
            </div>
          </div>
          <div class="provider" id="queries" style="margin-top:18px">
            <div class="provider-head"><div><h3>Запросы для анализа</h3><small>Каждая строка запускается как отдельный поисковый запрос. Для точной фразы используйте кавычки.</small></div><span class="chip">{len(project.get('queries', []))} запросов</span></div>
            <div class="field">
              <label>Что искать <span class="help-dot" data-tip="Лучше дать 5-10 формулировок: точное название, сокращения, домен, бренд, имя руководителя, город или отраслевой контекст.">?</span></label>
              <textarea id="queriesInput" class="textarea" name="queries" placeholder='"Название компании"&#10;"ФИО" "должность"&#10;"бренд" "город"' style="min-height:300px">{esc(queries)}</textarea>
            </div>
            <div class="query-suggest-box">
              <button class="btn light" type="button" onclick="suggestProjectQueries()">Предложить запросы</button>
              <span class="muted">Система добавит точные фразы, новости, отзывы, официальный сайт и варианты написания.</span>
            </div>
            <div class="query-helper">
              <div class="insight"><b>Точная фраза</b><span class="muted">"Георгий Филимонов"</span></div>
              <div class="insight"><b>Контекст</b><span class="muted">"Филимонов" "губернатор Вологодской области"</span></div>
              <div class="insight"><b>Варианты</b><span class="muted">официальное название, сокращение, бренд, домен</span></div>
            </div>
          </div>
          <div class="provider" id="control-urls" style="margin-top:18px">
            <div class="provider-head"><div><h3>Контрольные страницы проекта</h3><small>Официальный сайт, карточки компаний, каталоги, отзовики и страницы, которые нужно проверять напрямую.</small></div><span class="chip">{len(project.get('control_urls', []))} URL</span></div>
            <div class="field">
              <label>URL страниц и каталогов <span class="help-dot" data-tip="Эти адреса не являются общими источниками платформы. Они проверяются только для этого проекта и помогают не потерять официальные карточки, каталоги и важные страницы.">?</span></label>
              <textarea class="textarea" name="control_urls" placeholder="https://example.ru/company&#10;https://catalog.example.ru/profile/123" style="min-height:160px">{esc(control_urls)}</textarea>
            </div>
            <p class="hint">Не добавляйте сюда поисковые системы и новостные сайты целиком. Для новостей используются Google, Яндекс, GDELT и RSS; здесь нужны только конкретные страницы проекта.</p>
          </div>
          <div class="provider" id="schedule" style="margin-top:18px">
            <div class="provider-head"><div><h3>Автоматический сбор</h3><small>Как часто платформа сама собирает упоминания по этому проекту.</small></div><span class="chip">{esc(last_collected_txt)}</span></div>
            <div class="field">
              <label class="check-control"><input type="checkbox" name="schedule_enabled" value="1" {"checked" if sched_enabled else ""}><span>Собирать автоматически в фоне</span></label>
            </div>
            <div class="field">
              <label>Частота сбора <span class="help-dot" data-tip="Не чаще раза в 3 часа. Чем реже — тем экономнее по лимитам; для большинства задач достаточно 6–24 часов.">?</span></label>
              <select class="select" name="schedule_interval_hours" style="width:260px;box-sizing:border-box">{schedule_options}</select>
            </div>
            <p class="hint">По умолчанию автосбор выключен. Срез можно в любой момент запустить вручную на дашборде.</p>
          </div>
          <div class="provider" id="tips" style="margin-top:18px">
            <div class="provider-head"><div><h3>Как писать запросы</h3><small>Хорошие запросы уменьшают шум и повышают качество среза.</small></div></div>
            <div class="meta"><span class="chip">"точная фраза"</span><span class="chip">персона + должность</span><span class="chip">бренд + регион</span><span class="chip">домен / ИНН</span></div>
            <p class="hint">Для общих слов обязательно добавляйте контекст. Например, не “Цифра”, а "Российская академия Цифра", "cifra.digital", юридическое название или город.</p>
          </div>
          <div class="bar" style="margin-top:18px">
            <button class="btn" type="submit">Сохранить проект</button>
            <a class="btn secondary" href="/?project={quote(selected_name)}">Перейти к срезу</a>
          </div>
        </form>
        <form method="post" action="/topics" style="margin-top:10px">
          <input type="hidden" name="action" value="delete">
          <input type="hidden" name="original_project_name" value="{esc(selected_name)}">
          <button class="btn light" type="submit">Удалить проект</button>
        </form>
      </div>
    </section>
  </main>
  <script>
  function cleanTerm(value) {{
    return (value || '').replace(/\\s+/g, ' ').trim();
  }}
  function normalizedProjectNames() {{
    const nameInput = document.getElementById('projectNameInput');
    const originalNameInput = document.querySelector('form[action="/topics"] input[name="original_project_name"]');
    return {{
      current: cleanTerm(nameInput ? nameInput.value : ''),
      original: cleanTerm(originalNameInput ? originalNameInput.value : '')
    }};
  }}
  function projectWasRenamed() {{
    const names = normalizedProjectNames();
    return !!(names.current && names.original && names.current.toLowerCase() !== names.original.toLowerCase());
  }}
  function fieldMatchesOriginal(field) {{
    if (!field) return true;
    return cleanTerm(field.value) === cleanTerm(field.dataset.originalValue || '');
  }}
  function inheritedValue(field) {{
    if (!field) return '';
    if (projectWasRenamed() && fieldMatchesOriginal(field)) return '';
    return cleanTerm(field.value);
  }}
  function clearInheritedBrandData() {{
    if (!projectWasRenamed()) return;
    [
      document.getElementById('brandWebsiteInput'),
      document.getElementById('brandCityInput'),
      document.getElementById('brandIndustryInput'),
      document.getElementById('brandAliasesInput'),
      document.getElementById('brandPhoneInput'),
      document.getElementById('brandAddressInput'),
      document.getElementById('brandSocialInput'),
      document.getElementById('relevanceHintInput')
    ].forEach(function(field) {{
      if (field && fieldMatchesOriginal(field)) field.value = '';
    }});
  }}
  function suggestProjectQueries() {{
    const nameInput = document.getElementById('projectNameInput');
    const queriesInput = document.getElementById('queriesInput');
    const name = cleanTerm(nameInput ? nameInput.value : '');
    if (!name || !queriesInput) return;
    const current = queriesInput.value.split(/\\n+/).map(cleanTerm).filter(Boolean);
    const words = name.split(' ').filter(function(word) {{ return word.length > 2; }});
    const shortName = words.slice(0, 2).join(' ');
    const variants = [
      '"' + name + '"',
      name,
      '"' + name + '" новости',
      '"' + name + '" отзывы',
      '"' + name + '" официальный сайт',
      '"' + name + '" руководство',
      '"' + name + '" регион',
      shortName && shortName !== name ? '"' + shortName + '"' : '',
      name.includes('ё') ? name.replace(/ё/g, 'е') : '',
      name.includes('е') ? name.replace(/е/g, 'ё') : ''
    ].filter(Boolean);
    variants.forEach(function(item) {{
      if (!current.includes(item)) current.push(item);
    }});
    queriesInput.value = current.join('\\n');
    queriesInput.focus();
  }}
  async function autofillBrandProfile() {{
    const button = document.getElementById('autofillBrandButton');
    const status = document.getElementById('autofillBrandStatus');
    const nameInput = document.getElementById('projectNameInput');
    const websiteInput = document.getElementById('brandWebsiteInput');
    const aliasesInput = document.getElementById('brandAliasesInput');
    const cityInput = document.getElementById('brandCityInput');
    const industryInput = document.getElementById('brandIndustryInput');
    const hintInput = document.getElementById('relevanceHintInput');
    const queriesInput = document.getElementById('queriesInput');
    const name = cleanTerm(nameInput ? nameInput.value : '');
    const city = cleanTerm(cityInput ? cityInput.value : '');
    const industry = cleanTerm(industryInput ? industryInput.value : '');
    if (!name) {{
      if (status) status.textContent = 'Сначала укажите название проекта.';
      return;
    }}
    if (button) {{
      button.disabled = true;
      button.textContent = 'Ищу...';
    }}
    if (status) status.textContent = 'Проверяю поисковые источники и подбираю вероятный официальный сайт...';
    try {{
      const response = await fetch('/api/project-autofill?name=' + encodeURIComponent(name) + '&city=' + encodeURIComponent(city) + '&industry=' + encodeURIComponent(industry), {{
        headers: {{'Accept':'application/json'}},
        cache: 'no-store'
      }});
      const data = await response.json();
      if (!response.ok || !data.ok) {{
        if (status) status.textContent = data.error || 'Не удалось подобрать сайт.';
        return;
      }}
      if (websiteInput && !cleanTerm(websiteInput.value)) websiteInput.value = cleanTerm(data.website || '');
      if (aliasesInput && Array.isArray(data.aliases) && data.aliases.length) {{
        const currentAliases = aliasesInput.value.split(',').map(cleanTerm).filter(Boolean);
        data.aliases.forEach(function(alias) {{
          if (alias && !currentAliases.includes(alias)) currentAliases.push(alias);
        }});
        aliasesInput.value = currentAliases.join(', ');
      }}
      // Заполняем пустые поля профиля данными, извлечёнными ИИ (не затираем введённое вручную)
      const fillIfEmpty = function(input, value) {{
        if (input && !cleanTerm(input.value) && cleanTerm(value || '')) input.value = cleanTerm(value);
      }};
      fillIfEmpty(cityInput, data.city);
      fillIfEmpty(industryInput, data.industry);
      fillIfEmpty(document.getElementById('brandPhoneInput'), data.phone);
      fillIfEmpty(document.getElementById('brandAddressInput'), data.address);
      const socialInput = document.getElementById('brandSocialInput');
      if (socialInput && Array.isArray(data.social_links) && data.social_links.length) {{
        const currentLinks = socialInput.value.split(/\\n+/).map(cleanTerm).filter(Boolean);
        data.social_links.forEach(function(link) {{
          if (link && !currentLinks.includes(link)) currentLinks.push(link);
        }});
        socialInput.value = currentLinks.join('\\n');
      }}
      if (queriesInput && Array.isArray(data.queries)) {{
        const currentQueries = queriesInput.value.split(/\\n+/).map(cleanTerm).filter(Boolean);
        data.queries.forEach(function(query) {{
          if (query && !currentQueries.includes(query)) currentQueries.push(query);
        }});
        queriesInput.value = currentQueries.join('\\n');
      }}
      if (hintInput && !cleanTerm(hintInput.value) && cleanTerm(data.relevance_hint || '')) {{
        hintInput.value = data.relevance_hint;
      }}
      if (status) {{
        const siteText = data.website ? ('сайт: ' + data.website) : 'сайт не найден';
        const enriched = data.ai_enriched ? ', профиль дополнен ИИ' : '';
        status.textContent = 'Готово: ' + siteText + enriched + '. Проверьте поля и при необходимости поправьте.';
      }}
    }} catch (error) {{
      if (status) status.textContent = 'Не удалось получить подсказку. Попробуйте ещё раз.';
    }} finally {{
      if (button) {{
        button.disabled = false;
        button.textContent = 'Заполнить профиль из интернета';
      }}
    }}
  }}
  function suggestFromBrandProfile() {{
    const nameInput = document.getElementById('projectNameInput');
    const queriesInput = document.getElementById('queriesInput');
    const cityInput = document.getElementById('brandCityInput');
    const websiteInput = document.getElementById('brandWebsiteInput');
    const phoneInput = document.getElementById('brandPhoneInput');
    const aliasesInput = document.getElementById('brandAliasesInput');
    const industryInput = document.getElementById('brandIndustryInput');
    const hintInput = document.getElementById('relevanceHintInput');
    if (!queriesInput) return;

    const name = cleanTerm(nameInput ? nameInput.value : '');
    clearInheritedBrandData();

    const city = inheritedValue(cityInput);
    const industry = inheritedValue(industryInput);
    const website = inheritedValue(websiteInput)
      .replace(/^https?:\\/\\//i, '').replace(/^www\\./i, '').replace(/\\/.*$/, '');
    const phones = inheritedValue(phoneInput).split(',').map(cleanTerm).filter(Boolean);
    const aliases = inheritedValue(aliasesInput).split(',').map(cleanTerm).filter(Boolean);

    const current = queriesInput.value.split(/\\n+/).map(cleanTerm).filter(Boolean);
    const variants = [];
    [name].concat(aliases).filter(Boolean).forEach(function(term) {{
      if (city) variants.push('"' + term + '" "' + city + '"');
    }});
    if (website) variants.push(website);
    phones.forEach(function(p) {{ if (p) variants.push(p); }});
    variants.forEach(function(item) {{
      if (item && !current.includes(item)) current.push(item);
    }});
    queriesInput.value = current.join('\\n');

    const currentHint = cleanTerm(hintInput ? hintInput.value : '');
    const names = normalizedProjectNames();
    const shouldRefreshHint = !currentHint || (
      names.original &&
      name &&
      names.original.toLowerCase() !== name.toLowerCase() &&
      currentHint.toLowerCase().includes(names.original.toLowerCase())
    );

    if (hintInput && shouldRefreshHint && name) {{
      let hint = '«' + name + '»';
      if (industry) hint += ' — ' + industry;
      if (city) hint += (industry ? ', ' : ' — ') + city;
      hint += '. Релевантны только публикации именно об этом бренде.';
      hint += ' Если слово «' + name + '» используется в тексте в другом, обычном значении, а не как название этого бренда — публикация НЕ релевантна' + (city ? ', даже если рядом упоминается ' + city : '') + '.';
      hintInput.value = hint;
    }}
    queriesInput.focus();
  }}
  (function bindProjectRenameReset() {{
    const nameInput = document.getElementById('projectNameInput');
    if (!nameInput) return;
    nameInput.addEventListener('change', clearInheritedBrandData);
    nameInput.addEventListener('blur', clearInheritedBrandData);
  }})();
  (function bindProjectAutofill() {{
    const nameInput = document.getElementById('projectNameInput');
    const websiteInput = document.getElementById('brandWebsiteInput');
    if (!nameInput || !websiteInput) return;
    let attemptedName = '';
    nameInput.addEventListener('blur', function() {{
      const currentName = cleanTerm(nameInput.value);
      if (!currentName || cleanTerm(websiteInput.value) || attemptedName === currentName) return;
      attemptedName = currentName;
      autofillBrandProfile();
    }});
  }})();
  </script>
</body>
</html>"""


def render_settings(config_path: str, message: str = "", user: dict | None = None) -> str:
    config = load_config(config_path)
    secrets = load_secrets(config)
    rss_feeds = get_rss_sources(config)
    rss_feed_list = "\n".join(f"{source.get('name', 'RSS')} — {source.get('url', '')}" for source in rss_feeds)
    webhooks = "\n".join(config.get("webhooks", []))
    vk_app_id = os.getenv("VK_APP_ID") or secrets.get("VK_APP_ID", "")
    vk_client_secret = secret_value(config, "VK_CLIENT_SECRET")
    vk_service_token = secret_value(config, "VK_SERVICE_TOKEN")
    vk_access_token = secret_value(config, "VK_ACCESS_TOKEN")
    vk_refresh_enabled = bool(secrets.get("VK_REFRESH_TOKEN"))
    vk_auth_url = ""
    if vk_app_id:
        # VK implicit flow: the user copies access_token from the address bar.
        vk_auth_url = "https://oauth.vk.com/authorize?" + urlencode({
            "client_id": vk_app_id,
            "display": "page",
            "redirect_uri": "https://oauth.vk.com/blank.html",
            "response_type": "token",
            "revoke": "1",
            "v": "5.199",
        })

    def status(secret_name: str) -> str:
        ok = bool(secret_value(config, secret_name))
        return f"<span class='status {'on' if ok else 'off'}'>{'подключено' if ok else 'не задано'}</span>"

    if vk_service_token:
        vk_mode_badge = "<span class='status on'>постоянный режим</span>"
        vk_mode_hint = "Сейчас VK подключён правильно: серверный ключ сохранён, ручное продление не требуется."
    elif vk_refresh_enabled:
        vk_mode_badge = "<span class='status off'>временный режим</span>"
        vk_mode_hint = "Сейчас работает временный режим через VK ID. Сбор идёт, но надёжнее сохранить VK_SERVICE_TOKEN и уйти от продления токена."
    elif vk_access_token:
        vk_mode_badge = "<span class='status off'>временный режим</span>"
        vk_mode_hint = "Сейчас сохранён только пользовательский access token. Он может истечь, поэтому для стабильного сервера лучше добавить VK_SERVICE_TOKEN."
    else:
        vk_mode_badge = "<span class='status off'>не настроено</span>"
        vk_mode_hint = "VK ещё не подключён: добавьте постоянный VK_SERVICE_TOKEN или временно вставьте VK_ACCESS_TOKEN."

    google_enabled = source_enabled(config, "google_custom_search")
    serper_enabled = source_enabled(config, "serper_google")
    yandex_enabled = source_enabled(config, "yandex_search")
    gdelt_enabled = source_enabled(config, "gdelt_news")
    newsdata_enabled = source_enabled(config, "newsdata")
    ai_settings = ollama_config(config)
    ai_status = ollama_status(config) if ai_settings["enabled"] else {
        "ok": False,
        "model_ready": False,
        "message": "Локальная ИИ выключена",
        "models": [],
    }
    cl_settings = claude_config(config)
    cl_status = claude_status(config) if cl_settings["enabled"] else {
        "ok": False,
        "has_key": bool(secret_value(config, "ANTHROPIC_API_KEY")),
        "message": "Claude API выключен",
    }
    yg_settings = yandex_gpt_config(config)
    yg_status = yandex_gpt_status(config) if yg_settings["enabled"] else {
        "ok": False,
        "has_key": bool(secret_value(config, "YANDEX_GPT_API_KEY")),
        "message": "YandexGPT выключен",
    }
    smtp_info = smtp_status(config)
    smtp_cfg = smtp_info["settings"]
    nav = nav_html("settings", user)

    # ── Сводка для верхней панели обзора ─────────────────────────────────────
    _overview_source_types = [
        "google_news", "gdelt_news", "newsdata", "web_pages",
        "google_custom_search", "serper_google", "yandex_search",
        "vk_search", "ok_search",
    ]
    active_sources = sum(1 for t in _overview_source_types if source_enabled(config, t))
    active_sources += len(rss_feeds)
    search_api_keys = sum(
        1 for k in ["GOOGLE_SEARCH_API_KEY", "YANDEX_SEARCH_API_KEY", "SERPER_API_KEY", "NEWSDATA_API_KEY"]
        if secret_value(config, k)
    )
    if cl_settings["enabled"]:
        ai_overview_value, ai_overview_sub = "Claude API", "облачный анализ"
    elif yg_settings["enabled"]:
        ai_overview_value, ai_overview_sub = "YandexGPT", "облачный анализ (РФ)"
    elif ai_settings["enabled"]:
        ai_overview_value, ai_overview_sub = "Ollama", "локальный анализ"
    else:
        ai_overview_value, ai_overview_sub = "Выключен", "анализ недоступен"
    _social_active = [s for s in [
        "VK" if source_enabled(config, "vk_search") else "",
        "OK" if source_enabled(config, "ok_search") else "",
    ] if s]
    social_overview_value = " · ".join(_social_active) if _social_active else "выключены"

    # ── Состояние автоматического сбора (расписание) ─────────────────────────
    schedule_cfg = config.get("schedule", {})
    schedule_enabled = schedule_cfg.get("enabled", True)
    _interval_presets = [
        (15, "каждые 15 минут"), (30, "каждые 30 минут"), (60, "каждый час"),
        (120, "каждые 2 часа"), (180, "каждые 3 часа"), (360, "каждые 6 часов"),
    ]
    schedule_interval = int(schedule_cfg.get("interval_minutes") or 30)
    if schedule_interval not in dict(_interval_presets):
        schedule_interval = 30
    schedule_options = "".join(
        f'<option value="{m}" {"selected" if m == schedule_interval else ""}>{esc(label)}</option>'
        for m, label in _interval_presets
    )
    schedule_overview_value = dict(_interval_presets)[schedule_interval] if schedule_enabled else "выключен"

    overview_html = f"""
    <section class="settings-overview">
      <div class="tile accent">
        <span class="tile-label">Источники</span>
        <span class="tile-value">{active_sources}</span>
        <span class="tile-sub">активных в сборе</span>
      </div>
      <div class="tile {'accent' if search_api_keys else 'warn'}">
        <span class="tile-label">Поисковые API</span>
        <span class="tile-value">{search_api_keys} из 4</span>
        <span class="tile-sub">{'с ключом доступа' if search_api_keys else 'ни одного ключа'}</span>
      </div>
      <div class="tile">
        <span class="tile-label">ИИ-аналитик</span>
        <span class="tile-value">{esc(ai_overview_value)}</span>
        <span class="tile-sub">{esc(ai_overview_sub)}</span>
      </div>
      <div class="tile">
        <span class="tile-label">Соцсети</span>
        <span class="tile-value">{esc(social_overview_value)}</span>
        <span class="tile-sub">публичные публикации</span>
      </div>
      <div class="tile {'accent' if schedule_enabled else 'warn'}">
        <span class="tile-label">Автосбор</span>
        <span class="tile-value">{esc(schedule_overview_value)}</span>
        <span class="tile-sub">{'фоновый сбор активен' if schedule_enabled else 'сбор на паузе'}</span>
      </div>
    </section>"""

    return f"""<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Настройки мониторинга</title>
  <link rel="icon" type="image/svg+xml" href="/icon.svg">
  <link rel="apple-touch-icon" href="/icon.svg">
  <link rel="manifest" href="/manifest.json">
  <meta name="theme-color" content="#147487">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-title" content="PR Monitor">
  <style>{STYLE}</style>{i18n_assets()}
</head>
<body>
  <header class="top">
    <h1>Источники и интеграции</h1>
    <p>Здесь подключается то, откуда система собирает данные: API, RSS, каталоги, вебхуки и расписание.</p>
    {nav}
  </header>
  <main class="wrap">
    {f'<div class="card" style="margin-bottom:18px"><b>{esc(message)}</b></div>' if message else ''}
    <div class="pagehead">
      <div><h2>Где ищем и куда отправляем события</h2><p>Тема поиска вынесена отдельно в раздел “Темы”, чтобы токены и вебхуки не смешивались с объектом мониторинга.</p></div>
      <a class="btn light" href="/topics">Открыть темы</a>
    </div>
    {overview_html}
    <form method="post" action="/settings">
      <section class="split">
        <aside class="card side-nav">
          <a href="#sources">Базовые источники</a>
          <a href="#search">Поисковые API</a>
          <a href="#ai">ИИ-аналитик</a>
          <a href="#social">Соцсети и видео</a>
          <a href="#mail">Письма и доступ</a>
          <a href="#webhooks">Вебхуки</a>
          <a href="#schedule">Расписание</a>
        </aside>
        <div>
          <h3 class="section-title" id="sources">Базовые источники</h3>
          <div class="settings">
            <div class="provider">
              <div class="provider-head"><div><h3>Google News RSS</h3><small>Быстрый бесплатный источник новостных упоминаний.</small></div><span class="status {'on' if source_enabled(config, 'google_news') else 'off'}">{'включено' if source_enabled(config, 'google_news') else 'выключено'}</span></div>
              <div class="meta"><span class="chip">новости</span><span class="chip">без токена</span><span class="chip">RSS</span></div>
              <label><input type="checkbox" name="enable_google_news" {'checked' if source_enabled(config, 'google_news') else ''}> Использовать в сборе</label>
            </div>
            <div class="provider">
              <div class="provider-head"><div><h3>GDELT News Index</h3><small>Широкий новостной индекс без API-ключа для дополнительного охвата.</small></div><span class="status {'on' if gdelt_enabled else 'off'}">{'включено' if gdelt_enabled else 'выключено'}</span></div>
              <div class="meta"><span class="chip">агрегатор</span><span class="chip">новости</span><span class="chip">без токена</span><span class="chip">до 90 дней</span></div>
              <label><input type="checkbox" name="enable_gdelt" {'checked' if gdelt_enabled else ''}> Использовать в срезе новостей РФ</label>
            </div>
            <div class="provider">
              <div class="provider-head"><div><h3>Новостные СМИ</h3><small>Федеральные, деловые, IT и региональные RSS-ленты. Работают без токенов.</small></div><span class="status {'on' if bool(rss_feeds) else 'off'}">{len(rss_feeds)} лент</span></div>
              <div class="meta"><span class="chip">СМИ</span><span class="chip">RSS</span><span class="chip">регионы</span><span class="chip">без токена</span></div>
              <p class="hint">Этот слой включен постоянно: программа берет свежие публикации из лент и оставляет только те, где есть фразы из темы мониторинга.</p>
              <textarea class="textarea" readonly style="min-height:140px">{esc(rss_feed_list)}</textarea>
            </div>
            <div class="provider">
              <div class="provider-head"><div><h3>Контрольные страницы проектов</h3><small>Официальные сайты, карточки организаций, каталоги и отзовики теперь задаются внутри конкретного проекта.</small></div><span class="status {'on' if source_enabled(config, 'web_pages') else 'off'}">{'включено' if source_enabled(config, 'web_pages') else 'выключено'}</span></div>
              <div class="meta"><span class="chip">проектные URL</span><span class="chip">каталоги</span><span class="chip">ручная проверка</span></div>
              <label><input type="checkbox" name="enable_web_pages" {'checked' if source_enabled(config, 'web_pages') else ''}> Использовать в сборе</label>
              <p class="hint">Сами URL больше не хранятся в общих настройках, чтобы чужие страницы не попадали во все темы. Откройте “Проекты” и заполните блок “Контрольные страницы проекта”.</p>
              <a class="btn light" href="/topics#control-urls">Открыть проекты</a>
            </div>
          </div>

          <h3 class="section-title" id="search" style="margin-top:24px">Поисковые API</h3>
          <div class="settings">
            <div class="provider">
              <div class="provider-head"><div><h3>Google Programmable Search</h3><small>Обычный Google-поиск по сайтам, а не только новости.</small></div><span class="status {'on' if google_enabled else 'off'}">{'включено' if google_enabled else 'выключено'}</span></div>
              <div class="meta"><span class="chip">Google</span><span class="chip">API key</span><span class="chip">CX</span></div>
              <p>{status('GOOGLE_SEARCH_API_KEY')} API key · {status('GOOGLE_SEARCH_CX')} Search CX</p>
              <label><input type="checkbox" name="enable_google_custom" {'checked' if google_enabled else ''}> Использовать в сборе</label>
              <div class="field"><label>GOOGLE_SEARCH_API_KEY</label><input class="input" name="GOOGLE_SEARCH_API_KEY" type="password" placeholder="оставьте пустым, чтобы не менять" style="width:100%;box-sizing:border-box"></div>
              <div class="field"><label>GOOGLE_SEARCH_CX</label><input class="input" name="GOOGLE_SEARCH_CX" type="text" value="{esc(secret_value(config, 'GOOGLE_SEARCH_CX'))}" placeholder="ID Programmable Search Engine" style="width:100%;box-sizing:border-box"></div>
              <p class="hint">Нужны API key из Google Cloud и Search engine ID/CX из Programmable Search Engine. Важно: Google закрыл Custom Search JSON API для новых клиентов; если проект возвращает 403 “does not have access”, нужен старый проект с доступом или другой поисковый провайдер.</p>
              <div class="bar" style="margin:10px 0 0">
                <a class="btn light" href="https://console.cloud.google.com/apis/library/customsearch.googleapis.com" target="_blank" rel="noopener">Включить API</a>
                <a class="btn light" href="https://programmablesearchengine.google.com/controlpanel/all" target="_blank" rel="noopener">Создать CX</a>
                <a class="btn light" href="/google-test">Проверить Google</a>
              </div>
            </div>
            <div class="provider">
              <div class="provider-head"><div><h3>Яндекс Search API</h3><small>Официальный поиск по базе Яндекса через Yandex Cloud AI Studio.</small></div><span class="status {'on' if yandex_enabled else 'off'}">{'включено' if yandex_enabled else 'выключено'}</span></div>
              <div class="meta"><span class="chip">Яндекс</span><span class="chip">API key</span><span class="chip">folder id</span><span class="chip">web search</span></div>
              <p>{status('YANDEX_SEARCH_API_KEY')} API key · {status('YANDEX_FOLDER_ID')} folder id</p>
              <label><input type="checkbox" name="enable_yandex" {'checked' if yandex_enabled else ''}> Использовать в сборе</label>
              <div class="field"><label>YANDEX_SEARCH_API_KEY</label><input class="input" name="YANDEX_SEARCH_API_KEY" type="password" placeholder="оставьте пустым, чтобы не менять" style="width:100%;box-sizing:border-box"></div>
              <div class="field"><label>YANDEX_FOLDER_ID</label><input class="input" name="YANDEX_FOLDER_ID" type="text" value="{esc(secret_value(config, 'YANDEX_FOLDER_ID'))}" placeholder="ID каталога, не ID API-ключа" style="width:100%;box-sizing:border-box"></div>
              <p class="hint">Нужен секретный API key и ID каталога/folder. На странице API-ключа строка “Идентификатор” у ключа не подходит; это ID самого ключа. Folder id находится в обзоре каталога “default”.</p>
              <div class="bar" style="margin:10px 0 0">
                <a class="btn light" href="https://aistudio.yandex.cloud/" target="_blank" rel="noopener">Открыть AI Studio</a>
                <a class="btn light" href="/yandex-test">Проверить Яндекс</a>
              </div>
            </div>
            <div class="provider">
              <div class="provider-head"><div><h3>Google через Serper</h3><small>Google-выдача через внешний SERP API, когда Custom Search JSON API недоступен.</small></div><span class="status {'on' if serper_enabled else 'off'}">{'включено' if serper_enabled else 'выключено'}</span></div>
              <div class="meta"><span class="chip">Google</span><span class="chip">Serper</span><span class="chip">SERP API</span></div>
              <p>{status('SERPER_API_KEY')} SERPER_API_KEY</p>
              <label><input type="checkbox" name="enable_serper" {'checked' if serper_enabled else ''}> Использовать в сборе</label>
              <div class="field"><label>SERPER_API_KEY</label><input class="input" name="SERPER_API_KEY" type="password" placeholder="оставьте пустым, чтобы не менять" style="width:100%;box-sizing:border-box"></div>
              <p class="hint">Это рабочая замена Google Custom Search: Serper возвращает обычную Google-выдачу по API и снимает с нас капчи/парсинг.</p>
              <div class="bar" style="margin:10px 0 0">
                <a class="btn light" href="https://serper.dev/api-keys" target="_blank" rel="noopener">Открыть ключи Serper</a>
                <a class="btn light" href="/serper-test">Проверить Serper</a>
              </div>
            </div>
            <div class="provider">
              <div class="provider-head"><div><h3>NewsData.io</h3><small>Коммерческий news API для расширения охвата по стране, языку и источникам.</small></div><span class="status {'on' if newsdata_enabled else 'off'}">{'включено' if newsdata_enabled else 'выключено'}</span></div>
              <div class="meta"><span class="chip">агрегатор</span><span class="chip">API key</span><span class="chip">country=ru</span><span class="chip">language=ru</span></div>
              <p>{status('NEWSDATA_API_KEY')} NEWSDATA_API_KEY</p>
              <label><input type="checkbox" name="enable_newsdata" {'checked' if newsdata_enabled else ''}> Использовать в срезе новостей РФ</label>
              <div class="field"><label>NEWSDATA_API_KEY</label><input class="input" name="NEWSDATA_API_KEY" type="password" placeholder="оставьте пустым, чтобы не менять" style="width:100%;box-sizing:border-box"></div>
              <p class="hint">Без ключа источник остается выключенным. С ключом он добавит еще один независимый новостной индекс поверх Яндекса, Google и GDELT.</p>
              <div class="bar" style="margin:10px 0 0">
                <a class="btn light" href="https://newsdata.io/register" target="_blank" rel="noopener">Получить ключ</a>
              </div>
            </div>
          </div>

          <h3 class="section-title" id="ai" style="margin-top:24px">ИИ-аналитик</h3>
          <div class="settings">
            <div class="provider">
              <div class="provider-head"><div><h3>Claude API (Anthropic)</h3><small>Облачная нейросеть Claude — наиболее точные резюме и анализ. Приоритет над Ollama.</small></div><span class="status {'on' if cl_settings['enabled'] else 'off'}">{'включено' if cl_settings['enabled'] else 'выключено'}</span></div>
              <div class="meta"><span class="chip">облако</span><span class="chip">API-ключ</span><span class="chip">платно</span></div>
              <p class="hint">Данные выборки отправляются в API Anthropic. Ключ хранится только локально в <code>data/secrets.json</code> и никуда не передаётся. Если Claude включён, Ollama не используется.</p>
              <label><input type="checkbox" name="enable_claude" {'checked' if cl_settings['enabled'] else ''}> Использовать Claude API для ИИ-анализа</label>
              <div class="field" style="margin-top:14px">
                <label>ANTHROPIC_API_KEY</label>
                <input class="input" name="ANTHROPIC_API_KEY" type="password" placeholder="sk-ant-... (оставьте пустым, чтобы не менять)" style="width:100%;box-sizing:border-box">
                {'<span class="status on" style="display:inline-block;margin-top:6px">ключ сохранён</span>' if cl_status.get('has_key') else '<span class="status off" style="display:inline-block;margin-top:6px">ключ не задан</span>'}
              </div>
              <div class="field">
                <label>Модель</label>
                <select class="select" name="claude_model" style="width:100%;box-sizing:border-box">
                  {''.join(f'<option value="{m}" {"selected" if m == cl_settings["model"] else ""}>{m}</option>' for m in CLAUDE_MODELS)}
                </select>
              </div>
              <div class="field"><label>Максимум токенов в ответе</label><input class="input" name="claude_max_tokens" type="number" min="256" max="4096" value="{esc(str(cl_settings['max_tokens']))}" style="width:160px;box-sizing:border-box"></div>
              <div class="coverage-note">{esc(cl_status['message'])}</div>
              <div class="bar" style="margin:10px 0 0">
                <a class="btn light" href="/claude-test">Проверить Claude API</a>
                <a class="btn light" href="https://console.anthropic.com/settings/keys" target="_blank" rel="noopener">Получить ключ</a>
              </div>
            </div>
            <div class="provider">
              <div class="provider-head"><div><h3>YandexGPT (Yandex Cloud)</h3><small>Облачная нейросеть Яндекса — работает напрямую из России, без блокировок. Используется, если Claude выключен.</small></div><span class="status {'on' if yg_settings['enabled'] else 'off'}">{'включено' if yg_settings['enabled'] else 'выключено'}</span></div>
              <div class="meta"><span class="chip">облако</span><span class="chip">доступно из РФ</span><span class="chip">платно</span></div>
              <p class="hint">Данные выборки отправляются в Yandex Cloud Foundation Models. Ключ и Folder ID хранятся только локально в <code>data/secrets.json</code>. Если Claude включён, YandexGPT не используется.</p>
              <label><input type="checkbox" name="enable_yandex_gpt" {'checked' if yg_settings['enabled'] else ''}> Использовать YandexGPT для ИИ-анализа</label>
              <div class="field" style="margin-top:14px">
                <label>YANDEX_GPT_API_KEY</label>
                <input class="input" name="YANDEX_GPT_API_KEY" type="password" placeholder="AQVN... (оставьте пустым, чтобы не менять)" style="width:100%;box-sizing:border-box">
                {'<span class="status on" style="display:inline-block;margin-top:6px">ключ сохранён</span>' if yg_status.get('has_key') else '<span class="status off" style="display:inline-block;margin-top:6px">ключ не задан</span>'}
              </div>
              <div class="field">
                <label>Модель</label>
                <select class="select" name="yandex_gpt_model" style="width:100%;box-sizing:border-box">
                  {''.join(f'<option value="{m}" {"selected" if m == yg_settings["model"] else ""}>{m}</option>' for m in YANDEX_GPT_MODELS)}
                </select>
              </div>
              <div class="field"><label>Максимум токенов в ответе</label><input class="input" name="yandex_gpt_max_tokens" type="number" min="256" max="4096" value="{esc(str(yg_settings['max_tokens']))}" style="width:160px;box-sizing:border-box"></div>
              <div class="coverage-note">{esc(yg_status['message'])}</div>
              <div class="bar" style="margin:10px 0 0">
                <a class="btn light" href="/yandex-gpt-test">Проверить YandexGPT</a>
                <a class="btn light" href="https://yandex.cloud/ru/services/ai-studio" target="_blank" rel="noopener">Получить ключ</a>
              </div>
            </div>
            <div class="provider">
              <div class="provider-head"><div><h3>Ollama</h3><small>Бесплатная локальная модель для резюме, выводов и рекомендаций по выборке.</small></div><span class="status {'on' if ai_settings['enabled'] else 'off'}">{'включено' if ai_settings['enabled'] else 'выключено'}</span></div>
              <div class="meta"><span class="chip">локально</span><span class="chip">без токена</span><span class="chip">данные не уходят наружу</span></div>
              <p class="hint">Ollama должна быть запущена на этом компьютере или сервере. Приложение обращается к локальному API только после ручного запуска на странице “ИИ-анализ”.</p>
              <label><input type="checkbox" name="enable_ollama" {'checked' if ai_settings['enabled'] else ''}> Использовать Ollama для ИИ-анализа</label>
              <div class="field" style="margin-top:14px"><label>Адрес Ollama</label><input class="input" name="ollama_base_url" type="text" value="{esc(ai_settings['base_url'])}" placeholder="{DEFAULT_BASE_URL}" style="width:100%;box-sizing:border-box"></div>
              <div class="field"><label>Модель</label><input class="input" name="ollama_model" type="text" value="{esc(ai_settings['model'])}" placeholder="{DEFAULT_MODEL}" style="width:100%;box-sizing:border-box"></div>
              <div class="field"><label>Таймаут ответа, секунд</label><input class="input" name="ollama_timeout" type="number" min="5" max="180" value="{esc(ai_settings['timeout'])}" style="width:160px;box-sizing:border-box"></div>
              <div class="coverage-note">{esc(ai_status['message'])}{f' · моделей найдено: {len(ai_status.get("models", []))}' if ai_status.get('models') else ''}</div>
              <div class="bar" style="margin:10px 0 0">
                <a class="btn light" href="/ollama-test">Проверить Ollama</a>
                <a class="btn light" href="https://ollama.com/download" target="_blank" rel="noopener">Скачать Ollama</a>
              </div>
            </div>
            <div class="provider">
              <div class="provider-head"><div><h3>Как запустить бесплатно</h3><small>Минимальный путь для локального ИИ без внешних API.</small></div><span class="status on">инструкция</span></div>
              <p class="hint">1. Установите Ollama. 2. Выполните команду загрузки модели. 3. Включите Ollama здесь и сохраните настройки. 4. Откройте “ИИ-анализ”.</p>
              <pre class="card" style="overflow:auto;margin:0;background:#f6f9fb">ollama pull qwen2.5:1.5b
ollama serve</pre>
              <p class="hint">Если компьютер слабый, можно попробовать более легкую модель. Если сервер мощнее, можно выбрать модель крупнее.</p>
            </div>
          </div>

          <h3 class="section-title" id="social" style="margin-top:24px">Соцсети и видео</h3>
          <div class="settings">
            <div class="provider">
              <div class="provider-head"><div><h3>VK public posts</h3><small>Поиск публичных постов через VK API — основной соцсетевой источник.</small></div><span class="status {'on' if source_enabled(config, 'vk_search') else 'off'}">{'включено' if source_enabled(config, 'vk_search') else 'выключено'}</span></div>
              <div class="meta"><span class="chip">VK</span><span class="chip">service token</span><span class="chip">newsfeed.search</span></div>
              <p>{status('VK_APP_ID')} VK app id · {status('VK_SERVICE_TOKEN')} постоянный сервисный ключ · {status('VK_ACCESS_TOKEN')} пользовательский токен</p>
              <p>{vk_mode_badge}</p>
              <p class="hint">{vk_mode_hint}</p>
              <label><input type="checkbox" name="enable_vk" {'checked' if source_enabled(config, 'vk_search') else ''}> Использовать в сборе</label>
              <div class="field"><label>VK_APP_ID</label><input class="input" name="VK_APP_ID" type="text" value="{esc(vk_app_id)}" placeholder="ID приложения VK"></div>
              <div class="field"><label>VK_CLIENT_SECRET <span class="hint" style="font-weight:400">(Защищённый ключ из настроек приложения VK)</span></label><div class="secret-field"><input class="input" name="VK_CLIENT_SECRET" type="password" placeholder="оставьте пустым, чтобы не менять"><button type="button" class="reveal-btn" aria-label="Показать значение">👁</button></div>{'<span class="status on" style="display:inline-block;margin-top:4px">сохранён</span>' if vk_client_secret else '<span class="status off" style="display:inline-block;margin-top:4px">не задан</span>'}</div>
              <div class="field"><label>VK_SERVICE_TOKEN <span class="hint" style="font-weight:400">(Сервисный ключ из раздела «Ключи доступа»)</span></label><div class="secret-field"><input class="input" name="VK_SERVICE_TOKEN" type="password" placeholder="вставьте постоянный сервисный ключ"><button type="button" class="reveal-btn" aria-label="Показать значение">👁</button></div>{'<span class="status on" style="display:inline-block;margin-top:4px">сохранён</span>' if vk_service_token else '<span class="status off" style="display:inline-block;margin-top:4px">не задан</span>'}</div>
              <div class="field"><label>VK_ACCESS_TOKEN</label><div class="secret-field"><input class="input" name="VK_ACCESS_TOKEN" type="password" placeholder="вставьте access_token из адресной строки"><button type="button" class="reveal-btn" aria-label="Показать значение">👁</button></div></div>
              <div class="bar" style="margin:10px 0 0">
                <a class="btn light" href="https://dev.vk.com/ru/admin/apps-list" target="_blank" rel="noopener">Настройки приложения VK</a>
                {f'<a class="btn" href="{esc(vk_auth_url)}" target="_blank" rel="noopener">Получить токен на 24 часа</a>' if vk_auth_url else '<span class="muted">Сначала сохраните VK_APP_ID</span>'}
                <a class="btn light" href="/vk-test">Проверить VK</a>
              </div>
              <details class="hint-details">
                <summary>Как получить ключи VK</summary>
                <p class="hint"><b>Рекомендуемый вариант</b> для онлайн-сервера: в кабинете VK откройте «Разработка → Ключи доступа», нажмите «Показать» напротив <b>сервисного ключа</b> и сохраните его здесь. Он не требует ежедневного обновления. Защищённый и сервисный ключи — разные значения.</p>
                <p class="hint"><b>Запасной вариант</b>: получите пользовательский токен, скопируйте значение после <b>access_token=</b> до символа <b>&amp;</b> и сохраните в VK_ACCESS_TOKEN. Такой токен ограничен по времени и может быть привязан к IP.</p>
                <p class="hint">VK ID выдаёт access token на 1 час и refresh token на 180 дней, но для серверного поиска проще и надёжнее постоянный сервисный ключ — он официально поддерживается методом newsfeed.search.</p>
              </details>
            </div>
            <div class="provider">
              <div class="provider-head"><div><h3>Одноклассники (OK.ru)</h3><small>Открытые страницы и публикации OK через поисковые индексы. Аудитория 35+, сильна в регионах.</small></div><span class="status {'on' if source_enabled(config, 'ok_search') else 'off'}">{'включено' if source_enabled(config, 'ok_search') else 'выключено'}</span></div>
              <div class="meta"><span class="chip">OK.ru</span><span class="chip">публичные страницы</span><span class="chip">site:ok.ru</span></div>
              <p><span class="status on">приложение 512004968849</span> · использует Serper, Google или Яндекс из раздела «Поисковые API»</p>
              <label><input type="checkbox" name="enable_ok" {'checked' if source_enabled(config, 'ok_search') else ''}> Использовать в сборе</label>
              <details class="hint-details">
                <summary>Подробнее об OK.ru</summary>
                <p class="hint">У единого приложения VK/OK общий набор ключей, однако сервисный ключ VK не авторизует старый OK REST API, а глобальный метод stream.search больше недоступен. Поэтому система ищет индексируемые публикации запросом <b>site:ok.ru</b> — отдельный ключ OK не требуется.</p>
                <p class="hint">Ограничение: публикации и ссылки будут собраны, но реакции и комментарии доступны только когда открытая страница отдаёт их без авторизации.</p>
              </details>
            </div>
            <div class="provider">
              <div class="provider-head"><div><h3>Telegram и YouTube</h3><small>Для Telegram нужен список каналов или сторонний поиск; для YouTube нужен API key.</small></div><span class="status off">ожидает подключения</span></div>
              <div class="meta"><span class="chip">Telegram</span><span class="chip">YouTube</span><span class="chip">ключи/каналы</span></div>
              <div class="field"><label>TELEGRAM_BOT_TOKEN</label><div class="secret-field"><input class="input" name="TELEGRAM_BOT_TOKEN" type="password" placeholder="оставьте пустым, чтобы не менять"><button type="button" class="reveal-btn" aria-label="Показать значение">👁</button></div></div>
              <div class="field"><label>YOUTUBE_API_KEY</label><div class="secret-field"><input class="input" name="YOUTUBE_API_KEY" type="password" placeholder="оставьте пустым, чтобы не менять"><button type="button" class="reveal-btn" aria-label="Показать значение">👁</button></div></div>
            </div>
          </div>

          <h3 class="section-title" id="webhooks" style="margin-top:24px">Вебхуки</h3>
          <div class="provider">
            <div class="provider-head"><div><h3>Исходящие события</h3><small>URL для отправки новых упоминаний, всплесков негатива и готовых отчетов.</small></div><span class="chip">{len(config.get('webhooks', []))} URL</span></div>
            <div class="field"><label>Webhook URL, каждый с новой строки</label><textarea class="textarea" name="webhooks">{esc(webhooks)}</textarea></div>
          </div>

          <h3 class="section-title" id="mail" style="margin-top:24px">Письма и доступ</h3>
          <div class="settings">
            <div class="provider">
              <div class="provider-head"><div><h3>SMTP для регистрации и восстановления</h3><small>Сервис будет отправлять письма с паролем, подтверждением почты и ссылками на восстановление.</small></div><span class="status {'on' if smtp_info['ready'] else 'off'}">{'готово' if smtp_info['ready'] else 'не настроено'}</span></div>
              <div class="meta"><span class="chip">регистрация</span><span class="chip">подтверждение email</span><span class="chip">сброс пароля</span></div>
              <div class="field"><label>PUBLIC_BASE_URL</label><input class="input" name="PUBLIC_BASE_URL" type="text" value="{esc(smtp_cfg['public_base_url'])}" placeholder="https://your-domain.example" style="width:100%;box-sizing:border-box"></div>
              <div class="field"><label>SMTP_HOST</label><input class="input" name="SMTP_HOST" type="text" value="{esc(smtp_cfg['host'])}" placeholder="smtp.yandex.ru / smtp.gmail.com" style="width:100%;box-sizing:border-box"></div>
              <div class="field"><label>SMTP_PORT</label><input class="input" name="SMTP_PORT" type="number" value="{esc(str(smtp_cfg['port']))}" style="width:180px;box-sizing:border-box"></div>
              <div class="field"><label>Защита соединения</label>
                <select class="select" name="SMTP_SECURITY" style="width:220px;box-sizing:border-box">
                  <option value="starttls" {'selected' if smtp_cfg['security'] == 'starttls' else ''}>STARTTLS</option>
                  <option value="ssl" {'selected' if smtp_cfg['security'] == 'ssl' else ''}>SSL</option>
                  <option value="plain" {'selected' if smtp_cfg['security'] == 'plain' else ''}>без шифрования</option>
                </select>
              </div>
              <div class="field"><label>SMTP_USERNAME</label><input class="input" name="SMTP_USERNAME" type="text" value="{esc(smtp_cfg['username'])}" placeholder="логин отправителя" style="width:100%;box-sizing:border-box"></div>
              <div class="field"><label>SMTP_PASSWORD</label><input class="input" name="SMTP_PASSWORD" type="password" placeholder="оставьте пустым, чтобы не менять" style="width:100%;box-sizing:border-box"></div>
              <div class="field"><label>SMTP_FROM_EMAIL</label><input class="input" name="SMTP_FROM_EMAIL" type="email" value="{esc(smtp_cfg['from_email'])}" placeholder="no-reply@your-domain.example" style="width:100%;box-sizing:border-box"></div>
              <div class="field"><label>SMTP_FROM_NAME</label><input class="input" name="SMTP_FROM_NAME" type="text" value="{esc(smtp_cfg['from_name'])}" placeholder="PR Monitor" style="width:100%;box-sizing:border-box"></div>
              <div class="coverage-note">{esc(smtp_info['message'])}</div>
            </div>
          </div>

          <h3 class="section-title" id="schedule" style="margin-top:24px">Расписание</h3>
          <div class="provider">
            <div class="provider-head"><div><h3>Автоматический сбор</h3><small>Фоновый сбор упоминаний с заданным интервалом.</small></div><span class="status {'on' if schedule_enabled else 'off'}">{'включён' if schedule_enabled else 'выключен'}</span></div>
            <label><input type="checkbox" name="enable_schedule" {'checked' if schedule_enabled else ''}> Автоматически собирать упоминания в фоне</label>
            <div class="field" style="margin-top:12px"><label>Как часто собирать</label>
              <select class="select input-narrow" name="schedule_interval">{schedule_options}</select>
            </div>
            <p class="hint">Фоновый сбор выполняет контейнер <code>worker</code>. Он перечитывает эти настройки автоматически — перезапуск не требуется. Если снять галочку, сбор встаёт на паузу, но воркер продолжает работать и сразу подхватит повторное включение.</p>
            <details class="hint-details"><summary>Запуск вручную</summary>
              <p class="hint">Для локального запуска без Docker:</p>
              <pre class="card" style="overflow:auto;margin:8px 0 0;background:#f6f9fb">python run.py watch --minutes 30</pre>
            </details>
          </div>

          <div class="settings-savebar">
            <button class="btn" type="submit">Сохранить интеграции</button>
            <a class="btn light" href="/">Вернуться</a>
            <span class="hint" style="margin-left:auto">Изменения вступают в силу при следующем сборе</span>
          </div>
        </div>
      </section>
    </form>
  </main>
  <script>
  (function() {{
    // Показать/скрыть значение токена
    document.querySelectorAll('.reveal-btn').forEach(function(btn) {{
      btn.addEventListener('click', function() {{
        var input = btn.parentNode.querySelector('input');
        if (!input) return;
        var show = input.type === 'password';
        input.type = show ? 'text' : 'password';
        btn.textContent = show ? '🙈' : '👁';
      }});
    }});
    // Подсветка активной секции в боковой навигации (scroll-spy)
    var navLinks = Array.prototype.slice.call(document.querySelectorAll('.side-nav a'));
    var sections = navLinks
      .map(function(a) {{ return document.getElementById(a.getAttribute('href').slice(1)); }})
      .filter(Boolean);
    if (sections.length && 'IntersectionObserver' in window) {{
      var observer = new IntersectionObserver(function(entries) {{
        entries.forEach(function(entry) {{
          if (!entry.isIntersecting) return;
          var id = entry.target.id;
          navLinks.forEach(function(a) {{
            a.classList.toggle('active', a.getAttribute('href') === '#' + id);
          }});
        }});
      }}, {{ rootMargin: '-20% 0px -70% 0px' }});
      sections.forEach(function(s) {{ observer.observe(s); }});
    }}
  }})();
  </script>
</body>
</html>"""


def render_claude_test(config_path: str, user: dict | None = None) -> str:
    config = load_config(config_path)
    settings = claude_config(config)
    status = claude_status(config)
    nav = nav_html("settings", user)
    has_key = bool(secret_value(config, "ANTHROPIC_API_KEY"))
    status_color = "on" if status["ok"] else "off"
    model_opts = "".join(
        f'<option value="{m}" {"selected" if m == settings["model"] else ""}>{m}</option>'
        for m in CLAUDE_MODELS
    )
    return f"""<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Проверка Claude API</title>
  <link rel="icon" type="image/svg+xml" href="/icon.svg">
  <link rel="apple-touch-icon" href="/icon.svg">
  <link rel="manifest" href="/manifest.json">
  <meta name="theme-color" content="#147487">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-title" content="PR Monitor">
  <style>{STYLE}</style>{i18n_assets()}
</head>
<body>
  <header class="top">
    <h1>Проверка Claude API</h1>
    <p>Диагностика подключения к Anthropic Claude.</p>
    {nav}
  </header>
  <main class="wrap">
    <div class="pagehead">
      <div><h2>Статус Claude API</h2><p>Модель: {esc(settings['model'])} · Макс. токенов: {settings['max_tokens']}</p></div>
      <a class="btn light" href="/settings#ai">← Настройки ИИ</a>
    </div>
    <div class="settings">
      <div class="provider">
        <div class="provider-head">
          <div><h3>Соединение</h3><small>Результат тестового обращения к Anthropic API.</small></div>
          <span class="status {status_color}">{'успешно' if status['ok'] else 'ошибка'}</span>
        </div>
        <div class="coverage-note">{esc(status['message'])}</div>
        {'<p class="hint" style="margin-top:10px">API-ключ не найден. Добавьте ANTHROPIC_API_KEY в настройках.</p>' if not has_key else ''}
        <div class="bar" style="margin-top:14px">
          <a class="btn" href="/claude-test">Проверить снова</a>
          <a class="btn light" href="https://console.anthropic.com/settings/keys" target="_blank" rel="noopener">Консоль Anthropic</a>
          <a class="btn light" href="/settings#ai">Настройки</a>
        </div>
      </div>
      <div class="provider">
        <div class="provider-head"><div><h3>Доступные модели</h3><small>Поддерживаемые версии Claude.</small></div></div>
        <ul class="hint" style="margin:0;padding-left:18px">
          <li><b>claude-opus-4-6</b> — самая мощная, лучший анализ, выше стоимость</li>
          <li><b>claude-sonnet-4-6</b> — баланс качества и цены</li>
          <li><b>claude-haiku-4-5-20251001</b> — быстрая и дешёвая, для простых запросов</li>
        </ul>
        <p class="hint" style="margin-top:10px">Текущая выбранная модель: <b>{esc(settings['model'])}</b>. Сменить можно в <a href="/settings#ai">настройках</a>.</p>
      </div>
    </div>
  </main>
</body>
</html>"""


def render_yandex_gpt_test(config_path: str, user: dict | None = None) -> str:
    config = load_config(config_path)
    settings = yandex_gpt_config(config)
    status = yandex_gpt_status(config)
    nav = nav_html("settings", user)
    has_key = bool(secret_value(config, "YANDEX_GPT_API_KEY"))
    status_color = "on" if status["ok"] else "off"
    return f"""<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Проверка YandexGPT</title>
  <link rel="icon" type="image/svg+xml" href="/icon.svg">
  <link rel="apple-touch-icon" href="/icon.svg">
  <link rel="manifest" href="/manifest.json">
  <meta name="theme-color" content="#147487">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-title" content="PR Monitor">
  <style>{STYLE}</style>{i18n_assets()}
</head>
<body>
  <header class="top">
    <h1>Проверка YandexGPT</h1>
    <p>Диагностика подключения к Yandex Cloud Foundation Models.</p>
    {nav}
  </header>
  <main class="wrap">
    <div class="pagehead">
      <div><h2>Статус YandexGPT</h2><p>Модель: {esc(settings['model'])} · Макс. токенов: {settings['max_tokens']}</p></div>
      <a class="btn light" href="/settings#ai">← Настройки ИИ</a>
    </div>
    <div class="settings">
      <div class="provider">
        <div class="provider-head">
          <div><h3>Соединение</h3><small>Результат тестового обращения к Yandex Cloud.</small></div>
          <span class="status {status_color}">{'успешно' if status['ok'] else 'ошибка'}</span>
        </div>
        <div class="coverage-note">{esc(status['message'])}</div>
        {'<p class="hint" style="margin-top:10px">API-ключ не найден. Добавьте YANDEX_GPT_API_KEY и YANDEX_FOLDER_ID в настройках.</p>' if not has_key else ''}
        <div class="bar" style="margin-top:14px">
          <a class="btn" href="/yandex-gpt-test">Проверить снова</a>
          <a class="btn light" href="https://yandex.cloud/ru/services/ai-studio" target="_blank" rel="noopener">Yandex AI Studio</a>
          <a class="btn light" href="/settings#ai">Настройки</a>
        </div>
      </div>
      <div class="provider">
        <div class="provider-head"><div><h3>Доступные модели</h3><small>Поддерживаемые версии YandexGPT.</small></div></div>
        <ul class="hint" style="margin:0;padding-left:18px">
          <li><b>yandexgpt/latest</b> — основная модель, баланс качества и цены</li>
          <li><b>yandexgpt-lite/latest</b> — быстрая и дешёвая, для простых запросов</li>
          <li><b>yandexgpt-32k/latest</b> — увеличенный контекст для больших выборок</li>
        </ul>
        <p class="hint" style="margin-top:10px">Текущая выбранная модель: <b>{esc(settings['model'])}</b>. Сменить можно в <a href="/settings#ai">настройках</a>.</p>
      </div>
    </div>
  </main>
</body>
</html>"""


def render_ollama_test(config_path: str, user: dict | None = None) -> str:
    config = load_config(config_path)
    settings = ollama_config(config)
    status = ollama_status(config)
    nav = nav_html("settings", user)
    model_rows = "".join(f"<div class='row'><span>{esc(model)}</span><b>локально</b></div>" for model in status.get("models", []))
    ready_text = "Модель готова" if status.get("model_ready") else "Выбранная модель не найдена"
    if not status.get("ok"):
        ready_text = "Ollama не отвечает"
    return f"""<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Проверка Ollama</title>
  <link rel="icon" type="image/svg+xml" href="/icon.svg">
  <link rel="apple-touch-icon" href="/icon.svg">
  <link rel="manifest" href="/manifest.json">
  <meta name="theme-color" content="#147487">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-title" content="PR Monitor">
  <style>{STYLE}</style>{i18n_assets()}
</head>
<body>
  <header class="top">
    <h1>Проверка Ollama</h1>
    <p>Проверяем бесплатную локальную ИИ-модель для анализа публикаций.</p>
    {nav}
  </header>
  <main class="wrap">
    <section class="layout">
      <div class="card">
        <div class="chart-title"><h3>{esc(ready_text)}</h3><span>{'включена в настройках' if settings['enabled'] else 'выключена в настройках'}</span></div>
        <div class="metric-grid">
          {metric_card("Адрес", settings["base_url"], "локальный API")}
          {metric_card("Модель", settings["model"], "выбрана для анализа")}
          {metric_card("Статус", "OK" if status.get("ok") else "Нет связи", status.get("message", ""))}
        </div>
        <div class="coverage-note">{esc(status.get("message", ""))}</div>
        <div class="bar" style="margin-top:14px">
          <a class="btn" href="/settings#ai">Вернуться к настройкам ИИ</a>
          <a class="btn light" href="/agent">Открыть ИИ-анализ</a>
        </div>
      </div>
      <aside class="side">
        <div class="card">
          <h3>Локальные модели</h3>
          <div class="list">{model_rows or '<span class="muted">Модели не найдены или Ollama не запущена.</span>'}</div>
        </div>
        <div class="card" style="margin-top:14px">
          <h3>Команды</h3>
          <pre style="white-space:pre-wrap;margin:0">ollama pull {esc(settings["model"])}
ollama serve</pre>
        </div>
      </aside>
    </section>
  </main>
</body>
</html>"""


def render_vk_test(config_path: str, user: dict | None = None) -> str:
    config = load_config(config_path)
    service_token = secret_value(config, "VK_SERVICE_TOKEN")
    token = service_token or secret_value(config, "VK_ACCESS_TOKEN")
    token_kind = "сервисный ключ" if service_token else "пользовательский токен"
    _projects = visible_projects(config, user)
    project = _projects[0] if _projects else {}
    query = next((item for item in project.get("queries", []) if item.strip()), "")
    title = "Проверка VK"
    status = "Не настроено"
    details = "Добавьте VK_SERVICE_TOKEN или VK_ACCESS_TOKEN в разделе “Источники и интеграции”, включите VK и сохраните настройки."
    rows = ""
    nav = nav_html("", user)

    def vk_error_message(error: dict) -> tuple[str, str]:
        code = error.get("error_code", "n/a")
        text = error.get("error_msg", "unknown error")
        normalized = str(text).lower()
        if code == 5 and "expired" in normalized:
            return (
                "VK-токен истёк",
                "Нужно выпустить новый токен: Источники и интеграции → VK → Получить токен, затем вставить access_token и сохранить настройки.",
            )
        if code == 5 and "another ip" in normalized:
            return (
                "VK-токен не подходит для онлайн-сервера",
                "VK отклонил текущий токен, потому что он был выдан для другого IP-адреса. Выпустите новый токен через кнопку “Получить токен” и сохраните его в настройках.",
            )
        if code == 5:
            return (
                "VK не принял токен",
                "Токен недействителен или выпущен не для этого приложения. Выпустите новый токен через кнопку “Получить токен” и сохраните настройки.",
            )
        return ("VK вернул ошибку", f"{text} · code {code}")

    if token and query:
        try:
            url = vk_search_url(query, token)
            payload, _ = fetch_url(url, config["user_agent"], timeout=15)
            parsed = json.loads(payload)
            if parsed.get("error"):
                error = parsed["error"]
                status, details = vk_error_message(error)
            else:
                items = iter_vk_items(payload)
                status = "VK подключен"
                details = f"Используется {token_kind}. Тестовый запрос: {query}. Найдено публичных постов: {len(items)}."
                for item in items[:10]:
                    rows += (
                        "<tr>"
                        f"<td><a href='{esc(item['url'])}' target='_blank' rel='noopener'>{esc(item['title'])}</a><div class='snippet'>{esc(item['snippet'])}</div></td>"
                        f"<td>{esc(item['source'])}</td>"
                        f"<td>{esc(display_datetime(item['published_at'], 'нет даты'))}</td>"
                        "</tr>"
                    )
        except Exception as exc:
            status = "Проверка не прошла"
            details = str(exc)
    elif not query:
        details = "В теме мониторинга нет поисковых фраз."

    return f"""<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title)}</title>
  <link rel="icon" type="image/svg+xml" href="/icon.svg">
  <link rel="apple-touch-icon" href="/icon.svg">
  <link rel="manifest" href="/manifest.json">
  <meta name="theme-color" content="#147487">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-title" content="PR Monitor">
  <style>{STYLE}</style>{i18n_assets()}
</head>
<body>
  <header class="top">
    <h1>{esc(title)}</h1>
    <p>Быстрая проверка токена и метода поиска публичных постов VK.</p>
    {nav}
  </header>
  <main class="wrap">
    <div class="card" style="margin-bottom:18px">
      <h2 style="margin:0 0 8px;color:#173a47">{esc(status)}</h2>
      <p class="hint">{esc(details)}</p>
      <div class="bar" style="margin:14px 0 0">
        <a class="btn" href="/settings#social">Вернуться к VK</a>
        <form method="post" action="/collect" style="display:inline"><button class="btn secondary" type="submit">Собрать упоминания</button></form>
      </div>
    </div>
    <table>
      <thead><tr><th>Пост</th><th>Источник</th><th>Дата</th></tr></thead>
      <tbody>{rows or '<tr><td colspan="3">Пока нет тестовых результатов.</td></tr>'}</tbody>
    </table>
  </main>
</body>
</html>"""


def render_yandex_test(config_path: str, user: dict | None = None) -> str:
    config = load_config(config_path)
    api_key = secret_value(config, "YANDEX_SEARCH_API_KEY")
    folder_id = secret_value(config, "YANDEX_FOLDER_ID")
    _projects = visible_projects(config, user)
    project = _projects[0] if _projects else {}
    query = next((item for item in project.get("queries", []) if item.strip()), "")
    title = "Проверка Яндекса"
    status = "Не настроено"
    details = "Добавьте YANDEX_SEARCH_API_KEY и YANDEX_FOLDER_ID в разделе “Источники и интеграции”, включите Яндекс и сохраните настройки."
    rows = ""
    nav = nav_html("", user)

    if api_key and folder_id and query:
        try:
            xml_text = yandex_search_request(query, api_key, folder_id, config["user_agent"])
            items = iter_yandex_items(xml_text)
            status = "Яндекс подключен"
            details = f"Тестовый запрос: {query}. Найдено результатов: {len(items)}."
            for item in items[:10]:
                rows += (
                    "<tr>"
                    f"<td><a href='{esc(item['url'])}' target='_blank' rel='noopener'>{esc(item['title'])}</a><div class='snippet'>{esc(item['snippet'])}</div></td>"
                    f"<td>{esc(item['source'])}</td>"
                    "</tr>"
                )
        except Exception as exc:
            status = "Проверка не прошла"
            details = str(exc)
    elif not query:
        details = "В теме мониторинга нет поисковых фраз."

    return f"""<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title)}</title>
  <link rel="icon" type="image/svg+xml" href="/icon.svg">
  <link rel="apple-touch-icon" href="/icon.svg">
  <link rel="manifest" href="/manifest.json">
  <meta name="theme-color" content="#147487">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-title" content="PR Monitor">
  <style>{STYLE}</style>{i18n_assets()}
</head>
<body>
  <header class="top">
    <h1>{esc(title)}</h1>
    <p>Быстрая проверка Yandex Search API по текущей теме мониторинга.</p>
    {nav}
  </header>
  <main class="wrap">
    <div class="card" style="margin-bottom:18px">
      <h2 style="margin:0 0 8px;color:#173a47">{esc(status)}</h2>
      <p class="hint">{esc(details)}</p>
      <div class="bar" style="margin:14px 0 0">
        <a class="btn" href="/settings#search">Вернуться к Яндексу</a>
        <form method="post" action="/collect" style="display:inline"><button class="btn secondary" type="submit">Собрать упоминания</button></form>
      </div>
    </div>
    <table>
      <thead><tr><th>Результат</th><th>Источник</th></tr></thead>
      <tbody>{rows or '<tr><td colspan="2">Пока нет тестовых результатов.</td></tr>'}</tbody>
    </table>
  </main>
</body>
</html>"""


def render_google_test(config_path: str, user: dict | None = None) -> str:
    config = load_config(config_path)
    api_key = secret_value(config, "GOOGLE_SEARCH_API_KEY")
    cx = secret_value(config, "GOOGLE_SEARCH_CX")
    _projects = visible_projects(config, user)
    project = _projects[0] if _projects else {}
    query = next((item for item in project.get("queries", []) if item.strip()), "")
    title = "Проверка Google"
    status = "Не настроено"
    details = "Добавьте GOOGLE_SEARCH_API_KEY и GOOGLE_SEARCH_CX в разделе “Источники и интеграции”, включите Google и сохраните настройки."
    rows = ""
    nav = nav_html("", user)

    if api_key and cx and query:
        try:
            url = google_custom_search_url(query, api_key, cx)
            payload, _ = fetch_url(url, config["user_agent"], timeout=20)
            parsed = json.loads(payload)
            if parsed.get("error"):
                error = parsed["error"]
                status = "Google вернул ошибку"
                details = f"{error.get('message', 'unknown error')} · code {error.get('code', 'n/a')}"
            else:
                items = iter_google_custom_items(payload)
                status = "Google подключен"
                details = f"Тестовый запрос: {query}. Найдено результатов: {len(items)}."
                for item in items[:10]:
                    rows += (
                        "<tr>"
                        f"<td><a href='{esc(item['url'])}' target='_blank' rel='noopener'>{esc(item['title'])}</a><div class='snippet'>{esc(item['snippet'])}</div></td>"
                        f"<td>{esc(item['source'])}</td>"
                        "</tr>"
                    )
        except Exception as exc:
            status = "Проверка не прошла"
            details = str(exc)
    elif not query:
        details = "В теме мониторинга нет поисковых фраз."

    return f"""<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title)}</title>
  <link rel="icon" type="image/svg+xml" href="/icon.svg">
  <link rel="apple-touch-icon" href="/icon.svg">
  <link rel="manifest" href="/manifest.json">
  <meta name="theme-color" content="#147487">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-title" content="PR Monitor">
  <style>{STYLE}</style>{i18n_assets()}
</head>
<body>
  <header class="top">
    <h1>{esc(title)}</h1>
    <p>Быстрая проверка Google Programmable Search по текущей теме мониторинга.</p>
    {nav}
  </header>
  <main class="wrap">
    <div class="card" style="margin-bottom:18px">
      <h2 style="margin:0 0 8px;color:#173a47">{esc(status)}</h2>
      <p class="hint">{esc(details)}</p>
      <div class="bar" style="margin:14px 0 0">
        <a class="btn" href="/settings#search">Вернуться к Google</a>
        <form method="post" action="/collect" style="display:inline"><button class="btn secondary" type="submit">Собрать упоминания</button></form>
      </div>
    </div>
    <table>
      <thead><tr><th>Результат</th><th>Источник</th></tr></thead>
      <tbody>{rows or '<tr><td colspan="2">Пока нет тестовых результатов.</td></tr>'}</tbody>
    </table>
  </main>
</body>
</html>"""


def render_serper_test(config_path: str, user: dict | None = None) -> str:
    config = load_config(config_path)
    api_key = secret_value(config, "SERPER_API_KEY")
    _projects = visible_projects(config, user)
    project = _projects[0] if _projects else {}
    query = next((item for item in project.get("queries", []) if item.strip()), "")
    title = "Проверка Google через Serper"
    status = "Не настроено"
    details = "Добавьте SERPER_API_KEY в разделе “Источники и интеграции”, включите Google через Serper и сохраните настройки."
    rows = ""
    nav = nav_html("", user)

    if api_key and query:
        try:
            payload = serper_search_request(query, api_key, config["user_agent"])
            parsed = json.loads(payload)
            if parsed.get("message") or parsed.get("error"):
                status = "Serper вернул ошибку"
                details = parsed.get("message") or json.dumps(parsed.get("error"), ensure_ascii=False)
            else:
                items = iter_serper_items(payload)
                status = "Serper подключен"
                details = f"Тестовый Google-запрос: {query}. Найдено результатов: {len(items)}."
                for item in items[:10]:
                    rows += (
                        "<tr>"
                        f"<td><a href='{esc(item['url'])}' target='_blank' rel='noopener'>{esc(item['title'])}</a><div class='snippet'>{esc(item['snippet'])}</div></td>"
                        f"<td>{esc(item['source'])}</td>"
                        "</tr>"
                    )
        except Exception as exc:
            status = "Проверка не прошла"
            details = str(exc)
    elif not query:
        details = "В теме мониторинга нет поисковых фраз."

    return f"""<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title)}</title>
  <link rel="icon" type="image/svg+xml" href="/icon.svg">
  <link rel="apple-touch-icon" href="/icon.svg">
  <link rel="manifest" href="/manifest.json">
  <meta name="theme-color" content="#147487">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-title" content="PR Monitor">
  <style>{STYLE}</style>{i18n_assets()}
</head>
<body>
  <header class="top">
    <h1>{esc(title)}</h1>
    <p>Проверка Google-выдачи через Serper API по текущей теме мониторинга.</p>
    {nav}
  </header>
  <main class="wrap">
    <div class="card" style="margin-bottom:18px">
      <h2 style="margin:0 0 8px;color:#173a47">{esc(status)}</h2>
      <p class="hint">{esc(details)}</p>
      <div class="bar" style="margin:14px 0 0">
        <a class="btn" href="/settings#search">Вернуться к источникам</a>
        <form method="post" action="/collect" style="display:inline"><button class="btn secondary" type="submit">Собрать упоминания</button></form>
      </div>
    </div>
    <table>
      <thead><tr><th>Результат Google</th><th>Источник</th></tr></thead>
      <tbody>{rows or '<tr><td colspan="2">Пока нет тестовых результатов.</td></tr>'}</tbody>
    </table>
  </main>
</body>
</html>"""


def handle_settings_post(config_path: str, body: bytes) -> None:
    form = parse_qs(body.decode("utf-8"))
    config = load_config(config_path)
    secrets = load_secrets(config)
    set_source_enabled(config, "google_news", "enable_google_news" in form)
    set_source_enabled(config, "gdelt_news", "enable_gdelt" in form)
    set_source_enabled(config, "newsdata", "enable_newsdata" in form)
    set_source_enabled(config, "web_pages", "enable_web_pages" in form)
    set_source_enabled(config, "google_custom_search", "enable_google_custom" in form)
    set_source_enabled(config, "serper_google", "enable_serper" in form)
    set_source_enabled(config, "yandex_search", "enable_yandex" in form)
    set_source_enabled(config, "vk_search", "enable_vk" in form)
    config["webhooks"] = [line.strip() for line in first_param(form, "webhooks").splitlines() if line.strip()]
    ai = config.setdefault("ai", {})
    ai["ollama_enabled"] = "enable_ollama" in form
    ai["ollama_base_url"] = first_param(form, "ollama_base_url", DEFAULT_BASE_URL) or DEFAULT_BASE_URL
    ai["ollama_model"] = first_param(form, "ollama_model", DEFAULT_MODEL) or DEFAULT_MODEL
    try:
        ai["ollama_timeout"] = max(5, min(180, int(first_param(form, "ollama_timeout", "45"))))
    except ValueError:
        ai["ollama_timeout"] = 45
    # Claude API settings
    ai["claude_enabled"] = "enable_claude" in form
    claude_model = first_param(form, "claude_model", CLAUDE_DEFAULT_MODEL) or CLAUDE_DEFAULT_MODEL
    if claude_model not in CLAUDE_MODELS:
        claude_model = CLAUDE_DEFAULT_MODEL
    ai["claude_model"] = claude_model
    try:
        ai["claude_max_tokens"] = max(256, min(4096, int(first_param(form, "claude_max_tokens", "1024"))))
    except ValueError:
        ai["claude_max_tokens"] = 1024
    # YandexGPT settings
    ai["yandex_gpt_enabled"] = "enable_yandex_gpt" in form
    yandex_gpt_model = first_param(form, "yandex_gpt_model", YANDEX_GPT_DEFAULT_MODEL) or YANDEX_GPT_DEFAULT_MODEL
    if yandex_gpt_model not in YANDEX_GPT_MODELS:
        yandex_gpt_model = YANDEX_GPT_DEFAULT_MODEL
    ai["yandex_gpt_model"] = yandex_gpt_model
    try:
        ai["yandex_gpt_max_tokens"] = max(256, min(4096, int(first_param(form, "yandex_gpt_max_tokens", "1024"))))
    except ValueError:
        ai["yandex_gpt_max_tokens"] = 1024

    set_source_enabled(config, "ok_search", "enable_ok" in form)

    # Расписание автоматического сбора
    schedule = config.setdefault("schedule", {})
    schedule["enabled"] = "enable_schedule" in form
    try:
        interval = int(first_param(form, "schedule_interval", "30"))
    except ValueError:
        interval = 30
    schedule["interval_minutes"] = interval if interval in {15, 30, 60, 120, 180, 360} else 30

    for key in [
        "ANTHROPIC_API_KEY",
        "YANDEX_GPT_API_KEY",
        "VK_CLIENT_SECRET",
        "VK_SERVICE_TOKEN",
        "OK_APPLICATION_KEY",
        "OK_SERVICE_TOKEN",
        "OK_SECRET_KEY",
        "GOOGLE_SEARCH_API_KEY",
        "GOOGLE_SEARCH_CX",
        "SERPER_API_KEY",
        "VK_ACCESS_TOKEN",
        "VK_APP_ID",
        "YANDEX_SEARCH_API_KEY",
        "YANDEX_FOLDER_ID",
        "TELEGRAM_BOT_TOKEN",
        "YOUTUBE_API_KEY",
        "NEWSDATA_API_KEY",
        "SMTP_HOST",
        "SMTP_PORT",
        "SMTP_USERNAME",
        "SMTP_PASSWORD",
        "SMTP_FROM_EMAIL",
        "SMTP_FROM_NAME",
        "SMTP_SECURITY",
        "PUBLIC_BASE_URL",
        "YOOKASSA_SHOP_ID",
        "YOOKASSA_SECRET_KEY",
    ]:
        value = first_param(form, key)
        if value:
            secrets[key] = value

    save_config(config, config_path)
    save_secrets(config, secrets)


def handle_topics_post(config_path: str, body: bytes, user: dict) -> str:
    """Создание/сохранение/удаление проекта. Возвращает сообщение для показа на странице
    (в т.ч. об упоре в лимиты тарифа)."""
    form = parse_qs(body.decode("utf-8"))
    config = load_config(config_path)
    account_id = account_id_of(user)
    if not account_id:
        return "Не удалось определить аккаунт."
    action = first_param(form, "action", "save")
    original_name = first_param(form, "original_project_name")
    is_admin = bool(user["is_superadmin"]) or user["role"] == "admin"
    conn = connect(config["database"])
    try:
        if action == "create":
            quota = account_quota_state(conn, account_id)["dimensions"]["projects"]
            if quota["reached"]:
                return (f"Достигнут лимит проектов по тарифу ({quota['limit']}). "
                        "Повысьте тариф, чтобы добавить ещё.")
            create_project_row(conn, account_id, "Новый проект", owner=user["username"])
            return "Проект создан."
        existing = get_project_by_name(conn, account_id, original_name) if original_name else None
        if action == "delete":
            # не даём удалить единственный проект аккаунта
            if existing and len(list_projects(conn, account_id)) > 1:
                delete_project_row(conn, existing["id"])
                return "Проект удалён."
            return "Нельзя удалить единственный проект аккаунта."
        # save (создаём, если проекта ещё нет — например, у нового аккаунта)
        creating = existing is None
        if creating:
            quota = account_quota_state(conn, account_id)["dimensions"]["projects"]
            if quota["reached"]:
                return (f"Достигнут лимит проектов по тарифу ({quota['limit']}). "
                        "Повысьте тариф, чтобы добавить ещё.")
            existing = create_project_row(conn, account_id, original_name or "Мониторинг", owner=user["username"])
        project_id = existing["id"]
        raw_name = first_param(form, "project_name", existing["name"] or "Мониторинг").strip() or "Мониторинг"
        new_name = _project_unique_name(conn, account_id, raw_name, exclude_id=project_id)
        queries = [line.strip() for line in first_param(form, "queries").splitlines() if line.strip()]
        control_urls = [line.strip() for line in first_param(form, "control_urls").splitlines() if line.strip()]
        # Квота запросов — общая по аккаунту: считаем сумму по другим проектам + новые здесь.
        from . import billing
        q_limit = billing.effective_quota(get_account(conn, account_id), "queries")
        if q_limit is not None:
            other = sum(
                len(p["queries"]) for p in list_projects(conn, account_id) if p["id"] != project_id
            )
            if other + len(queries) > q_limit:
                allowed = max(0, q_limit - other)
                return (f"Превышен лимит запросов по тарифу: {other + len(queries)} из {q_limit}. "
                        f"В этом проекте можно сохранить не более {allowed}. "
                        "Сократите список или повысьте тариф — остальные изменения не сохранены.")
        updates = {
            "name": new_name,
            "queries": queries,
            "control_urls": control_urls,
            "language": (first_param(form, "language", existing.get("language") or "ru") or "ru").strip() or "ru",
            "region": (first_param(form, "region", existing.get("region") or "RU") or "RU").strip() or "RU",
            "schedule_enabled": bool(first_param(form, "schedule_enabled")),
            "schedule_interval_hours": billing.normalize_collection_interval(
                first_param(form, "schedule_interval_hours") or billing.DEFAULT_COLLECTION_INTERVAL
            ),
        }
        # Профиль бренда обновляем только если форма его содержала (скрытый маркер brand_form):
        # parse_qs отбрасывает пустые поля, поэтому без маркера POST из старой формы
        # был бы неотличим от намеренной очистки и затирал бы профиль и подсказку для ИИ.
        if first_param(form, "brand_form"):
            brand = {
                "website": first_param(form, "brand_website"),
                "city": first_param(form, "brand_city"),
                "industry": first_param(form, "brand_industry"),
                "aliases": first_param(form, "brand_aliases"),
                "phone": first_param(form, "brand_phone"),
                "address": first_param(form, "brand_address"),
                "social_links": [line.strip() for line in first_param(form, "brand_social_links").splitlines() if line.strip()],
            }
            updates["brand"] = brand if any(brand.values()) else None
            updates["relevance_hint"] = first_param(form, "relevance_hint") or ""
        if is_admin:
            owner = first_param(form, "owner", existing.get("owner") or user["username"])
            if owner:
                updates["owner"] = owner
        else:
            updates["owner"] = user["username"]
        update_project_row(conn, project_id, **updates)
        return "Проект создан." if creating else "Проект сохранён."
    finally:
        conn.close()


def handle_dashboard_project_post(config_path: str, body: bytes, user: dict) -> tuple[str, bool]:
    form = parse_qs(body.decode("utf-8"))
    config = load_config(config_path)
    account_id = account_id_of(user)
    name = first_param(form, "project_name", "Новый проект")
    queries = [line.strip() for line in first_param(form, "queries").splitlines() if line.strip()]
    language = (first_param(form, "language", "ru") or "ru").strip() or "ru"
    region = (first_param(form, "region", "RU") or "RU").strip() or "RU"
    if not queries:
        queries = [name]
    conn = connect(config["database"])
    try:
        project = create_project_row(
            conn,
            account_id,
            name,
            queries=queries,
            owner=user["username"],
            language=language,
            region=region,
        )
    finally:
        conn.close()
    return project["name"], first_param(form, "next") == "collect"


def _render_auth_layout(title: str, subtitle: str, card_html: str) -> str:
    return f"""<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title)}</title>
  <link rel="icon" type="image/svg+xml" href="/icon.svg">
  <link rel="apple-touch-icon" href="/icon.svg">
  <link rel="manifest" href="/manifest.json">
  <meta name="theme-color" content="#147487">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-title" content="PR Monitor">
  <style>{STYLE}{AUTH_STYLE}</style>{i18n_assets()}
</head>
<body>
  <main class="auth-shell">
    <section class="auth-panel">
      <div class="auth-lang">{_language_switcher_html()}</div>
      <div>
        <div class="auth-brand">
          <div class="auth-logo">PR</div>
          <div>
            <div style="font-size:18px;font-weight:700;color:#1d1d1f">PR Monitor</div>
            <div style="font-size:14px;color:#7d8595">media intelligence platform</div>
          </div>
        </div>
        <p class="auth-kicker">Премиальная система мониторинга</p>
        <h1 class="auth-title">{esc(title)}</h1>
        <p class="auth-copy">{esc(subtitle)}</p>
        <div class="auth-points">
          <div class="auth-point"><b>СМИ и соцсети</b><span>Одна рабочая лента публикаций, дублей и цитируемости по проекту.</span></div>
          <div class="auth-point"><b>Аналитика под клиента</b><span>Дашборд, Excel-отчёты и ИИ-разбор истории упоминаний.</span></div>
          <div class="auth-point"><b>Командный доступ</b><span>Личные кабинеты, роли, проекты и разделение клиентских данных.</span></div>
          <div class="auth-point"><b>Единый вход</b><span>Почта, подтверждение доступа, восстановление пароля и управление аккаунтом.</span></div>
        </div>
      </div>
      <div class="auth-footer">
        <span>PR Monitor</span>
        <span>•</span>
        <span>медиамониторинг для агентств, PR и маркетинга</span>
      </div>
    </section>
    {card_html}
  </main>
</body>
</html>"""


def render_login(error: str = "", info: str = "", email: str = "") -> str:
    return _render_auth_layout(
        "Вход в рабочий кабинет",
        "Войдите в сервис, чтобы открыть проекты, историю упоминаний, ИИ-анализ и отчётность.",
        f"""
        <form class="auth-card" method="post" action="/login">
          <h1>Вход</h1>
          <p>Используйте логин администратора или email, который пришёл вам в письме с доступом.</p>
          {f'<div class="auth-alert">{esc(error)}</div>' if error else ''}
          {f'<div class="auth-info">{esc(info)}</div>' if info else ''}
          <div class="field">
            <label>Логин или email</label>
            <input class="input" name="username" autocomplete="username" autofocus value="{esc(email)}" style="width:100%;box-sizing:border-box">
          </div>
          <div class="field">
            <label>Пароль</label>
            <input class="input" name="password" type="password" autocomplete="current-password" style="width:100%;box-sizing:border-box">
          </div>
          <button class="btn" type="submit" style="width:100%">Войти в кабинет</button>
          <div class="auth-links">
            <a href="/register">Зарегистрироваться</a>
            <a href="/forgot-password">Не помню пароль</a>
          </div>
          <p class="auth-note">Если кабинет вам создаёт администратор, письмо с данными для входа придёт на указанную почту.</p>
        </form>
        """,
    )


def render_register(error: str = "", info: str = "", full_name: str = "", email: str = "") -> str:
    return _render_auth_layout(
        "Создайте кабинет в PR Monitor",
        "После регистрации сервис отправит письмо с временным паролем и ссылкой для подтверждения почты.",
        f"""
        <form class="auth-card" method="post" action="/register">
          <h1>Регистрация</h1>
          <p>Укажите рабочую почту. Логином для входа станет этот email.</p>
          {f'<div class="auth-alert">{esc(error)}</div>' if error else ''}
          {f'<div class="auth-info">{esc(info)}</div>' if info else ''}
          <div class="field">
            <label>Имя или компания</label>
            <input class="input" name="full_name" autocomplete="name" value="{esc(full_name)}" style="width:100%;box-sizing:border-box">
          </div>
          <div class="field">
            <label>Рабочий email</label>
            <input class="input" name="email" type="email" autocomplete="email" value="{esc(email)}" required style="width:100%;box-sizing:border-box">
          </div>
          <button class="btn" type="submit" style="width:100%">Получить доступ</button>
          <div class="auth-links">
            <a href="/login">Уже есть доступ</a>
            <a href="/forgot-password">Восстановить пароль</a>
          </div>
        </form>
        """,
    )


def render_forgot_password(error: str = "", info: str = "", email: str = "") -> str:
    return _render_auth_layout(
        "Восстановление пароля",
        "Введите почту, и мы отправим ссылку для создания нового пароля.",
        f"""
        <form class="auth-card" method="post" action="/forgot-password">
          <h1>Сброс пароля</h1>
          <p>Письмо придёт на тот адрес, который привязан к кабинету.</p>
          {f'<div class="auth-alert">{esc(error)}</div>' if error else ''}
          {f'<div class="auth-info">{esc(info)}</div>' if info else ''}
          <div class="field">
            <label>Email</label>
            <input class="input" name="email" type="email" autocomplete="email" required value="{esc(email)}" style="width:100%;box-sizing:border-box">
          </div>
          <button class="btn" type="submit" style="width:100%">Отправить ссылку</button>
          <div class="auth-links">
            <a href="/login">Вернуться ко входу</a>
            <a href="/register">Создать кабинет</a>
          </div>
        </form>
        """,
    )


def render_reset_password(token: str, error: str = "", info: str = "") -> str:
    return _render_auth_layout(
        "Новый пароль",
        "Задайте новый пароль для входа в кабинет.",
        f"""
        <form class="auth-card" method="post" action="/reset-password">
          <h1>Новый пароль</h1>
          <p>После сохранения вы сразу сможете войти в систему.</p>
          {f'<div class="auth-alert">{esc(error)}</div>' if error else ''}
          {f'<div class="auth-info">{esc(info)}</div>' if info else ''}
          <input type="hidden" name="token" value="{esc(token)}">
          <div class="field">
            <label>Новый пароль</label>
            <input class="input" name="password" type="password" autocomplete="new-password" required style="width:100%;box-sizing:border-box">
          </div>
          <div class="field">
            <label>Повторите пароль</label>
            <input class="input" name="password_confirm" type="password" autocomplete="new-password" required style="width:100%;box-sizing:border-box">
          </div>
          <button class="btn" type="submit" style="width:100%">Сохранить пароль</button>
          <div class="auth-links">
            <a href="/login">Вернуться ко входу</a>
          </div>
        </form>
        """,
    )


def render_auth_notice(title: str, message: str, links: list[tuple[str, str]] | None = None) -> str:
    links_html = "".join(f'<a href="{esc(href)}">{esc(label)}</a>' for href, label in (links or []))
    return _render_auth_layout(
        title,
        message,
        f"""
        <section class="auth-card">
          <h1>{esc(title)}</h1>
          <div class="auth-info">{esc(message)}</div>
          <div class="auth-links">{links_html}</div>
        </section>
        """,
    )


def _source_status(s: dict) -> tuple[str, str]:
    """Возвращает (текст, css-класс цвета) статуса источника по статистике среза."""
    if s.get("disabled"):
        return "заблокирован (403/429)", "off"
    if s.get("errors") and not s.get("inserted"):
        return "ошибки", "off"
    if not s.get("found"):
        return "нет данных", "metric-state warn"
    if s.get("found") and not s.get("inserted"):
        return "только дубли", "metric-state warn"
    return "работает", "on"


def _build_source_health_prompt(report: dict) -> str:
    meta = report.get("report", {})
    sources = meta.get("sources", [])
    lines = []
    for s in sources:
        status, _ = _source_status(s)
        lines.append(
            f"- {s.get('label')} [{s.get('type')}]: найдено {s.get('found', 0)}, "
            f"новых {s.get('inserted', 0)}, ошибок {s.get('errors', 0)}, "
            f"статус: {status}" + (f", последняя ошибка: {s.get('last_error')}" if s.get('last_error') else "")
        )
    listing = "\n".join(lines) or "- источников нет"
    return (
        "Ты — инженер по мониторингу источников данных в системе медиа-аналитики. "
        "Ниже статистика работы источников за последний срез сбора (сервер находится в РФ, "
        "часть зарубежных сервисов может блокироваться по гео).\n\n"
        f"Срез: найдено всего {meta.get('total_found', 0)}, новых {meta.get('total_inserted', 0)}, "
        f"статус {meta.get('status', '?')}.\n\n"
        f"Источники:\n{listing}\n\n"
        "Дай краткий разбор без воды:\n"
        "1) Какие источники работают штатно.\n"
        "2) Какие молчат или сбоят и наиболее вероятная причина (гео-блок, нет ключа, "
        "неверный запрос, источник пуст).\n"
        "3) Приоритетные действия: что починить в первую очередь, что можно отключить.\n"
        "Опирайся только на цифры выше, не выдумывай источники."
    )


def _source_health_section(config: dict, report: dict | None, last_audit: dict | None, ai_check: bool) -> str:
    if not report or not report.get("report", {}).get("sources"):
        return (
            '<section class="card" style="margin-bottom:18px">'
            '<div class="pagehead"><div><h2>Здоровье источников</h2>'
            '<p>ИИ-контроль работоспособности источников сбора.</p></div></div>'
            '<p class="hint">Статистика появится после первого среза. Запустите сбор на дашборде — '
            'система зафиксирует, какие источники реально отдают данные.</p></section>'
        )
    meta = report["report"]
    sources = meta.get("sources", [])
    working = sum(1 for s in sources if _source_status(s)[1] == "on")
    silent = sum(1 for s in sources if not s.get("found"))
    errored = sum(1 for s in sources if s.get("disabled") or s.get("errors"))

    rows = ""
    for s in sorted(sources, key=lambda x: (x.get("inserted", 0), x.get("found", 0))):
        status_text, status_cls = _source_status(s)
        rows += (
            "<tr>"
            f"<td><b>{esc(str(s.get('label', '')))}</b></td>"
            f"<td class='muted'>{esc(str(s.get('type', '')))}</td>"
            f"<td>{s.get('found', 0)}</td>"
            f"<td>{s.get('inserted', 0)}</td>"
            f"<td>{s.get('errors', 0)}</td>"
            f"<td><span class='status {status_cls}'>{esc(status_text)}</span></td>"
            "</tr>"
        )

    created = esc(str(report.get("created_at", "")))
    # ИИ-комментарий
    provider = active_provider(config)
    if ai_check and provider:
        result = ai_complete(config, "Ты инженер по источникам данных.", _build_source_health_prompt(report), max_tokens=1200)
        if result.get("ok"):
            ai_block = (
                f'<div class="ai-answer" style="margin-top:12px">{render_ai_text(result["text"])}</div>'
                f'<div class="coverage-note">Анализ выполнил {esc(provider_label(config))}</div>'
            )
        else:
            ai_block = f'<p class="hint" style="margin-top:12px">ИИ не ответил: {esc(result.get("message", ""))}</p>'
    elif provider:
        ai_block = (
            '<div class="bar" style="margin-top:12px">'
            f'<a class="btn" href="/admin?ai_check=1">Проверить источники с ИИ ({esc(provider_label(config))})</a>'
            '</div>'
        )
    else:
        ai_block = '<p class="hint" style="margin-top:12px">Включите ИИ-провайдер в настройках, чтобы получить разбор источников.</p>'

    audit_line = ""
    if last_audit and last_audit.get("status") == "ok" and last_audit.get("agreement") is not None:
        audit_details = last_audit.get("details") or []
        audit_checked = (
            len([d for d in audit_details if d.get("relevant", True)])
            if audit_details else last_audit.get("checked", 0)
        )
        audit_line = (
            f'<div class="coverage-note">Последняя ИИ-проверка тональности: '
            f'совпадение {last_audit.get("agreement")}% на {audit_checked} релевантных публ.</div>'
        )

    return f"""
    <section class="card" style="margin-bottom:18px">
      <div class="pagehead">
        <div><h2>Здоровье источников</h2><p>Доставка данных по источникам за последний срез ({created}).</p></div>
      </div>
      <div class="metric-grid" style="margin-bottom:12px">
        {metric_card("Источников", len(sources), "включено в срезе")}
        {metric_card("Работают", working, "отдали новые данные")}
        {metric_card("Молчат", silent, "0 найдено")}
        {metric_card("Сбои", errored, "ошибки или блокировка")}
      </div>
      <table>
        <thead><tr><th>Источник</th><th>Тип</th><th>Найдено</th><th>Новых</th><th>Ошибки</th><th>Статус</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
      {audit_line}
      {ai_block}
    </section>
    """


def render_admin(config_path: str, user: dict, message: str = "", query_params: dict | None = None) -> str:
    config = load_config(config_path)
    conn = connect(config["database"])
    try:
        users = list_users(conn)
        default_admin_warning = uses_default_admin_password(conn)
        source_report = latest_source_report(conn)
        last_audit = latest_ai_audit(conn)
        pending_sentiment = count_pending_sentiment(conn)
        irrelevant_total = count_irrelevant(conn)
    finally:
        conn.close()
    ai_check = first_param(query_params or {}, "ai_check") == "1"
    source_health_html = _source_health_section(config, source_report, last_audit, ai_check)
    correcting = first_param(query_params or {}, "sentiment_correcting") == "1"
    sentiment_tools_html = f"""
    <section class="card" style="margin-bottom:18px">
      <div class="pagehead"><div><h2>Качество данных</h2>
        <p>После каждого сбора ИИ перепроверяет публикации: уточняет тональность и исключает из статистики
        случайные совпадения, не относящиеся к объекту мониторинга. Здесь — ручной догон по всей базе.</p></div></div>
      <p class="hint">Не проверено ИИ: <b>{pending_sentiment}</b> публикаций (тональность и/или релевантность).
        Уже исключено как нерелевантные: <b>{irrelevant_total}</b> — они не учитываются в статистике и дашборде.
        Кнопка запустит проверку всех необработанных публикаций — это разовая операция, обычно не требуется.</p>
      <div class="bar" style="margin-top:10px">
        <form method="post" action="/correct-sentiment" style="margin:0">
          <button class="btn light" type="submit">Проверить тональность и релевантность через ИИ</button>
        </form>
        {'<span class="status metric-state warn" style="align-self:center">идёт проверка — обновите страницу через минуту</span>' if correcting else ''}
      </div>
    </section>"""
    user_rows = ""
    for row in users:
        row_id = row["id"]
        row_username = row["username"]
        row_email = row["email"] or "—"
        row_verified = bool(row["email_verified"])
        row_role = row["role"]
        row_active = bool(row["is_active"])
        row_full_name = row["full_name"] or ""
        row_created = row["created_at"]
        can_disable = row_username != user["username"]
        user_rows += f"""
        <tr>
          <td><b>{esc(row_username)}</b><div class="muted">{esc(row_full_name)}</div></td>
          <td><div>{esc(row_email)}</div><div class="muted">{'подтверждён' if row_verified else 'ждёт подтверждения'}</div></td>
          <td>{esc(user_role_label(row))}</td>
          <td>{'<span class="status on">активен</span>' if row_active else '<span class="status off">заблокирован</span>'}</td>
          <td>{esc(row_created)}</td>
          <td>
            <form method="post" action="/admin" class="bar" style="margin:0">
              <input type="hidden" name="action" value="update_user">
              <input type="hidden" name="user_id" value="{row_id}">
              <select class="select" name="role">
                <option value="user" {"selected" if row_role == "user" else ""}>пользователь</option>
                <option value="admin" {"selected" if row_role == "admin" else ""}>админ</option>
              </select>
              <label class="muted"><input type="checkbox" name="is_active" value="1" {"checked" if row_active else ""} {"disabled" if not can_disable else ""}> доступ включен</label>
              <button class="btn light" type="submit">Сохранить</button>
            </form>
            <form method="post" action="/admin" class="bar" style="margin:8px 0 0">
              <input type="hidden" name="action" value="reset_password">
              <input type="hidden" name="user_id" value="{row_id}">
              <input class="input" name="password" type="password" placeholder="новый пароль">
              <button class="btn light" type="submit">Сменить пароль</button>
            </form>
          </td>
        </tr>
        """
    project_rows = ""
    for project in visible_projects(config, user):
        project_rows += f"""
        <tr>
          <td><b>{esc(project.get("name", ""))}</b><div class="muted">{len(project.get("queries", []))} запросов</div></td>
          <td>{esc(project.get("owner", "admin"))}</td>
          <td><a href="/topics?project={quote(project.get("name", ""))}">Открыть</a></td>
        </tr>
        """
    nav = nav_html("admin", user)
    return f"""<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Админ-панель</title>
  <link rel="icon" type="image/svg+xml" href="/icon.svg">
  <link rel="apple-touch-icon" href="/icon.svg">
  <link rel="manifest" href="/manifest.json">
  <meta name="theme-color" content="#147487">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-title" content="PR Monitor">
  <style>{STYLE}</style>{i18n_assets()}
</head>
<body>
  <header class="top">
    <h1>Админ-панель</h1>
    <p>Управление пользователями, ролями и владельцами проектов. Локальная версия подготовлена как основа будущей онлайн-платформы.</p>
    {nav}
  </header>
  <main class="wrap">
    {f'<div class="card" style="margin-bottom:18px"><b>{esc(message)}</b></div>' if message else ''}
    {('<div class="card" style="margin-bottom:18px;border-left:4px solid #b8860b">'
      '<b>Внимание:</b> у стандартного пользователя <code>admin</code> всё ещё стоит стартовый пароль. '
      'Перед рабочим запуском лучше сразу сменить его в таблице ниже.'
      '</div>') if default_admin_warning else ''}
    {source_health_html}
    {sentiment_tools_html}
    <section class="admin-grid">
      <form class="provider" method="post" action="/admin">
        <input type="hidden" name="action" value="create_user">
        <div class="provider-head"><div><h3>Выдать доступ</h3><small>Создайте кабинет вручную или сразу отправьте письмо с доступом на email.</small></div></div>
        <div class="field"><label>Логин</label><input class="input" name="username" style="width:100%;box-sizing:border-box" placeholder="если пусто — будет использован email"></div>
        <div class="field"><label>Email</label><input class="input" name="email" type="email" style="width:100%;box-sizing:border-box" placeholder="user@company.ru"></div>
        <div class="field"><label>Имя / компания</label><input class="input" name="full_name" style="width:100%;box-sizing:border-box"></div>
        <div class="field"><label>Пароль</label><input class="input" name="password" type="password" style="width:100%;box-sizing:border-box" placeholder="если пусто — сгенерируется автоматически"></div>
        <div class="field"><label>Роль</label><select class="select" name="role" style="width:100%;box-sizing:border-box"><option value="user">пользователь</option><option value="admin">админ</option></select></div>
        <button class="btn" type="submit" style="width:100%">Создать кабинет</button>
        <p class="hint">Если SMTP уже настроен, пользователь сразу получит письмо с паролем и ссылкой подтверждения. Пользователь увидит только свои проекты. Админ видит все проекты и может менять владельца проекта в разделе “Проекты”.</p>
      </form>
      <div>
        <div class="pagehead"><div><h2>Пользователи</h2><p>Роли, блокировка доступа и смена паролей.</p></div></div>
        <table>
          <thead><tr><th>Пользователь</th><th>Email</th><th>Роль</th><th>Статус</th><th>Создан</th><th>Действия</th></tr></thead>
          <tbody>{user_rows or '<tr><td colspan="6">Пользователей пока нет.</td></tr>'}</tbody>
        </table>
        <div class="pagehead" style="margin-top:24px"><div><h2>Проекты</h2><p>Кому принадлежат сохраненные поисковые запросы.</p></div></div>
        <table>
          <thead><tr><th>Проект</th><th>Владелец</th><th></th></tr></thead>
          <tbody>{project_rows or '<tr><td colspan="3">Проектов пока нет.</td></tr>'}</tbody>
        </table>
      </div>
    </section>
  </main>
</body>
</html>"""


def handle_admin_post(config_path: str, body: bytes, user: dict) -> str:
    if user["role"] != "admin":
        return "Недостаточно прав."
    form = parse_qs(body.decode("utf-8"))
    action = first_param(form, "action")
    config = load_config(config_path)
    conn = connect(config["database"])
    try:
        if action == "create_user":
            username = first_param(form, "username")
            email = normalize_email(first_param(form, "email"))
            password = first_param(form, "password")
            role = first_param(form, "role", "user")
            full_name = first_param(form, "full_name")
            if not username and not email:
                return "Укажите логин или email."
            seat_quota = account_quota_state(conn, account_id_of(user))["dimensions"]["users"]
            if seat_quota["reached"]:
                return (f"Достигнут лимит пользователей по тарифу ({seat_quota['limit']}). "
                        "Повысьте тариф, чтобы добавить ещё сотрудников.")
            if not password:
                password = "PRM-" + datetime.now(timezone.utc).strftime("%H%M%S") + os.urandom(3).hex()
            login = username or email
            user_id = create_user(conn, login, password, role, full_name, email=email, email_verified=not bool(email))
            # новый сотрудник попадает в аккаунт пригласившего админа (то же место/тенант)
            if account_id_of(user):
                conn.execute("UPDATE users SET account_id = ? WHERE id = ?", (account_id_of(user), user_id))
                conn.commit()
            if email:
                verify_token = create_email_verification_token(conn, user_id, email)
                verify_url = build_public_url(config, "/verify-email", token=verify_token)
                mailed, mail_message = send_verification_email(config, email, full_name or login, password, verify_url)
                if mailed:
                    return f"Пользователь {login} создан, письмо с доступом отправлено."
                return f"Пользователь {login} создан, но письмо не ушло: {mail_message}"
            return f"Пользователь {login} создан."
        if action == "update_user":
            user_id = int(first_param(form, "user_id", "0"))
            target = conn.execute("SELECT username FROM users WHERE id = ?", (user_id,)).fetchone()
            is_active = "is_active" in form
            if target and target["username"] == user["username"]:
                is_active = True
            update_user(conn, user_id, first_param(form, "role", "user"), is_active)
            return "Пользователь обновлен."
        if action == "reset_password":
            user_id = int(first_param(form, "user_id", "0"))
            password = first_param(form, "password")
            if not password:
                return "Введите новый пароль."
            update_user_password(conn, user_id, password)
            return "Пароль обновлен."
    except Exception as exc:
        return f"Не удалось выполнить действие: {exc}"
    finally:
        conn.close()
    return "Действие не распознано."


def _billing_account_row(account: dict) -> str:
    from . import billing
    usage = account.get("usage", {})
    dims = []
    for dim, label in (("projects", "проектов"), ("queries", "запросов"), ("users", "польз.")):
        limit = billing.effective_quota(account, dim)
        limit_txt = "∞" if limit is None else str(limit)
        dims.append(f"{usage.get(dim, 0)}/{limit_txt} {label}")
    days = billing.account_days_left(account)
    days_txt = "—" if days is None else f"{days} дн."
    active = billing.account_is_active(account)
    status_cls = "on" if active else "off"
    return (
        "<tr>"
        f'<td><b>{esc(account.get("name",""))}</b><div class="muted">#{account.get("id")}</div></td>'
        f'<td>{esc(billing.plan_title(account.get("plan")))}</td>'
        f'<td><span class="status {status_cls}">{esc(billing.ACCOUNT_STATUSES.get(account.get("status",""), account.get("status","")))}</span></td>'
        f'<td class="muted">{esc(" · ".join(dims))}</td>'
        f'<td>{esc(days_txt)}</td>'
        f'<td><a href="/billing?account_id={account.get("id")}">Управлять</a></td>'
        "</tr>"
    )


def render_billing(config_path: str, user: dict, message: str = "", query_params: dict | None = None) -> str:
    from . import billing
    config = load_config(config_path)
    query_params = query_params or {}
    nav = nav_html("billing", user)
    sid_raw = first_param(query_params, "account_id")
    conn = connect(config["database"])
    try:
        accounts = list_accounts(conn)
        selected = None
        sel_usage = {}
        payments = []
        sel_users = []
        if sid_raw:
            try:
                selected = get_account(conn, int(sid_raw))
            except ValueError:
                selected = None
        if selected:
            sel_usage = account_usage(conn, selected["id"])
            payments = list_payments(conn, selected["id"])
            sel_users = [dict(r) for r in conn.execute(
                "SELECT username, email, role, is_active FROM users WHERE account_id = ? ORDER BY id", (selected["id"],)
            ).fetchall()]
    finally:
        conn.close()

    if selected:
        plan_opts = "".join(
            f'<option value="{p}" {"selected" if selected.get("plan")==p else ""}>{esc(billing.plan_title(p))}</option>'
            for p in billing.PLAN_ORDER
        )
        status_opts = "".join(
            f'<option value="{s}" {"selected" if selected.get("status")==s else ""}>{esc(lbl)}</option>'
            for s, lbl in billing.ACCOUNT_STATUSES.items()
        )
        period_val = (selected.get("period_end") or "")[:10]
        def _qval(dim):
            v = selected.get(f"quota_{dim}")
            return "" if v is None else str(v)
        usage_line = " · ".join(
            f"{sel_usage.get(dim,0)} / {('∞' if billing.effective_quota(selected, dim) is None else billing.effective_quota(selected, dim))} {label}"
            for dim, label in (("projects","проектов"),("queries","запросов"),("users","пользователей"))
        )
        pay_rows = "".join(
            f'<tr><td>{esc((p.get("created_at") or "")[:10])}</td><td>{esc(str(p.get("amount") or 0))} ₽</td>'
            f'<td>{esc(billing.plan_title(p.get("plan")) if p.get("plan") else "—")}</td>'
            f'<td>{esc(str(p.get("period_months") or "—"))}</td><td>{esc(p.get("provider") or "")}</td>'
            f'<td class="muted">{esc(p.get("note") or "")}</td></tr>'
            for p in payments
        ) or '<tr><td colspan="6" class="muted">Платежей пока нет.</td></tr>'
        user_rows = "".join(
            f'<tr><td>{esc(u["username"])}</td><td>{esc(u.get("email") or "—")}</td>'
            f'<td>{esc(user_role_label(u))}</td><td>{"активен" if u["is_active"] else "заблокирован"}</td></tr>'
            for u in sel_users
        ) or '<tr><td colspan="4" class="muted">Пользователей нет.</td></tr>'
        body = f"""
        <div class="pagehead"><div><h2>Аккаунт «{esc(selected.get('name',''))}»</h2>
          <p>Использование: {esc(usage_line)}. <a href="/billing">← ко всем клиентам</a></p></div></div>
        <section class="admin-grid">
          <form class="provider" method="post" action="/billing">
            <input type="hidden" name="action" value="save_account">
            <input type="hidden" name="account_id" value="{selected['id']}">
            <div class="provider-head"><div><h3>Тариф и доступ</h3><small>Смена тарифа, статуса, срока и индивидуальных квот.</small></div></div>
            <div class="field"><label>Название клиента</label><input class="input" name="name" value="{esc(selected.get('name',''))}" style="width:100%;box-sizing:border-box"></div>
            <div class="field"><label>Тариф</label><select class="select" name="plan" style="width:100%;box-sizing:border-box">{plan_opts}</select></div>
            <div class="field"><label>Статус</label><select class="select" name="status" style="width:100%;box-sizing:border-box">{status_opts}</select></div>
            <div class="field"><label>Оплачено до (пусто — бессрочно)</label><input class="input" name="period_end" type="date" value="{esc(period_val)}" style="width:100%;box-sizing:border-box"></div>
            <div class="field"><label>Квоты — индивидуально (пусто = по тарифу)</label>
              <div class="bar" style="margin:0;gap:8px">
                <input class="input" name="quota_projects" placeholder="проекты" value="{_qval('projects')}" style="width:31%">
                <input class="input" name="quota_queries" placeholder="запросы" value="{_qval('queries')}" style="width:31%">
                <input class="input" name="quota_users" placeholder="польз." value="{_qval('users')}" style="width:31%">
              </div>
            </div>
            <button class="btn" type="submit" style="width:100%">Сохранить</button>
          </form>
          <form class="provider" method="post" action="/billing">
            <input type="hidden" name="action" value="record_payment">
            <input type="hidden" name="account_id" value="{selected['id']}">
            <div class="provider-head"><div><h3>Отметить оплату</h3><small>Зафиксировать платёж, активировать тариф и продлить срок.</small></div></div>
            <div class="field"><label>Сумма, ₽</label><input class="input" name="amount" type="number" step="1" placeholder="11900" style="width:100%;box-sizing:border-box"></div>
            <div class="field"><label>Тариф</label><select class="select" name="plan" style="width:100%;box-sizing:border-box">{plan_opts}</select></div>
            <div class="field"><label>Период, мес</label><input class="input" name="period_months" type="number" value="1" style="width:100%;box-sizing:border-box"></div>
            <div class="field"><label>Комментарий</label><input class="input" name="note" placeholder="например: счёт №12, безнал" style="width:100%;box-sizing:border-box"></div>
            <button class="btn" type="submit" style="width:100%">Провести оплату</button>
            <p class="hint">Активирует аккаунт, ставит тариф и продлевает «оплачено до» на N месяцев.</p>
          </form>
        </section>
        <div class="pagehead" style="margin-top:20px"><div><h2>История платежей</h2></div></div>
        <table><thead><tr><th>Дата</th><th>Сумма</th><th>Тариф</th><th>Мес</th><th>Способ</th><th>Заметка</th></tr></thead>
          <tbody>{pay_rows}</tbody></table>
        <div class="pagehead" style="margin-top:20px"><div><h2>Пользователи аккаунта</h2></div></div>
        <table><thead><tr><th>Логин</th><th>Email</th><th>Роль</th><th>Статус</th></tr></thead>
          <tbody>{user_rows}</tbody></table>
        """
    else:
        rows = "".join(_billing_account_row(a) for a in accounts) or '<tr><td colspan="6" class="muted">Аккаунтов нет.</td></tr>'
        from .yookassa import yookassa_status
        yk = yookassa_status(config)
        yk_cfg = yk["settings"]
        base_url = (secret_value(config, "PUBLIC_BASE_URL") or "").rstrip("/")
        webhook_url = (base_url + "/yookassa-webhook") if base_url else "/yookassa-webhook"
        integrations = f"""
        <details class="provider" style="margin-bottom:22px" {'open' if not yk['ready'] else ''}>
          <summary style="cursor:pointer;display:flex;align-items:center;justify-content:space-between;gap:12px;list-style:none">
            <span><b>Платёжные интеграции</b><small class="muted" style="display:block">Подключение приёма онлайн-оплаты (ключи ЮKassa, вебхук)</small></span>
            <span class="status {'on' if yk['ready'] else 'off'}">{'ЮKassa подключена' if yk['ready'] else 'не настроена'}</span>
          </summary>
          <form method="post" action="/billing" style="margin-top:14px">
            <input type="hidden" name="action" value="save_integrations">
            <div class="provider-head"><div><h3>ЮKassa</h3><small>Онлайн-оплата подписок клиентами (РФ). Ключи: кабинет ЮKassa → «Интеграция → Ключи API».</small></div></div>
            <div class="field"><label>YOOKASSA_SHOP_ID</label><input class="input" name="YOOKASSA_SHOP_ID" type="text" value="{esc(yk_cfg['shop_id'])}" placeholder="например 123456" style="width:100%;box-sizing:border-box"></div>
            <div class="field"><label>YOOKASSA_SECRET_KEY</label><input class="input" name="YOOKASSA_SECRET_KEY" type="password" placeholder="оставьте пустым, чтобы не менять" style="width:100%;box-sizing:border-box"></div>
            <button class="btn" type="submit">Сохранить ключи</button>
            <div class="coverage-note" style="margin-top:10px">В кабинете ЮKassa добавьте HTTP-уведомление на событие <b>payment.succeeded</b> с URL:<br><code>{esc(webhook_url)}</code></div>
            <p class="hint">Для проверки используйте тестовый магазин ЮKassa и тестовые карты. KZ-приём (Freedom Pay/Kaspi) добавится отдельным модулем.</p>
          </form>
        </details>
        <div class="pagehead"><div><h2>Клиенты</h2><p>Все аккаунты платформы. Заходите в любого, чтобы управлять тарифом, сроком и квотами.</p></div>
          <a class="btn light" href="/analytics">Аналитика оплат →</a></div>
        <table>
          <thead><tr><th>Клиент</th><th>Тариф</th><th>Статус</th><th>Использование</th><th>Оплачено</th><th></th></tr></thead>
          <tbody>{rows}</tbody>
        </table>
        """
        body = integrations
    return f"""<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Оплаты клиентов</title>
  <link rel="icon" type="image/svg+xml" href="/icon.svg">
  <style>{STYLE}</style>{i18n_assets()}
</head>
<body>
  <header class="top"><h1>Биллинг</h1><p>Управление подписками и квотами клиентов.</p>{nav}</header>
  <main class="wrap">
    {f'<div class="card" style="margin-bottom:18px"><b>{esc(message)}</b></div>' if message else ''}
    {body}
  </main>
</body>
</html>"""


def _rub_fmt(n) -> str:
    try:
        return f"{int(round(float(n))):,}".replace(",", " ")
    except (TypeError, ValueError):
        return "0"


def render_analytics(config_path: str, user: dict, query_params: dict | None = None) -> str:
    """Вкладка «Аналитика». Отчёт №1 — финансы по клиентам и выручке."""
    from . import billing
    from .db import list_all_payments
    config = load_config(config_path)
    nav = nav_html("analytics", user)
    conn = connect(config["database"])
    try:
        accounts = list_accounts(conn)
        payments = list_all_payments(conn)
    finally:
        conn.close()
    fin = billing.finance_summary(accounts, payments)

    metrics = "".join([
        metric_card("Выручка всего", _rub_fmt(fin["total_revenue"]) + " ₽", f"{fin['payments_count']} платежей"),
        metric_card("За 30 дней", _rub_fmt(fin["revenue_30d"]) + " ₽", "поступления"),
        metric_card("MRR", _rub_fmt(fin["mrr"]) + " ₽", "ежемесячный доход"),
        metric_card("ARPU", _rub_fmt(fin["arpu"]) + " ₽", "на платящего клиента"),
        metric_card("Платящих", str(fin["paying_active"]), "активных подписок"),
        metric_card("Новые (30д)", str(fin["new_paying_30d"]), "первая оплата"),
        metric_card("Отток (30д)", str(fin["churn_30d"]), "ушедших клиентов"),
        metric_card("Всего аккаунтов", str(fin["total_accounts"]), "включая триалы"),
    ])

    # график выручки по месяцам
    rbm = fin["revenue_by_month"]
    max_rev = max([r["amount"] for r in rbm], default=0) or 1
    bars_html = "".join(
        f'<div class="barline"><span style="width:70px">{esc(r["month"])}</span>'
        f'<div class="track"><div class="fill" style="width:{max(2, round(r["amount"]/max_rev*100))}%"></div></div>'
        f'<b>{_rub_fmt(r["amount"])} ₽</b></div>'
        for r in rbm
    )

    # распределение по тарифам
    plan_rows = "".join(
        f'<div class="row"><span>{esc(billing.plan_title(p))}</span><b>{n}</b></div>'
        for p, n in sorted(fin["by_plan"].items(), key=lambda kv: -kv[1])
    ) or '<span class="muted">нет активных аккаунтов</span>'

    # агрегаты по клиентам
    per_acc = {}
    for p in payments:
        if (p.get("status") or "succeeded") != "succeeded":
            continue
        aid = p.get("account_id")
        agg = per_acc.setdefault(aid, {"total": 0.0, "count": 0, "last": ""})
        agg["total"] += billing._amount(p)
        agg["count"] += 1
        if (p.get("created_at") or "") > agg["last"]:
            agg["last"] = p.get("created_at") or ""
    client_rows = ""
    for a in sorted(accounts, key=lambda x: per_acc.get(x["id"], {}).get("total", 0), reverse=True):
        agg = per_acc.get(a["id"], {"total": 0, "count": 0, "last": ""})
        days = billing.account_days_left(a)
        active = billing.account_is_active(a)
        client_rows += (
            "<tr>"
            f'<td><b>{esc(a.get("name",""))}</b></td>'
            f'<td>{esc(billing.plan_title(a.get("plan")))}</td>'
            f'<td><span class="status {"on" if active else "off"}">{esc(billing.ACCOUNT_STATUSES.get(a.get("status",""), a.get("status","")))}</span></td>'
            f'<td>{esc((a.get("period_end") or "—")[:10])}</td>'
            f'<td>{_rub_fmt(agg["total"])} ₽</td>'
            f'<td>{agg["count"]}</td>'
            f'<td class="muted">{esc((agg["last"] or "—")[:10])}</td>'
            f'<td><a href="/billing?account_id={a["id"]}">Открыть</a></td>'
            "</tr>"
        )
    client_rows = client_rows or '<tr><td colspan="8" class="muted">Клиентов нет.</td></tr>'

    return f"""<!doctype html>
<html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Аналитика — Финансы</title><link rel="icon" type="image/svg+xml" href="/icon.svg"><style>{STYLE}</style>{i18n_assets()}</head>
<body>
  <header class="top"><h1>Аналитика</h1><p>Отчёты по платформе. Текущий отчёт: финансы.</p>{nav}</header>
  <main class="wrap">
    <div class="pagehead"><div><h2>Финансы</h2><p>Выручка, подписки, рост и отток клиентов.</p></div>
      <a class="btn light" href="/billing">← Оплаты клиентов</a></div>
    <section class="metric-grid" style="margin-bottom:18px">{metrics}</section>
    <section class="split">
      <div class="card"><div class="chart-title"><h3>Выручка по месяцам</h3><span>последние 12</span></div>{bars_html}</div>
      <div class="card"><div class="chart-title"><h3>Активные тарифы</h3></div>{plan_rows}</div>
    </section>
    <div class="pagehead" style="margin-top:20px"><div><h2>Клиенты</h2><p>Параметры оплаты по каждому аккаунту.</p></div></div>
    <table>
      <thead><tr><th>Клиент</th><th>Тариф</th><th>Статус</th><th>Оплачено до</th><th>Всего оплачено</th><th>Платежей</th><th>Последний</th><th></th></tr></thead>
      <tbody>{client_rows}</tbody>
    </table>
    <p class="hint" style="margin-top:14px">Это первый отчёт. Дальше добавим: воронку trial→оплата, удержание (retention), разбивку по источникам, активность сбора.</p>
  </main>
</body></html>"""


def render_upgrade(config_path: str, user: dict, message: str = "") -> str:
    """Страница тарифов и онлайн-оплаты для администратора аккаунта."""
    from . import billing
    from .yookassa import yookassa_status
    config = load_config(config_path)
    nav = nav_html("", user)
    conn = connect(config["database"])
    try:
        account = get_account(conn, account_id_of(user))
        usage = account_usage(conn, account_id_of(user)) if account_id_of(user) else {}
    finally:
        conn.close()
    yk_ready = yookassa_status(config)["ready"]
    current_plan = (account or {}).get("plan", "trial")
    days = billing.account_days_left(account)
    current_note = (
        f"Текущий тариф: <b>«{esc(billing.plan_title(current_plan))}»</b>"
        + (f", осталось дней: {days}" if days is not None else "")
        + f". Использование: {usage.get('projects',0)} проектов, {usage.get('queries',0)} запросов, {usage.get('users',0)} польз."
    )
    def _rub(n: int) -> str:
        return f"{n:,}".replace(",", " ")  # неразрывный пробел-разделитель тысяч
    cards = ""
    for key in billing.SELLABLE_PLANS:
        p = billing.plan_def(key)
        month_txt = _rub(p["price"])
        year_txt = _rub(billing.plan_amount(key, 12))
        is_current = key == current_plan
        cards += f"""
        <div class="provider" style="flex:1;min-width:240px">
          <div class="provider-head"><div><h3>{esc(p['title'])}</h3><small>{esc(p.get('blurb',''))}</small></div></div>
          <div style="font-size:28px;font-weight:800;margin:6px 0">{month_txt} ₽<span class="muted" style="font-size:14px;font-weight:500">/мес</span></div>
          <div class="muted" style="margin-bottom:10px">до {p['projects']} проектов · {p['queries']} запросов · {p['users']} польз.</div>
          <form method="post" action="/pay" style="margin:0">
            <input type="hidden" name="plan" value="{key}">
            <div class="bar" style="margin:0;gap:8px">
              <button class="btn" type="submit" name="months" value="1" {'disabled' if not yk_ready else ''}>Месяц · {month_txt} ₽</button>
              <button class="btn light" type="submit" name="months" value="12" {'disabled' if not yk_ready else ''}>Год · {year_txt} ₽</button>
            </div>
          </form>
          {'<div class="coverage-note">это ваш текущий тариф</div>' if is_current else ''}
        </div>
        """
    yk_warn = "" if yk_ready else '<div class="card" style="margin-bottom:14px"><b>Онлайн-оплата временно недоступна.</b> Обратитесь к администратору платформы.</div>'
    return f"""<!doctype html>
<html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Тарифы и оплата</title><link rel="icon" type="image/svg+xml" href="/icon.svg"><style>{STYLE}</style>{i18n_assets()}</head>
<body>
  <header class="top"><h1>Тарифы</h1><p>Выберите план и оплатите онлайн — доступ расширится автоматически.</p>{nav}</header>
  <main class="wrap">
    {f'<div class="card" style="margin-bottom:18px"><b>{esc(message)}</b></div>' if message else ''}
    {yk_warn}
    <div class="card" style="margin-bottom:18px">{current_note}</div>
    <section style="display:flex;gap:16px;flex-wrap:wrap">{cards}</section>
    <p class="hint" style="margin-top:16px">Оплата за год — со скидкой {int(billing.ANNUAL_DISCOUNT*100)}%. Оплата проходит через ЮKassa. После оплаты тариф и срок обновятся автоматически.</p>
  </main>
</body></html>"""


def handle_pay(config_path: str, body: bytes, user: dict) -> tuple[bool, str]:
    """Создаёт онлайн-платёж. Возвращает (ok, confirmation_url | сообщение об ошибке)."""
    from . import billing
    from .yookassa import create_payment
    from .mailer import build_public_url
    form = parse_qs(body.decode("utf-8"))
    account_id = account_id_of(user)
    if not account_id:
        return False, "Не определён аккаунт."
    plan = first_param(form, "plan")
    if plan not in billing.SELLABLE_PLANS:
        return False, "Неизвестный тариф."
    try:
        months = int(first_param(form, "months", "1"))
    except ValueError:
        months = 1
    months = 12 if months >= 12 else 1
    config = load_config(config_path)
    return_url = build_public_url(config, "/billing/return") or "/billing/return"
    return create_payment(config, account_id, plan, months, return_url)


def render_payment_return(config_path: str, user: dict) -> str:
    return render_auth_notice(
        "Оплата обрабатывается",
        "Спасибо! Как только ЮKassa подтвердит платёж (обычно несколько секунд), "
        "тариф и срок подписки обновятся автоматически. Обновите дашборд через минуту.",
        [("/", "На дашборд"), ("/upgrade", "К тарифам")],
    )


def handle_billing_post(config_path: str, body: bytes, user: dict) -> str:
    from . import billing
    form = parse_qs(body.decode("utf-8"))
    action = first_param(form, "action")
    config = load_config(config_path)
    # Платёжные интеграции — уровень платформы, без привязки к аккаунту.
    if action == "save_integrations":
        secrets = load_secrets(config)
        saved = []
        for key in ("YOOKASSA_SHOP_ID", "YOOKASSA_SECRET_KEY"):
            value = first_param(form, key).strip()
            if value:
                secrets[key] = value
                saved.append(key)
        save_secrets(config, secrets)
        return "Ключи ЮKassa сохранены." if saved else "Изменений нет."
    try:
        account_id = int(first_param(form, "account_id", "0"))
    except ValueError:
        account_id = 0
    if not account_id:
        return "Не указан аккаунт."
    conn = connect(config["database"])

    def _int_or_none(name):
        raw = first_param(form, name).strip()
        if not raw:
            return None
        try:
            return max(0, int(raw))
        except ValueError:
            return None

    try:
        account = get_account(conn, account_id)
        if not account:
            return "Аккаунт не найден."
        if action == "save_account":
            plan = first_param(form, "plan", account.get("plan", "trial"))
            status = first_param(form, "status", account.get("status", "trial"))
            period_raw = first_param(form, "period_end").strip()
            period_end = (period_raw + "T00:00:00") if period_raw else None
            update_account(
                conn, account_id,
                name=first_param(form, "name", account.get("name", "")).strip() or account.get("name", ""),
                plan=plan if plan in billing.PLANS else account.get("plan"),
                status=status if status in billing.ACCOUNT_STATUSES else account.get("status"),
                period_end=period_end,
                quota_projects=_int_or_none("quota_projects"),
                quota_queries=_int_or_none("quota_queries"),
                quota_users=_int_or_none("quota_users"),
            )
            return "Аккаунт обновлён."
        if action == "record_payment":
            try:
                amount = float(first_param(form, "amount", "0") or 0)
            except ValueError:
                amount = 0.0
            months = _int_or_none("period_months") or 1
            plan = first_param(form, "plan", account.get("plan", "trial"))
            plan = plan if plan in billing.PLANS else account.get("plan", "trial")
            # продлеваем от большего из «сейчас» и текущего срока
            from datetime import datetime, timezone
            current_end = billing._parse_iso(account.get("period_end"))
            now = datetime.now(timezone.utc)
            start = current_end if (current_end and current_end > now) else now
            new_end = billing.period_end_after(months, start=start)
            record_payment(conn, account_id, amount=amount, plan=plan, provider="manual",
                            period_months=months, note=first_param(form, "note"))
            update_account(conn, account_id, plan=plan, status="active", period_end=new_end)
            return f"Оплата зафиксирована. Тариф «{billing.plan_title(plan)}», оплачено до {new_end[:10]}."
    except Exception as exc:
        return f"Не удалось выполнить действие: {exc}"
    finally:
        conn.close()
    return "Действие не распознано."
