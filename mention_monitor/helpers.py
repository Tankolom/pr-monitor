from __future__ import annotations

import html
import json
import os
import re
from datetime import datetime, timedelta, timezone
from urllib.parse import quote

from . import db  # проекты теперь живут в БД; цикла нет (db не импортирует helpers)

EMOJI_RE = re.compile(
    "["
    "\U0001F1E6-\U0001F1FF"
    "\U0001F300-\U0001F5FF"
    "\U0001F600-\U0001F64F"
    "\U0001F680-\U0001F6FF"
    "\U0001F700-\U0001F77F"
    "\U0001F780-\U0001F7FF"
    "\U0001F800-\U0001F8FF"
    "\U0001F900-\U0001F9FF"
    "\U0001FA00-\U0001FAFF"
    "\u2600-\u26FF"
    "\u2700-\u27BF"
    "]+",
    flags=re.UNICODE,
)

VK_REDIRECT_URI = os.getenv(
    "VK_REDIRECT_URI",
    "https://109-235-117-6.sslip.io/vk-oauth-callback",
)

UI_TRANSLATIONS = {
    "en": {
        "Мониторинг упоминаний": "Mention monitoring",
        "Дашборд": "Dashboard",
        "ИИ-анализ": "AI analysis",
        "Проекты": "Projects",
        "Скачать Excel": "Export Excel",
        "Админ-панель": "Admin panel",
        "Источники и интеграции": "Sources & integrations",
        "Оплаты клиентов": "Client billing",
        "Аналитика": "Analytics",
        "Выйти": "Log out",
        "админ": "admin",
        "пользователь": "user",
        "Премиальная система мониторинга": "Premium monitoring platform",
        "СМИ и соцсети": "Media and social platforms",
        "Одна рабочая лента публикаций, дублей и цитируемости по проекту.": "One working feed of mentions, duplicates, and citation patterns for the project.",
        "Премиальная панель для мониторинга СМИ: упоминания, динамика, тональность, перепечатки и ИИ-анализ по истории проекта.": "Premium dashboard for media monitoring: mentions, trends, sentiment, reprints, and AI analysis across project history.",
        "Аналитика под клиента": "Client-ready analytics",
        "Дашборд, Excel-отчёты и ИИ-разбор истории упоминаний.": "Dashboard, Excel reports, and AI analysis of the mention history.",
        "Командный доступ": "Team access",
        "Личные кабинеты, роли, проекты и разделение клиентских данных.": "Personal accounts, roles, projects, and separation of client data.",
        "Единый вход": "Unified access",
        "Почта, подтверждение доступа, восстановление пароля и управление аккаунтом.": "Email, access confirmation, password recovery, and account management.",
        "медиамониторинг для агентств, PR и маркетинга": "media monitoring for agencies, PR, and marketing",
        "Вход в рабочий кабинет": "Sign in to your workspace",
        "Войдите в сервис, чтобы открыть проекты, историю упоминаний, ИИ-анализ и отчётность.": "Sign in to access projects, mention history, AI analysis, and reporting.",
        "Вход": "Sign in",
        "Используйте логин администратора или email, который пришёл вам в письме с доступом.": "Use the admin login or the email address from your access invitation.",
        "Логин или email": "Login or email",
        "Пароль": "Password",
        "Войти в кабинет": "Open workspace",
        "Зарегистрироваться": "Create account",
        "Не помню пароль": "Forgot password",
        "Если кабинет вам создаёт администратор, письмо с данными для входа придёт на указанную почту.": "If an administrator creates your account, your login details will be sent to the specified email address.",
        "Создайте кабинет в PR Monitor": "Create your PR Monitor account",
        "После регистрации сервис отправит письмо с временным паролем и ссылкой для подтверждения почты.": "After registration, the service will send a temporary password and an email confirmation link.",
        "Регистрация": "Registration",
        "Укажите рабочую почту. Логином для входа станет этот email.": "Enter your work email. This email will become your login.",
        "Имя или компания": "Name or company",
        "Рабочий email": "Work email",
        "Получить доступ": "Get access",
        "Уже есть доступ": "Already have access",
        "Восстановить пароль": "Recover password",
        "Восстановление пароля": "Password recovery",
        "Введите почту, и мы отправим ссылку для создания нового пароля.": "Enter your email and we will send you a link to create a new password.",
        "Сброс пароля": "Reset password",
        "Письмо придёт на тот адрес, который привязан к кабинету.": "The email will be sent to the address linked to the account.",
        "Email": "Email",
        "Отправить ссылку": "Send link",
        "Вернуться ко входу": "Back to sign in",
        "Создать кабинет": "Create account",
        "Новый пароль": "New password",
        "Задайте новый пароль для входа в кабинет.": "Set a new password for signing in.",
        "После сохранения вы сразу сможете войти в систему.": "You will be able to sign in immediately after saving it.",
        "Повторите пароль": "Repeat password",
        "Сохранить пароль": "Save password",
        "PR Monitor": "PR Monitor",
        "media intelligence": "media intelligence",
        "Командный центр проекта": "Project command center",
        "Выберите проект": "Choose project",
        "Текущий проект": "Current project",
        "Настроить проект": "Configure project",
        "Показать": "Show",
        "Открыть проект": "Open project",
        "Разобрать с ИИ": "Analyze with AI",
        "Новый проект": "New project",
        "Источники": "Sources",
        "API (JSON) для интеграций ↗": "API (JSON) for integrations ↗",
        "Машинно-читаемые данные выборки (JSON) для интеграций — CRM, BI, боты. Те же фильтры, что на экране.": "Machine-readable result data (JSON) for integrations — CRM, BI, bots. Uses the same filters as on screen.",
        "Повысить тариф ↗": "Upgrade plan ↗",
        "Собрать упоминания": "Collect mentions",
        "Идёт сбор…": "Collecting…",
        "Поиск внутри выборки": "Search within results",
        "Сбор с": "Collected from",
        "по": "to",
        "вся тональность": "all sentiment",
        "в выбранном фильтре": "in the selected filter",
        "уникальные площадки": "unique sources",
        "к прошлому периоду": "vs previous period",
        "репутационный фон": "reputation background",
        "Упоминания": "Mentions",
        "Динамика": "Trend",
        "Позитив": "Positive",
        "Негатив": "Negative",
        "Риск": "Risk",
        "Нет данных": "No data",
        "Сбор упоминаний": "Mention collection",
        "последний запуск:": "last run:",
        "Яндекс · Google/Serper · Google News · GDELT · RSS": "Yandex · Google/Serper · Google News · GDELT · RSS",
        "Период": "Period",
        "Глубина": "Depth",
        "Расширять поисковые формулировки": "Expand search wording",
        "Читать страницы полностью": "Read full pages",
        "Аналитические панели": "Analytics panels",
        "Динамика, источники, тональность, цитируемость и рабочие PR-метрики.": "Trends, sources, sentiment, citation, and practical PR metrics.",
        "Лента публикаций": "Publication feed",
        "Доказательная база, из которой строятся графики и выводы.": "The evidence base used to build charts and conclusions.",
        "Топ источников": "Top sources",
        "Проекты": "Projects",
        "проекты": "projects",
        "запросы": "queries",
        "сбор:": "collection:",
        "Тариф": "Plan",
        "Готов к запуску": "Ready to start",
        "После запуска здесь появится ход выполнения и результат.": "Collection progress and the result will appear here after launch.",
        "Запускаем сбор": "Starting collection",
        "Подготавливаем источники и поисковые запросы.": "Preparing sources and search queries.",
        "Собираем публикации": "Collecting publications",
        "Сбор завершён": "Collection finished",
        "Проверьте написание названия и поисковые фразы проекта.": "Check the project name spelling and search phrases.",
        "Сбор завершился с ошибкой": "Collection finished with an error",
        "Не удалось получить данные от источников.": "Could not get data from sources.",
        "Не удалось проверить состояние": "Could not check status",
        "Обновите страницу и попробуйте ещё раз.": "Refresh the page and try again.",
        "Не удалось запустить сбор": "Could not start collection",
        "Сервер не принял задачу.": "The server did not accept the task.",
        "Проверьте соединение и попробуйте снова.": "Check the connection and try again.",
        "Проект: ": "Project: ",
        "прошло ": "elapsed ",
        "Найдено: ": "Found: ",
        " · добавлено новых: ": " · newly added: ",
        "Открыть темы": "Open topics",
        "Сохранить проект": "Save project",
        "Смотреть статистику": "View analytics",
        "Что искать": "What to search for",
        "Название проекта": "Project name",
        "Язык проекта": "Project language",
        "Рынок / регион": "Market / region",
        "Создать проект прямо здесь": "Create a project right here",
        "Создайте проект и сразу задайте язык мониторинга и рынок, на котором будем искать упоминания.": "Create a project and immediately set the monitoring language and the market where mentions should be searched.",
        "Создать и открыть": "Create and open",
        "Для нового проекта можно оставить одно название — сервис сам создаст первый поисковый запрос.": "For a new project you can leave only the name — the service will create the first search query automatically.",
        "Сайт": "Website",
        "Город / регион": "City / region",
        "Сфера деятельности": "Industry",
        "Альтернативные названия": "Alternative names",
        "Телефон": "Phone",
        "Адрес": "Address",
        "Соцсети и каналы бренда": "Brand social channels",
        "Подсказка для ИИ-фильтра релевантности": "Prompt for AI relevance filter",
        "Русский": "Russian",
        "Английский": "English",
        "Россия": "Russia",
        "Казахстан": "Kazakhstan",
        "Весь мир": "Worldwide",
        "Заполнить профиль из интернета": "Fill profile from the web",
        "Сгенерировать запросы и подсказку из профиля": "Generate queries and prompt from profile",
        "Предложить запросы": "Suggest queries",
        "URL страниц и каталогов": "Page and directory URLs",
        "Частота сбора": "Collection frequency",
        "Удалить проект": "Delete project",
        "Пока нет данных. Нажмите «Собрать упоминания».": "No data yet. Click “Collect mentions”.",
        "Открыть": "Open",
        "Запросы, которые дают результат": "Queries that bring results",
        "Полные формулировки, количество найденных публикаций и переход к ленте.": "Full query wording, number of found publications, and a shortcut to the feed.",
        "Показать публикации": "Show publications",
        "Пока нет данных по запросам.": "No query data yet.",
        "среди топ-запросов": "among top queries",
        "без запроса": "without query",
        "позитив": "positive",
        "негатив": "negative",
        "нейтрально": "neutral",
        "последние 24 часа": "last 24 hours",
        "3 дня": "3 days",
        "7 дней": "7 days",
        "14 дней": "14 days",
        "30 дней": "30 days",
        "60 дней": "60 days",
        "90 дней": "90 days",
        "быстрый": "fast",
        "стандартный": "standard",
        "глубокий": "deep",
    }
}


def _language_switcher_html(compact: bool = False) -> str:
    cls = "lang-switch compact" if compact else "lang-switch"
    return (
        f'<div class="{cls}" aria-label="Language selector">'
        '<button type="button" data-lang="ru">RU</button>'
        '<button type="button" data-lang="en">EN</button>'
        "</div>"
    )


def i18n_assets() -> str:
    translations = json.dumps(UI_TRANSLATIONS, ensure_ascii=False)
    return f"""
<style>
.lang-switch{{display:inline-flex;align-items:center;gap:4px;padding:4px;border:1px solid rgba(209,221,228,.92);border-radius:999px;background:rgba(255,255,255,.86);box-shadow:0 8px 24px rgba(16,47,58,.07)}}
.lang-switch button{{border:0;background:transparent;color:#61747d;font:600 12px/1 -apple-system,BlinkMacSystemFont,"SF Pro Display","Inter",sans-serif;padding:7px 12px;border-radius:999px;cursor:pointer;transition:all .15s ease}}
.lang-switch button.active{{background:#102f3a;color:#fff;box-shadow:0 6px 16px rgba(16,47,58,.14)}}
.lang-switch.compact{{margin-top:6px}}
.nav-lang{{padding:0 4px 2px}}
.auth-lang{{position:absolute;top:24px;right:24px;z-index:2}}
@media (max-width: 840px){{.auth-lang{{top:16px;right:16px}}}}
</style>
<script>
(function(){{
  const translations = {translations};
  const STORAGE_KEY = 'uiLang';
  const COOKIE_KEY = 'ui_lang';
  window.__prTranslations = translations;

  function readLang(){{
    const cookieMatch = document.cookie.match(/(?:^|; )ui_lang=([^;]+)/);
    return localStorage.getItem(STORAGE_KEY) || (cookieMatch ? decodeURIComponent(cookieMatch[1]) : '') || 'ru';
  }}

  function saveLang(lang){{
    localStorage.setItem(STORAGE_KEY, lang);
    document.cookie = COOKIE_KEY + '=' + encodeURIComponent(lang) + '; path=/; max-age=31536000; SameSite=Lax';
  }}

  function replaceExact(value, map){{
    if (!value) return value;
    const trimmed = value.trim();
    const translated = map[trimmed];
    if (!translated) return value;
    const start = value.match(/^\\s*/)[0];
    const end = value.match(/\\s*$/)[0];
    return start + translated + end;
  }}

  function applyLanguage(lang){{
    const map = translations[lang] || {{}};
    window.__uiLang = lang;
    document.documentElement.lang = lang;
    document.querySelectorAll('.lang-switch button').forEach((button) => {{
      button.classList.toggle('active', button.dataset.lang === lang);
    }});
    if (lang === 'ru') {{
      if (window.__prOriginalTitle) document.title = window.__prOriginalTitle;
      document.querySelectorAll('[data-pr-original-text]').forEach((el) => {{
        el.textContent = el.getAttribute('data-pr-original-text');
      }});
      document.querySelectorAll('[data-pr-original-placeholder]').forEach((el) => {{
        el.setAttribute('placeholder', el.getAttribute('data-pr-original-placeholder'));
      }});
      document.querySelectorAll('[data-pr-original-aria-label]').forEach((el) => {{
        el.setAttribute('aria-label', el.getAttribute('data-pr-original-aria-label'));
      }});
      document.querySelectorAll('[data-pr-original-title]').forEach((el) => {{
        el.setAttribute('title', el.getAttribute('data-pr-original-title'));
      }});
      document.querySelectorAll('[data-pr-original-tip]').forEach((el) => {{
        el.setAttribute('data-tip', el.getAttribute('data-pr-original-tip'));
      }});
      return;
    }}
    if (!window.__prOriginalTitle) window.__prOriginalTitle = document.title;
    document.title = map[document.title] || document.title;

    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, {{
      acceptNode(node) {{
        if (!node.nodeValue || !node.nodeValue.trim()) return NodeFilter.FILTER_REJECT;
        const parent = node.parentElement;
        if (!parent) return NodeFilter.FILTER_REJECT;
        if (['SCRIPT','STYLE','TEXTAREA'].includes(parent.tagName)) return NodeFilter.FILTER_REJECT;
        return NodeFilter.FILTER_ACCEPT;
      }}
    }});
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    nodes.forEach((node) => {{
      if (!node.parentElement.hasAttribute('data-pr-original-text')) {{
        node.parentElement.setAttribute('data-pr-original-text', node.textContent);
      }}
      node.textContent = replaceExact(node.parentElement.getAttribute('data-pr-original-text'), map);
    }});

    document.querySelectorAll('[placeholder]').forEach((el) => {{
      if (!el.hasAttribute('data-pr-original-placeholder')) {{
        el.setAttribute('data-pr-original-placeholder', el.getAttribute('placeholder') || '');
      }}
      const original = el.getAttribute('data-pr-original-placeholder') || '';
      el.setAttribute('placeholder', map[original] || original);
    }});

    document.querySelectorAll('[aria-label]').forEach((el) => {{
      if (!el.hasAttribute('data-pr-original-aria-label')) {{
        el.setAttribute('data-pr-original-aria-label', el.getAttribute('aria-label') || '');
      }}
      const original = el.getAttribute('data-pr-original-aria-label') || '';
      el.setAttribute('aria-label', map[original] || original);
    }});

    document.querySelectorAll('[title]').forEach((el) => {{
      if (!el.hasAttribute('data-pr-original-title')) {{
        el.setAttribute('data-pr-original-title', el.getAttribute('title') || '');
      }}
      const original = el.getAttribute('data-pr-original-title') || '';
      el.setAttribute('title', map[original] || original);
    }});

    document.querySelectorAll('[data-tip]').forEach((el) => {{
      if (!el.hasAttribute('data-pr-original-tip')) {{
        el.setAttribute('data-pr-original-tip', el.getAttribute('data-tip') || '');
      }}
      const original = el.getAttribute('data-pr-original-tip') || '';
      el.setAttribute('data-tip', map[original] || original);
    }});
  }}

  function setup(){{
    window.__uiT = function(value){{
      const lang = window.__uiLang || readLang();
      const map = translations[lang] || {{}};
      return map[value] || value;
    }};
    document.querySelectorAll('.lang-switch button').forEach((button) => {{
      button.addEventListener('click', function() {{
        const lang = this.dataset.lang || 'ru';
        saveLang(lang);
        applyLanguage(lang);
      }});
    }});
    applyLanguage(readLang());
  }}

  if (document.readyState === 'loading') {{
    document.addEventListener('DOMContentLoaded', setup);
  }} else {{
    setup();
  }}
}})();
</script>
"""


def strip_emoji(value: str) -> str:
    return EMOJI_RE.sub("", value)


def esc(value) -> str:
    return html.escape(strip_emoji("" if value is None else str(value)))


def render_ai_text(text: str) -> str:
    lines = []
    for raw_line in (text or "").strip().splitlines():
        line = esc(raw_line.strip())
        if not line:
            continue
        line = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", line)
        lines.append(f"<p>{line}</p>")
    return "".join(lines) or "<p class='hint'>Ответ пустой.</p>"


def sentiment_ru(value: str) -> str:
    return {"positive": "позитив", "negative": "негатив", "neutral": "нейтрально"}.get(value, value)


def first_param(query_params: dict, name: str, default: str = "") -> str:
    return query_params.get(name, [default])[0].strip()


def first_int(query_params: dict, name: str, default: int, allowed: set[int] | None = None) -> int:
    try:
        value = int(query_params.get(name, [str(default)])[0])
    except (TypeError, ValueError):
        value = default
    if allowed and value not in allowed:
        return default
    return value


def user_role_label(user: dict | None) -> str:
    if not user:
        return ""
    return "админ" if user["role"] == "admin" else "пользователь"


def nav_html(active: str, user: dict | None, extra_report_href: str = "") -> str:
    items = [
        ("dashboard", "/", "Дашборд"),
        ("agent", "/agent", "ИИ-анализ"),
        ("topics", "/topics", "Проекты"),
    ]
    if extra_report_href:
        items.append(("report", extra_report_href, "Скачать Excel"))
    if user and user["role"] == "admin":
        items.append(("admin", "/admin", "Админ-панель"))
    _superadmin = False
    try:
        _superadmin = bool(user["is_superadmin"]) if user else False
    except (KeyError, IndexError, TypeError):
        _superadmin = False
    if _superadmin:
        # Глобальные интеграции/секреты платформы — только суперадмину
        items.append(("settings", "/settings", "Источники и интеграции"))
        items.append(("billing", "/billing", "Оплаты клиентов"))
        items.append(("analytics", "/analytics", "Аналитика"))
    links = "".join(
        f'<a class="{"active" if active == key else ""}" href="{esc(href)}"><span class="nav-ico">{nav_icon(key)}</span><span class="nav-label">{esc(label)}</span></a>'
        for key, href, label in items
    )
    user_block = ""
    if user:
        user_block = (
            '<div class="nav-user">'
            '<span class="nav-avatar">A</span>'
            f'<span class="nav-label"><b>{esc(user["username"])}</b><small>{esc(user_role_label(user))}</small></span>'
            '</div>'
            f'<a class="logout" href="/logout"><span class="nav-ico">{nav_icon("logout")}</span><span class="nav-label">Выйти</span></a>'
        )
    return (
        '<button class="sidebar-toggle" type="button" aria-label="Свернуть меню" onclick="document.body.classList.toggle(\'sidebar-collapsed\');localStorage.setItem(\'sidebarCollapsed\',document.body.classList.contains(\'sidebar-collapsed\')?\'1\':\'0\')">'
        '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 7h14M5 12h14M5 17h14"/></svg></button>'
        f"{i18n_assets()}"
        '<nav class="nav" aria-label="Основная навигация">'
        '<div class="nav-brand"><span class="brand-mark">PR</span><span class="nav-label"><b>PR Monitor</b><small>media intelligence</small></span></div>'
        f'<div class="nav-links">{links}</div><div class="nav-lang">{_language_switcher_html(True)}</div>'
        f'<div class="nav-bottom">{user_block}</div>'
        '</nav>'
        '<script>document.body.classList.add("with-sidebar");if(localStorage.getItem("sidebarCollapsed")==="1"){document.body.classList.add("sidebar-collapsed")}</script>'
    )


def nav_icon(key: str) -> str:
    return {
        "dashboard": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 11.5 12 4l9 7.5"/><path d="M5.5 10.5V20h13v-9.5"/><path d="M9.5 20v-5h5v5"/></svg>',
        "agent": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8L12 3Z"/><path d="M19 15l.8 2.2L22 18l-2.2.8L19 21l-.8-2.2L16 18l2.2-.8L19 15Z"/></svg>',
        "topics": '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="3"/><path d="M12 2v2M12 20v2M2 12h2M20 12h2"/></svg>',
        "settings": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8Z"/><path d="M4 12h2M18 12h2M12 4v2M12 18v2M6.3 6.3l1.4 1.4M16.3 16.3l1.4 1.4M17.7 6.3l-1.4 1.4M7.7 16.3l-1.4 1.4"/></svg>',
        "report": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 4v11"/><path d="m8 11 4 4 4-4"/><path d="M5 20h14"/></svg>',
        "admin": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3 5 6v5c0 4.6 2.9 8 7 10 4.1-2 7-5.4 7-10V6l-7-3Z"/><path d="M9.5 12.2 11.2 14l3.5-4"/></svg>',
        "billing": '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="6" width="18" height="12" rx="2"/><path d="M3 10h18"/><path d="M7 15h4"/></svg>',
        "analytics": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 20V4"/><path d="M4 20h16"/><rect x="7" y="12" width="3" height="5"/><rect x="12" y="8" width="3" height="9"/><rect x="17" y="5" width="3" height="12"/></svg>',
        "logout": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M10 17 5 12l5-5"/><path d="M5 12h12"/><path d="M14 5h4a1 1 0 0 1 1 1v12a1 1 0 0 1-1 1h-4"/></svg>',
    }.get(key, '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="3"/></svg>')


def _account_id(user: dict | None) -> int | None:
    """ID аккаунта пользователя (тенант). Для строки sqlite и dict работает одинаково."""
    if not user:
        return None
    try:
        return user["account_id"]
    except (KeyError, IndexError, TypeError):
        return None


def _is_account_admin(user: dict | None) -> bool:
    """Видит «все проекты» аккаунта и опции уровня аккаунта (admin или суперадмин)."""
    if not user:
        return False
    try:
        if user["is_superadmin"]:
            return True
    except (KeyError, IndexError, TypeError):
        pass
    try:
        return user["role"] == "admin"
    except (KeyError, IndexError, TypeError):
        return False


def ensure_project_owners(config: dict, default_owner: str = "admin") -> bool:
    """Проекты и владельцы теперь хранятся в БД и проставляются при создании.
    Оставлено как no-op для обратной совместимости вызовов."""
    return False


def visible_projects(config: dict, user: dict | None) -> list[dict]:
    """Проекты аккаунта пользователя. Все участники аккаунта видят все его проекты."""
    account_id = _account_id(user)
    if not account_id:
        return []
    conn = db.connect(config["database"])
    try:
        return db.list_projects(conn, account_id)
    finally:
        conn.close()


def project_is_visible(config: dict, user: dict | None, project_name: str) -> bool:
    if not user:
        return False
    return any(project.get("name") == project_name for project in visible_projects(config, user))


def account_id_of(user: dict | None) -> int | None:
    """Публичный доступ к ID аккаунта пользователя (для скоупинга запросов к БД)."""
    return _account_id(user)


def default_project_name(config: dict, user: dict | None, fallback: str = "all") -> str:
    """Имя первого доступного проекта или fallback — замена прежнего
    config['projects'][0]['name'] при выборе проекта по умолчанию."""
    projects = visible_projects(config, user) if user else []
    if projects:
        return projects[0].get("name", fallback)
    return fallback


def normalize_project_filter(config: dict, user: dict | None, requested: str) -> str:
    projects = visible_projects(config, user)
    if _is_account_admin(user):
        return requested or "all"
    if requested and requested != "all" and project_is_visible(config, user, requested):
        return requested
    if projects:
        return projects[0].get("name", "")
    return "__no_access__"


def report_query(sentiment_filter: str, search: str, collected_from: str, collected_to: str, project: str = "") -> str:
    parts = []
    if project and project != "all":
        parts.append(f"project={quote(project)}")
    if sentiment_filter and sentiment_filter != "all":
        parts.append(f"sentiment={sentiment_filter}")
    if search:
        parts.append(f"q={search}")
    if collected_from:
        parts.append(f"collected_from={collected_from}")
    if collected_to:
        parts.append(f"collected_to={collected_to}")
    return ("?" + "&".join(parts)) if parts else ""


def query_href(path: str, params: dict) -> str:
    parts = []
    for key, value in params.items():
        if value is None:
            continue
        value = str(value)
        if value == "":
            continue
        parts.append(f"{quote(str(key))}={quote(value)}")
    return path + (("?" + "&".join(parts)) if parts else "")


def bars(title: str, rows, label_key: str, value_key: str, cls: str = "", href_key: str = "", query_params: dict | None = None) -> str:
    max_value = max([int(row[value_key]) for row in rows], default=0) or 1
    body = ""
    params = query_params or {}
    for row in rows:
        value = int(row[value_key])
        width = max(3, round(value / max_value * 100))
        label = esc(row[label_key])
        if href_key:
            href = query_href("/", {**params, "q": row[href_key], "feed_page": ""}) + "#feed"
            label_html = f"<a href='{esc(href)}'>{label}</a>"
        else:
            label_html = f"<span>{label}</span>"
        body += (
            f"<div class='barline'>{label_html}"
            f"<div class='track'><div class='fill {cls}' style='width:{width}%'></div></div><b>{value}</b></div>"
        )
    empty = "<span class='muted'>нет данных</span>"
    return f"<div class='card'><h3>{esc(title)}</h3>{body or empty}</div>"


def query_performance_panel(rows, query_params: dict | None = None) -> str:
    params = query_params or {}
    total = sum(int(row["n"]) for row in rows) or 0
    max_value = max([int(row["n"]) for row in rows], default=0) or 1
    items = []
    for index, row in enumerate(rows, start=1):
        query = str(row["query"] or "").strip() or "без запроса"
        count = int(row["n"])
        width = max(4, round(count / max_value * 100))
        share = pct(count, total)
        href = query_href("/", {**params, "q": query, "feed_page": ""}) + "#feed"
        open_attr = " open" if index == 1 else ""
        items.append(
            "<details class='query-hit'"
            + open_attr
            + ">"
            + "<summary>"
            + f"<span class='query-rank'>{index}</span>"
            + f"<span class='query-title'>{esc(query)}</span>"
            + f"<b class='query-count'>{count}</b>"
            + "</summary>"
            + "<div class='query-hit-detail'>"
            + "<div class='query-progress'>"
            + f"<i style='width:{width}%'></i>"
            + "</div>"
            + f"<span>{share}% <i>среди топ-запросов</i></span>"
            + f"<a href='{esc(href)}'>Показать публикации</a>"
            + "</div>"
            + "</details>"
        )
    if not items:
        body = "<span class='muted'>Пока нет данных по запросам.</span>"
    else:
        body = "".join(items)
    return (
        "<div class='card query-performance'>"
        "<div class='chart-title'><div><h3>Запросы, которые дают результат</h3>"
        "<span>Полные формулировки, количество найденных публикаций и переход к ленте.</span></div></div>"
        f"<div class='query-hit-list'>{body}</div>"
        "</div>"
    )


def pct(value: int, total: int) -> int:
    return round(value / total * 100) if total else 0


def metric_card(label: str, value: str | int, caption: str, href: str = "") -> str:
    value_text = str(value).strip()
    # «Числовое» значение — только если это целиком число/процент (напр. «67%», «1 234», «+5%»),
    # а не фраза, в которой просто встречается цифра (напр. «резкий рост (было 1)»).
    is_numeric = bool(re.fullmatch(r"[+\-]?[\d\s.,]+%?", value_text))
    if not is_numeric and value_text:
        value_text = value_text[:1].upper() + value_text[1:]
    if is_numeric:
        value_class = "value value-numeric"
    elif len(value_text) > 13:
        value_class = "value value-text value-long"  # длинная фраза — мельче и переносится
    else:
        value_class = "value value-text"
    inner = f"<div class='k'>{esc(label)}</div><div class='{value_class}'>{esc(value_text)}</div><div class='caption'>{esc(caption)}</div>"
    if href:
        return f"<a class='metric metric-link' href='{esc(href)}'>{inner}</a>"
    return f"<div class='metric'>{inner}</div>"


def project_options(config: dict, selected: str, user: dict | None = None) -> str:
    names = []
    projects = visible_projects(config, user) if user else []
    for project in projects:
        name = project.get("name", "").strip()
        if name and name not in names:
            names.append(name)
    options = []
    if user is None or _is_account_admin(user):
        options.append(f'<option value="all" {"selected" if selected in {"", "all"} else ""}>все проекты</option>')
    options += [f'<option value="{esc(name)}" {"selected" if selected == name else ""}>{esc(name)}</option>' for name in names]
    return "".join(options) or '<option value="">нет доступных проектов</option>'


def project_by_name(config: dict, name: str, user: dict | None = None) -> dict:
    """Проект по имени в рамках аккаунта пользователя. Если проектов нет —
    непустой каркас нового проекта (НЕ пишется в БД до сохранения формы)."""
    projects = visible_projects(config, user) if user else []
    for project in projects:
        if project.get("name") == name:
            return project
    if projects:
        return projects[0]
    owner = (user or {}).get("username", "admin") if user else "admin"
    return new_project_data(config, "Новый проект", [], owner)


def blank_brand_profile() -> dict:
    return {
        "website": "",
        "city": "",
        "industry": "",
        "aliases": "",
        "phone": "",
        "address": "",
        "social_links": [],
    }


def new_project_data(config: dict, name: str, queries: list[str], owner: str) -> dict:
    """Каркас нового (ещё не сохранённого) проекта. id отсутствует — признак «новый»."""
    cleaned_queries = [query.strip() for query in queries if str(query).strip()]
    return {
        "id": None,
        "name": (name or "Новый проект").strip() or "Новый проект",
        "queries": cleaned_queries,
        "control_urls": [],
        "language": "ru",
        "region": "RU",
        "owner": owner,
        "brand": blank_brand_profile(),
        "relevance_hint": "",
        "schedule_enabled": False,
        "schedule_interval_hours": 3,
        "last_collected_at": None,
    }


def create_project(config: dict, name: str, queries: list[str], user: dict) -> dict:
    """Создаёт проект в БД под аккаунтом пользователя и возвращает его dict."""
    conn = db.connect(config["database"])
    try:
        return db.create_project_row(
            conn,
            account_id=_account_id(user),
            name=name,
            queries=queries,
            owner=(user or {}).get("username", ""),
        )
    finally:
        conn.close()


def project_summary_cards(config: dict, selected: str, user: dict | None = None) -> str:
    cards = ""
    projects = visible_projects(config, user) if user else []
    for project in projects:
        name = project.get("name", "Без названия")
        queries = project.get("queries", [])
        active = " active" if name == selected else ""
        preview = ", ".join(queries[:2]) if queries else "запросы еще не заданы"
        owner = f" · владелец: {project.get('owner')}" if user and user["role"] == "admin" else ""
        cards += f"""
        <a class="project-card{active}" href="/topics?project={quote(name)}">
          <b>{esc(name)}</b>
          <span>{len(queries)} запросов · {len(project.get('control_urls', []))} URL{esc(owner)}</span>
          <small>{esc(preview)}</small>
        </a>
        """
    return cards or '<span class="muted">Проектов пока нет.</span>'


SOURCE_HINTS = {
    "google_news": "новости и СМИ",
    "gdelt_news": "глобальный индекс новостей",
    "newsdata": "платный news API",
    "serper_google": "Google-выдача",
    "yandex_search": "Яндекс-выдача",
    "google_custom_search": "Google Custom Search",
    "vk_search": "публичные посты VK",
    "web_pages": "контрольные URL",
    "rss": "федеральные и региональные RSS",
    "site_search": "поиск по площадкам (Telegram, Dzen, OK, видео, отзовики)",
}


def source_label(source: dict) -> str:
    labels = {
        "google_news": "Google News",
        "gdelt_news": "GDELT",
        "newsdata": "NewsData.io",
        "serper_google": "Google через Serper",
        "yandex_search": "Яндекс",
        "google_custom_search": "Google Custom",
        "vk_search": "VK",
        "web_pages": "Контрольные страницы",
        "rss": "Новостные СМИ",
        "site_search": "Поиск по площадкам",
    }
    return labels.get(source.get("type"), source.get("name") or source.get("type") or "Источник")


def collect_source_options(config: dict) -> str:
    options = []
    seen = set()
    for source in config.get("sources", []):
        source_type = source.get("type")
        if not source_type or source_type in seen:
            continue
        seen.add(source_type)
        enabled = source.get("enabled", True)
        disabled = "" if enabled else " disabled"
        checked = " checked" if enabled else ""
        css = "source-check" + ("" if enabled else " disabled")
        hint = SOURCE_HINTS.get(source_type, source.get("name", ""))
        status = "готов к сбору" if enabled else "выключен в настройках"
        options.append(
            f"""
            <label class="{css}">
              <input type="checkbox" name="source_types" value="{esc(source_type)}"{checked}{disabled}>
              <span><b>{esc(source_label(source))}</b><small>{esc(hint)} · {esc(status)}</small></span>
            </label>
            """
        )
    return f"""
    <div class="source-picker">
      <div class="source-picker-head"><b>Где искать в этом запуске</b><span>Отметьте площадки, которые нужно опросить прямо сейчас.</span></div>
      <div class="source-checks">{''.join(options) or '<span class="muted">источники не настроены</span>'}</div>
    </div>
    """


def period_options() -> str:
    options = [
        ("1d", "последние 24 часа"),
        ("3d", "3 дня"),
        ("7d", "7 дней"),
        ("14d", "14 дней"),
        ("30d", "30 дней"),
        ("60d", "60 дней"),
        ("90d", "90 дней"),
    ]
    return "".join(f'<option value="{value}" {"selected" if value == "30d" else ""}>{label}</option>' for value, label in options)


def depth_options() -> str:
    # Подпись в самой опции поясняет смысл уровня — пользователю не нужно гадать.
    options = [
        ("fast", "быстрый — меньше источников и страниц, результат за секунды"),
        ("standard", "стандартный — баланс охвата и скорости (рекомендуется)"),
        ("deep", "глубокий — максимум источников и чтение страниц, дольше"),
    ]
    return "".join(f'<option value="{value}" {"selected" if value == "standard" else ""}>{label}</option>' for value, label in options)


def compact_number(value: int | float) -> str:
    value = int(round(value or 0))
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f}".replace(".", ",") + " млн"
    if value >= 10_000:
        return f"{round(value / 1000)} тыс."
    if value >= 1_000:
        return f"{value / 1000:.1f}".replace(".", ",") + " тыс."
    return str(value)


def parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        normalized = value.replace("Z", "+00:00")
        if len(normalized) == 10:
            normalized += "T00:00:00+00:00"
        dt = datetime.fromisoformat(normalized)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except ValueError:
        return None


def display_date(value: str | None, fallback: str = "нет даты") -> str:
    dt = parse_dt(value)
    return dt.strftime("%d/%m/%Y") if dt else fallback


def display_datetime(value: str | None, fallback: str = "нет даты") -> str:
    dt = parse_dt(value)
    return dt.strftime("%d/%m/%Y %H:%M") if dt else fallback


def display_period(value: str | None, bucket: str, fallback: str = "нет даты") -> str:
    value = value or ""
    dt = parse_dt(value)
    if bucket == "day":
        return dt.strftime("%d/%m") if dt else fallback
    if bucket == "month":
        match = re.match(r"(\d{4})-(\d{2})", value)
        if match:
            year, month = match.groups()
            month_name = [
                "",
                "январь",
                "февраль",
                "март",
                "апрель",
                "май",
                "июнь",
                "июль",
                "август",
                "сентябрь",
                "октябрь",
                "ноябрь",
                "декабрь",
            ][int(month)]
            return f"{month_name} {year}"
        return dt.strftime("%m/%Y") if dt else fallback
    if bucket == "week":
        match = re.match(r"(\d{4})-W(\d{1,2})", value)
        if match:
            year, week = match.groups()
            return f"{week.zfill(2)}/{year}"
    return value or fallback


def today_iso() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def default_from_iso(days: int = 90) -> str:
    return (datetime.now(timezone.utc).date() - timedelta(days=days - 1)).isoformat()


def parse_date_only(value: str | None):
    try:
        return datetime.fromisoformat((value or "")[:10]).date()
    except ValueError:
        return None


def add_months(dt, months: int):
    month = dt.month - 1 + months
    year = dt.year + month // 12
    month = month % 12 + 1
    return dt.replace(year=year, month=month, day=1)


def period_key_for_date(dt, bucket: str) -> str:
    if bucket == "month":
        return f"{dt.year}-{dt.month:02d}"
    if bucket == "week":
        return f"{dt.year}-W{int(dt.strftime('%W')):02d}"
    return dt.isoformat()


def complete_period_rows(rows, key_name: str, bucket: str, start_iso: str, end_iso: str) -> list[dict]:
    start = parse_date_only(start_iso) or parse_date_only(default_from_iso())
    end = parse_date_only(end_iso) or parse_date_only(today_iso())
    if not start or not end:
        return [dict(row) for row in rows]
    if start > end:
        start, end = end, start
    values = {str(row[key_name]): int(row["n"]) for row in rows}
    result = []
    if bucket == "month":
        cursor = start.replace(day=1)
        final = end.replace(day=1)
        while cursor <= final:
            key = period_key_for_date(cursor, "month")
            result.append({key_name: key, "period": key, "day": key, "n": values.get(key, 0)})
            cursor = add_months(cursor, 1)
        return result
    if bucket == "week":
        cursor = start
        while cursor <= end:
            key = period_key_for_date(cursor, "week")
            if not result or result[-1][key_name] != key:
                result.append({key_name: key, "period": key, "day": key, "n": values.get(key, 0)})
            cursor += timedelta(days=1)
        return result
    cursor = start
    while cursor <= end:
        key = cursor.isoformat()
        result.append({key_name: key, "period": key, "day": key, "n": values.get(key, 0)})
        cursor += timedelta(days=1)
    return result


def clean_query(value: str | None) -> str:
    return re.sub(r"\s+", " ", (value or "").replace('"', "").strip().lower())


def first_sentence(value: str | None, limit: int = 220) -> str:
    text = re.sub(r"\s+", " ", value or "").strip()
    if not text:
        return "Краткое описание не найдено. Откройте карточку, чтобы посмотреть служебные данные публикации."
    parts = re.split(r"(?<=[.!?…])\s+", text, maxsplit=1)
    sentence = parts[0].strip() if parts else text
    if len(sentence) > limit:
        sentence = sentence[:limit].rsplit(" ", 1)[0].strip() + "..."
    return sentence


def publication_feed_card(item) -> str:
    title = item["title"] or item["url"] or "Публикация без заголовка"
    summary = first_sentence(item["snippet"] or item["text"] if "text" in item.keys() else item["snippet"])
    has_pub_date = bool(item["published_at"])
    if has_pub_date:
        date = display_datetime(item["published_at"], "нет даты публикации")
        date_label = "Дата публикации"
        date_note = ""
        summary_date = display_date(item["published_at"], "")
        summary_date_title = "Дата публикации"
    else:
        date = display_datetime(item["collected_at"], "нет даты сбора")
        date_label = "Дата публикации"
        date_note = " <span title='Дата публикации неизвестна, показана дата сбора' style='color:#8a6200;font-size:11px;font-weight:700;background:#fff8e6;border-radius:4px;padding:1px 5px'>≈ оценочная</span>"
        summary_date = display_date(item["collected_at"], "") + " ≈"
        summary_date_title = "Дата публикации неизвестна — показана дата сбора"
    collected = display_datetime(item["collected_at"], "нет даты сбора")
    source = item["source"] or "unknown"
    return f"""
    <details class="feed-card">
      <summary>
        <span class="pill {esc(item['sentiment'])}">{esc(sentiment_ru(item['sentiment']))}</span>
        <span class="feed-main">
          <a href="{esc(item['url'])}" target="_blank" rel="noopener">{esc(title)}</a>
          <span>{esc(summary)}</span>
        </span>
        <span class="feed-date" title="{esc(summary_date_title)}">{esc(summary_date)}</span>
        <span class="feed-source">{esc(source)}</span>
        <span class="feed-more">Подробнее</span>
      </summary>
      <div class="feed-detail">
        <div><b>Запрос</b><span>{esc(item['query'])}</span></div>
        <div><b>{date_label}</b><span>{esc(date)}{date_note}</span></div>
        <div><b>Дата сбора</b><span>{esc(collected)}</span></div>
        <div><b>Язык</b><span>{esc(item['language'])}</span></div>
        <div class="feed-detail-wide"><b>Источник</b><span>{esc(source)}</span></div>
        <div class="feed-detail-wide"><b>Фрагмент</b><span>{esc(item['snippet'] or "нет фрагмента")}</span></div>
      </div>
    </details>
    """


def source_profile(source: str | None, url: str | None = None) -> dict:
    haystack = f"{source or ''} {url or ''}".lower()
    profiles = [
        ("ria.ru", 900_000, 95, "Россия", "федеральное агентство"),
        ("tass.ru", 850_000, 94, "Россия", "федеральное агентство"),
        ("interfax", 620_000, 91, "Россия", "федеральное агентство"),
        ("kommersant", 520_000, 90, "Россия", "федеральное деловое СМИ"),
        ("vedomosti", 480_000, 89, "Россия", "федеральное деловое СМИ"),
        ("companies.rbc", 90_000, 70, "Россия", "бизнес-каталог"),
        ("rbc", 350_000, 86, "Россия", "федеральный деловой источник"),
        ("rg.ru", 360_000, 84, "Россия", "федеральное СМИ"),
        ("iz.ru", 420_000, 84, "Россия", "федеральное СМИ"),
        ("lenta.ru", 430_000, 83, "Россия", "федеральное СМИ"),
        ("cnews", 180_000, 78, "Россия", "отраслевое СМИ"),
        ("тбанк", 260_000, 68, "Россия", "крупная экосистема"),
        ("tbank", 260_000, 68, "Россия", "крупная экосистема"),
        ("onlinevologda", 75_000, 62, "Вологодская область", "региональное СМИ"),
        ("cherinfo", 85_000, 64, "Вологодская область", "региональное СМИ"),
        ("krassever", 70_000, 61, "Вологодская область", "региональное СМИ"),
        ("newsvo", 80_000, 63, "Вологодская область", "региональное СМИ"),
        ("северинфо", 55_000, 56, "Вологодская область", "региональное СМИ"),
        ("вологда регион", 55_000, 56, "Вологодская область", "региональное СМИ"),
        ("2gis", 90_000, 62, "Калининград", "городской справочник"),
        ("klops", 170_000, 78, "Калининград", "региональное СМИ"),
        ("клопс", 170_000, 78, "Калининград", "региональное СМИ"),
        ("новый калининград", 145_000, 76, "Калининград", "региональное СМИ"),
        ("newkaliningrad", 145_000, 76, "Калининград", "региональное СМИ"),
        ("cifra.digital", 12_000, 42, "Калининград", "собственный сайт"),
        ("reputation", 20_000, 38, "Россия", "каталог"),
        ("companium", 18_000, 36, "Россия", "каталог"),
        ("fbc.ru", 16_000, 34, "Россия", "каталог"),
        ("cataloxy", 10_000, 28, "Калининград", "каталог"),
        ("yp.ru", 10_000, 28, "Калининград", "каталог"),
        ("orgs.biz", 8_000, 24, "Калининград", "каталог"),
    ]
    for token, reach, influence, geo, note in profiles:
        if token in haystack:
            return {"reach": reach, "influence": influence, "geo": geo, "note": note}
    if any(token in haystack for token in ["vk.com", "telegram", "youtube", "t.me"]):
        return {"reach": 25_000, "influence": 45, "geo": "не определено", "note": "соцсеть без подключенной статистики"}
    return {"reach": 15_000, "influence": 32, "geo": "не определено", "note": "оценка по умолчанию"}


def row_text(row) -> str:
    return " ".join(str(row[key] or "") for key in ["title", "snippet", "text", "source"] if key in row.keys())


def prominence_score(row) -> int:
    title = (row["title"] or "").lower()
    snippet = (row["snippet"] or "").lower()
    text = (row["text"] or "").lower()
    query = clean_query(row["query"])
    score = 0
    if query and query in title:
        score += 45
    elif any(part for part in query.split() if len(part) > 4 and part in title):
        score += 25
    if query and query in snippet[:350]:
        score += 25
    if query and text.count(query) >= 2:
        score += 15
    if source_profile(row["source"], row["url"])["influence"] >= 70:
        score += 15
    return min(100, score)


def engagement_count(row) -> int:
    total = 0
    for key in ["likes", "reposts", "shares", "comments", "views"]:
        if key in row.keys():
            try:
                total += int(row[key] or 0)
            except (TypeError, ValueError):
                pass
    return total


def detect_geo(row) -> str:
    text = row_text(row).lower()
    locations = [
        ("калининград", "Калининград"),
        ("москва", "Москва"),
        ("санкт-петербург", "Санкт-Петербург"),
        ("петербург", "Санкт-Петербург"),
        ("росси", "Россия"),
    ]
    for token, name in locations:
        if token in text:
            return name
    return source_profile(row["source"], row["url"])["geo"]


def normalize_title(value: str | None) -> str:
    clean = re.sub(r"[^a-zа-яё0-9]+", " ", (value or "").lower())
    return re.sub(r"\s+", " ", clean).strip()


def canonical_story_title(value: str | None) -> str:
    title = normalize_title(value)
    noise = [
        "георгий",
        "филимонов",
        "губернатор",
        "вологодской",
        "области",
        "российская",
        "академия",
        "цифра",
        "энерготрансбанк",
        "новости",
        "онлайн",
    ]
    words = [word for word in title.split() if len(word) > 3 and word not in noise]
    return " ".join(words[:14])


def story_tokens(value: str | None) -> set[str]:
    title = canonical_story_title(value)
    stop = {
        "поздравил",
        "провел",
        "получил",
        "рассказал",
        "напутствовал",
        "приветствовал",
        "утвердил",
        "встретился",
        "подтвердил",
    }
    return {word for word in title.split() if len(word) > 4 and word not in stop}


def title_features(value: str | None) -> tuple[str, set[str], set[str]]:
    key = canonical_story_title(value)
    tokens = story_tokens(value)
    compact = key.replace(" ", "")
    trigrams = {compact[index : index + 3] for index in range(max(0, len(compact) - 2))}
    return key, tokens, trigrams


def feature_similarity(
    left: tuple[str, set[str], set[str]],
    right: tuple[str, set[str], set[str]],
) -> float:
    left_key, left_tokens, left_trigrams = left
    right_key, right_tokens, right_trigrams = right
    if not left_key or not right_key:
        return 0
    if left_key == right_key:
        return 1
    length_ratio = min(len(left_key), len(right_key)) / max(len(left_key), len(right_key))
    if length_ratio < 0.45:
        return 0

    shared_tokens = left_tokens & right_tokens
    token_overlap = 0.0
    if left_tokens and right_tokens:
        token_overlap = len(shared_tokens) / max(1, min(len(left_tokens), len(right_tokens)))

    trigram_score = 0.0
    if left_trigrams and right_trigrams:
        trigram_score = 2 * len(left_trigrams & right_trigrams) / (len(left_trigrams) + len(right_trigrams))

    if len(shared_tokens) < 2 and trigram_score < 0.78:
        return 0
    return max(token_overlap, trigram_score)


def story_similarity(left_title: str | None, right_title: str | None) -> float:
    return feature_similarity(title_features(left_title), title_features(right_title))


def duplicate_groups(mentions) -> list[list]:
    groups: list[dict] = []
    for row in mentions:
        title = normalize_title(row["title"])
        if len(title) < 24:
            continue
        features = title_features(row["title"])
        placed = False
        for group in groups:
            reference_title = group["title"]
            length_ratio = min(len(title), len(reference_title)) / max(len(title), len(reference_title))
            if length_ratio >= 0.72 and feature_similarity(features, group["features"]) >= 0.86:
                group["items"].append(row)
                placed = True
                break
        if not placed:
            groups.append({"title": title, "features": features, "items": [row]})
    return [group["items"] for group in groups if len(group["items"]) > 1]


def story_groups(mentions) -> list[dict]:
    groups: list[dict] = []
    for row in mentions:
        features = title_features(row["title"])
        key = features[0]
        if len(key) < 14:
            key = normalize_title(row["title"])
        if len(key) < 14:
            continue
        placed = None
        for group in groups:
            same_first_source = (row["source"] or "") == (group["items"][0]["source"] or "")
            threshold = 0.82 if same_first_source else 0.60
            if feature_similarity(features, group["features"]) >= threshold:
                placed = group
                break
        if placed is None:
            placed = {"key": key, "features": features, "items": []}
            groups.append(placed)
        placed["items"].append(row)

    result = []
    for group in groups:
        items = group["items"]
        if not items:
            continue
        sources = sorted({item["source"] or "unknown" for item in items})
        primary = min(items, key=lambda row: parse_dt(row["published_at"] or row["collected_at"]) or datetime.max.replace(tzinfo=timezone.utc))
        influence = sum(source_profile(item["source"], item["url"])["influence"] for item in items)
        source_bonus = len(sources) * 8
        citation_index = influence + source_bonus
        result.append(
            {
                "title": primary["title"],
                "primary": primary,
                "items": items,
                "sources": sources,
                "mentions": len(items),
                "source_count": len(sources),
                "citation_index": citation_index,
            }
        )
    return sorted(result, key=lambda item: (item["citation_index"], item["mentions"]), reverse=True)


def citation_panel(mentions) -> str:
    stories = story_groups(mentions)
    reprints = sum(max(0, story["mentions"] - 1) for story in stories)
    total_index = sum(story["citation_index"] for story in stories)
    top_rows = ""
    for story in stories[:6]:
        primary = story["primary"]
        reprint_items = [item for item in story["items"] if item["id"] != primary["id"]]
        reprint_count = len(reprint_items)
        reprint_list = ""
        for item in sorted(reprint_items, key=lambda row: row["published_at"] or row["collected_at"])[:4]:
            reprint_list += (
                f'<div class="metric-mini"><span>{esc(item["source"] or "unknown")}</span>'
                f'<b><a href="{esc(item["url"])}" target="_blank" rel="noopener">открыть</a></b></div>'
            )
        if reprint_count > 4:
            reprint_list += f'<div class="metric-mini"><span>Еще перепечаток</span><b>{reprint_count - 4}</b></div>'
        if not reprint_list:
            reprint_list = '<div class="muted">перепечаток не найдено</div>'
        source_list = ", ".join(story["sources"][:4])
        if len(story["sources"]) > 4:
            source_list += f" +{len(story['sources']) - 4}"
        top_rows += f"""
        <tr>
          <td data-label="Сюжет"><a href="{esc(primary['url'])}" target="_blank" rel="noopener">{esc(story['title'])}</a><div class="muted">первоисточник: {esc(primary['source'] or 'unknown')} · {esc(display_datetime(primary['published_at'] or primary['collected_at']))}</div></td>
          <td data-label="Публикации"><b>{story['mentions']}</b><div class="muted">публикаций всего</div></td>
          <td data-label="Перепечатки"><b>{reprint_count}</b><div class="muted">после первоисточника</div>{reprint_list}</td>
          <td data-label="Источники"><b>{story['source_count']}</b><div class="muted">{esc(source_list)}</div></td>
          <td data-label="Индекс"><b>{story['citation_index']}</b><div class="muted">базовый ИЦ</div></td>
        </tr>
        """
    empty = '<tr><td colspan="5">Пока мало данных для группировки сюжетов.</td></tr>'
    return f"""
    <div class="card viz-wide citation-panel">
      <div class="chart-title"><h3>Цитируемость и перепечатки</h3><span>{len(stories)} сюжетов · {reprints} перепечаток · ИЦ {total_index}</span></div>
      <div class="citation-table-wrap"><table class="citation-table">
        <thead><tr><th>Сюжет / вероятный первоисточник</th><th>Публикации</th><th>Перепечатки</th><th>Источники</th><th>Индекс</th></tr></thead>
        <tbody>{top_rows or empty}</tbody>
      </table></div>
    </div>
    """


def period_growth(mentions) -> tuple[str, str]:
    dates = [parse_dt(row["published_at"] or row["collected_at"]) for row in mentions]
    dates = [dt for dt in dates if dt]
    if len(dates) < 2:
        return "0%", "мало данных"
    start = min(dates)
    end = max(dates)
    if start.date() == end.date():
        return f"{len(dates)}", "за один день"
    midpoint = start + (end - start) / 2
    previous = sum(1 for dt in dates if dt < midpoint)
    current = sum(1 for dt in dates if dt >= midpoint)
    if previous == 0:
        return f"+{current}", "к прошлому периоду"
    if previous < 5 and current > previous:
        return f"+{current - previous}", f"{previous} -> {current}, низкая база"
    growth = round((current - previous) / previous * 100)
    return f"{growth:+d}%", f"{previous} -> {current}"


def metric_details(rows: list[tuple[str, str]]) -> str:
    return "".join(f"<div class='metric-mini'><span>{esc(label)}</span><b>{esc(value)}</b></div>" for label, value in rows)


def commercial_metrics_panel(stats: dict, mentions) -> str:
    total = stats["total"]
    pos = stats["by_sentiment"].get("positive", 0)
    neg = stats["by_sentiment"].get("negative", 0)

    reach_total = 0
    publication_reach_total = 0
    weighted_influence = 0
    visible_scores = []
    engagement_total = 0
    geo_counts: dict[str, int] = {}
    source_rows = []
    unique_source_profiles = {}
    for row in mentions:
        profile = source_profile(row["source"], row["url"])
        publication_reach_total += profile["reach"]
        source_key = row["source"] or source_profile(row["source"], row["url"])["note"] or "unknown"
        if source_key not in unique_source_profiles:
            unique_source_profiles[source_key] = profile
        weighted_influence += profile["influence"]
        visible_scores.append(prominence_score(row))
        engagement_total += engagement_count(row)
        geo = detect_geo(row)
        geo_counts[geo] = geo_counts.get(geo, 0) + 1
    reach_total = sum(profile["reach"] for profile in unique_source_profiles.values())
    source_rows = [
        (name, compact_number(profile["reach"]), str(profile["influence"]))
        for name, profile in sorted(unique_source_profiles.items(), key=lambda item: item[1]["reach"], reverse=True)
    ]

    avg_influence = round(weighted_influence / total) if total else 0
    avg_prominence = round(sum(visible_scores) / len(visible_scores)) if visible_scores else 0
    high_prominence = sum(1 for score in visible_scores if score >= 60)
    negative_share = pct(neg, total)
    duplicate_sets = duplicate_groups(mentions)
    duplicate_mentions = sum(max(0, len(group) - 1) for group in duplicate_sets)
    grouped_duplicate_mentions = sum(len(group) for group in duplicate_sets)
    growth_value, growth_caption = period_growth(mentions)
    top_geo, top_geo_count = max(geo_counts.items(), key=lambda item: item[1], default=("нет данных", 0))
    social_measured = sum(1 for row in mentions if engagement_count(row) > 0)
    source_preview = source_rows[:4]
    geo_preview = sorted(geo_counts.items(), key=lambda item: item[1], reverse=True)[:4]

    risk_state = "good" if negative_share < 10 else "warn" if negative_share < 25 else "bad"
    engagement_state = "good" if engagement_total else "warn"
    duplicate_state = "good" if duplicate_mentions == 0 else "warn"

    cards = [
        {
            "name": "Охват",
            "caption": "потенциальная аудитория",
            "value": compact_number(reach_total),
            "state": "warn",
            "state_text": "оценка по источникам",
            "text": "Сумма расчетной аудитории уникальных источников. Это не реальные просмотры публикаций, а модельная оценка до подключения SimilarWeb/LiveInternet/собственной базы посещаемости.",
            "rows": [("Упоминаний в расчете", str(total)), ("Уникальных источников", str(stats.get("unique_sources", 0))), ("Если считать каждую публикацию", compact_number(publication_reach_total))] + [(name, reach) for name, reach, _ in source_preview],
        },
        {
            "name": "Влиятельность",
            "caption": "средний вес источников",
            "value": f"{avg_influence}/100",
            "state": "warn",
            "state_text": "по весам источников",
            "text": "Каждому источнику назначен вес. СМИ и крупные платформы получают больший вклад, каталоги и малые страницы меньший.",
            "rows": [("Средний индекс", f"{avg_influence}/100"), ("Позитивных публикаций", str(pos))] + [(name, f"{score}/100") for name, _, score in source_preview],
        },
        {
            "name": "Заметность",
            "caption": "роль объекта в материале",
            "value": f"{avg_prominence}/100",
            "state": "good" if avg_prominence >= 50 else "warn",
            "state_text": f"{high_prominence} сильных",
            "text": "Считается по тому, есть ли объект в заголовке, в начале текста, повторяется ли в материале и насколько силен источник.",
            "rows": [("Средняя заметность", f"{avg_prominence}/100"), ("Сильных упоминаний", str(high_prominence)), ("Всего упоминаний", str(total))],
        },
        {
            "name": "Вовлеченность",
            "caption": "реакции и просмотры",
            "value": compact_number(engagement_total),
            "state": engagement_state,
            "state_text": "нужны соц. API" if not engagement_total else "есть данные",
            "text": "Сумма лайков, репостов, комментариев и просмотров там, где источник отдает эти поля. Для VK данные уже сохраняются; для Telegram и YouTube нужны отдельные подключения.",
            "rows": [("Публикаций с соцметриками", str(social_measured)), ("Реакции + просмотры", compact_number(engagement_total)), ("Следующий шаг", "Telegram/YouTube API")],
        },
        {
            "name": "Доля негатива",
            "caption": "репутационный риск",
            "value": f"{negative_share}%",
            "state": risk_state,
            "state_text": "низкий риск" if negative_share < 10 else "проверить",
            "text": "Считается как доля негативных публикаций от всех найденных упоминаний в текущем фильтре.",
            "rows": [("Негативных", str(neg)), ("Всего", str(total)), ("Позитивных", str(pos))],
        },
        {
            "name": "Динамика",
            "caption": "рост/падение упоминаний",
            "value": growth_value,
            "state": "good" if growth_value.startswith("+") else "warn",
            "state_text": growth_caption,
            "text": "Сравнивается текущая половина периода с предыдущей. После накопления ежедневных данных это станет полноценным графиком роста и спадов.",
            "rows": [(display_period(str(row["day"]), "day", str(row["day"])), str(row["n"])) for row in stats["daily"][-5:]] or [("Данных", "мало")],
        },
        {
            "name": "География",
            "caption": "регионы и страны",
            "value": top_geo,
            "state": "good" if top_geo != "не определено" else "warn",
            "state_text": f"{top_geo_count} упоминаний",
            "text": "Регион определяется по тексту публикации и профилю источника. Позже сюда добавляется справочник источников и NER по локациям.",
            "rows": [(name, str(count)) for name, count in geo_preview] or [("Регион", "не определен")],
        },
        {
            "name": "Дубли",
            "caption": "перепечатки и похожие тексты",
            "value": str(duplicate_mentions),
            "state": duplicate_state,
            "state_text": f"{len(duplicate_sets)} групп",
            "text": "Группирует публикации с очень похожими заголовками. Значение показывает дополнительные публикации внутри групп, то есть вероятные перепечатки после первой записи.",
            "rows": [("Вероятных перепечаток", str(duplicate_mentions)), ("Публикаций в группах", str(grouped_duplicate_mentions)), ("Групп дублей", str(len(duplicate_sets))), ("Точных дублей ссылок", "не сохраняются")],
        },
    ]

    body = ""
    for item in cards:
        detail_rows = metric_details(item["rows"])
        body += (
            "<details class='metric-pill'>"
            f"<summary><b>{esc(item['name'])}</b><span class='muted'>{esc(item['caption'])}</span>"
            f"<div class='metric-number'>{esc(item['value'])}</div>"
            f"<span class='metric-state {esc(item['state'])}'>{esc(item['state_text'])}</span></summary>"
            f"<div class='metric-detail'><p>{esc(item['text'])}</p>{detail_rows}</div>"
            "</details>"
        )

    note = (
        "Это уже рабочая модель аналитики поверх текущей базы. Желтые статусы означают, что цифра считается, "
        "но для продажи как точной индустриальной метрики нужно подключить внешние данные: посещаемость СМИ, подписчиков, просмотры и реакции."
    )
    return f"""
    <div class="card viz-wide">
      <div class="chart-title"><h3>Рабочие PR-метрики</h3><span>по текущему фильтру и базе упоминаний</span></div>
      <div class="metric-list">{body}</div>
      <div class="coverage-note">{esc(note)}</div>
    </div>
    """
