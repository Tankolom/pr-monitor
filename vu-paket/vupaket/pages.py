"""HTML-страницы. Без шаблонизатора и фронтенд-сборки: всё отдаётся сервером."""
from __future__ import annotations

import html
from datetime import date

from .config import Settings
from .documents import MONTHS_NOM
from .validation import allowed_years, default_year

e = html.escape

CSS = """
:root{--bg:#f6f7f9;--card:#fff;--ink:#16202c;--muted:#5b6776;--line:#dfe3e8;--accent:#1f5eff;--accent-ink:#fff;
--ok:#0f7b4f;--warn:#9a5b00;--err:#b42318;--radius:14px}
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif}
a{color:var(--accent)}.wrap{max-width:880px;margin:0 auto;padding:0 16px}
header.top{padding:14px 0;border-bottom:1px solid var(--line);background:var(--card)}
header.top .wrap{display:flex;justify-content:space-between;align-items:center;gap:12px}
.logo{font-weight:700;text-decoration:none;color:var(--ink)}.logo span{color:var(--accent)}
h1{font-size:30px;line-height:1.2;margin:28px 0 12px}h2{font-size:22px;margin:32px 0 12px}h3{font-size:17px;margin:0 0 6px}
.lead{font-size:18px;color:var(--muted);margin:0 0 20px}
.btn{display:inline-block;background:var(--accent);color:var(--accent-ink);border:0;border-radius:10px;padding:14px 22px;
font-size:17px;font-weight:600;text-decoration:none;cursor:pointer;text-align:center}
.btn:hover{filter:brightness(.95)}.btn.ghost{background:transparent;color:var(--accent);border:1px solid var(--accent)}
.btn.block{display:block;width:100%}
.card{background:var(--card);border:1px solid var(--line);border-radius:var(--radius);padding:20px;margin:16px 0}
.grid{display:grid;gap:12px;grid-template-columns:1fr}
@media(min-width:720px){.grid.two{grid-template-columns:1fr 1fr}.grid.three{grid-template-columns:1fr 1fr 1fr}h1{font-size:38px}}
.muted{color:var(--muted)}.small{font-size:14px}.price{font-size:28px;font-weight:700}
ul.check{padding-left:0;list-style:none;margin:0}ul.check li{padding-left:28px;position:relative;margin:8px 0}
ul.check li:before{content:"✓";position:absolute;left:4px;color:var(--ok);font-weight:700}
label{display:block;font-weight:600;margin:14px 0 6px}.hint{font-weight:400;color:var(--muted);font-size:14px}
input[type=text],input[type=email],input[type=number],select{width:100%;padding:12px;border:1px solid #c5ccd6;border-radius:10px;
font-size:16px;background:#fff;color:var(--ink)}
input:focus,select:focus{outline:2px solid var(--accent);outline-offset:1px}
.radio{display:flex;gap:10px;align-items:flex-start;font-weight:400;margin:8px 0}.radio input{margin-top:5px}
.err{color:var(--err);font-size:14px;margin-top:4px}.field-err input,.field-err select{border-color:var(--err)}
.alert{border-radius:10px;padding:12px 14px;margin:12px 0}.alert.warn{background:#fff6e5;color:var(--warn)}
.alert.err{background:#fdecea;color:var(--err)}.alert.ok{background:#e8f6ef;color:var(--ok)}
footer{margin:48px 0 24px;color:var(--muted);font-size:14px}
.steps{counter-reset:s;list-style:none;padding:0}.steps li{counter-increment:s;padding-left:40px;position:relative;margin:12px 0}
.steps li:before{content:counter(s);position:absolute;left:0;top:0;width:28px;height:28px;border-radius:50%;background:var(--accent);
color:#fff;text-align:center;line-height:28px;font-weight:700;font-size:14px}
details{border-top:1px solid var(--line);padding:12px 0}summary{cursor:pointer;font-weight:600}
.doc{background:#fff;border:1px solid var(--line);border-radius:8px;padding:24px 20px;margin:16px 0;font-family:"Times New Roman",Times,serif;
font-size:15px;line-height:1.45;overflow:hidden}
.doc p{margin:0 0 6px}.doc .c{text-align:center}.doc .r{text-align:right}.doc .b{font-weight:700}.doc .big{font-size:18px}
.doc .j{text-align:justify}.doc .ind{text-indent:1.25cm}.doc .note{font-style:italic;font-size:13px}.doc .sp{height:8px}
.doc .row2{display:flex;justify-content:space-between;gap:16px;margin:6px 0}.doc .small{font-size:13px}
.doc-name{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif;font-size:12px;color:var(--muted);
text-transform:uppercase;letter-spacing:.04em;margin-bottom:12px}
.tbl{overflow-x:auto}.doc table{border-collapse:collapse;width:100%;font-size:13px}.doc th,.doc td{border:1px solid #999;padding:4px 6px;vertical-align:top}
@media(max-width:600px){.doc .j{text-align:left}.doc .ind{text-indent:1em}.doc{padding:16px 12px}}
.fade{position:relative;max-height:640px;overflow:hidden}.fade:after{content:"";position:absolute;left:0;right:0;bottom:0;height:200px;
background:linear-gradient(rgba(246,247,249,0),var(--bg))}
.sticky-pay{position:sticky;bottom:0;background:var(--card);border-top:1px solid var(--line);padding:12px 0;margin-top:16px}
table.stats{border-collapse:collapse;width:100%;font-size:14px}table.stats td,table.stats th{border-bottom:1px solid var(--line);padding:6px;text-align:left}
"""


def layout(s: Settings, title: str, body: str, goal: str | None = None, noindex: bool = False) -> str:
    metrika = ""
    if s.metrika_id.isdigit():
        mid = s.metrika_id
        goal_js = f"ym({mid},'reachGoal','{e(goal)}');" if goal else ""
        # Вебвизор выключен намеренно: он записывал бы ввод анкеты (персональные данные).
        metrika = (
            "<script>(function(m,e,t,r,i,k,a){m[i]=m[i]||function(){(m[i].a=m[i].a||[]).push(arguments)};"
            "m[i].l=1*new Date();k=e.createElement(t),a=e.getElementsByTagName(t)[0],k.async=1,k.src=r,"
            "a.parentNode.insertBefore(k,a)})(window,document,'script','https://mc.yandex.ru/metrika/tag.js','ym');"
            f"ym({mid},'init',{{clickmap:false,trackLinks:true,accurateTrackBounce:true,webvisor:false}});{goal_js}</script>"
        )
    robots = '<meta name="robots" content="noindex,nofollow">' if noindex else ""
    return f"""<!doctype html><html lang="ru"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)}</title>{robots}
<meta name="description" content="Приказ, план работы, журнал проверок и письмо в военкомат — заполнены под вашу компанию за 15 минут.">
<style>{CSS}</style>{metrika}</head><body>
<header class="top"><div class="wrap"><a class="logo" href="/">ВУ<span>·</span>Пакет</a>
<a class="small" href="/sample">Пример документов</a></div></header>
<main class="wrap">{body}</main>
<footer class="wrap">{footer(s)}</footer></body></html>"""


def footer(s: Settings) -> str:
    seller = (f"{e(s.seller_name)}, ИНН {e(s.seller_inn)} · {e(s.seller_email)}" if s.seller_ready
              else "<b>[ДЕМО: реквизиты продавца не заданы — заполните VU_SELLER_* перед запуском]</b>")
    return (f"<p>{seller}</p><p><a href='/offer'>Оферта и возврат</a> · <a href='/privacy'>Обработка персональных данных</a></p>"
            "<p>Шаблоны документов, не юридическая консультация. Проверяйте реквизиты и требования своего военкомата.</p>")


def price_str(rub: int) -> str:
    return f"{rub:,}".replace(",", " ") + " ₽"


def landing(s: Settings) -> str:
    y = default_year()
    p = price_str(s.price_rub)
    body = f"""
<h1>Документы по воинскому учёту для вашей компании — за 15 минут</h1>
<p class="lead">Приказ, план работы на {y} год, журнал проверок и письмо в военкомат. Заполнены вашими реквизитами, в формате Word.
По Положению о воинском учёте в редакции 2026 года.</p>
<p><a class="btn" href="/form">Заполнить данные — бесплатно</a></p>
<p class="small muted">Сначала предпросмотр, оплата {p} — только если всё устраивает. Возврат в течение 7 дней.</p>

<div class="card"><h3>Кому подходит</h3>
<p>ООО и другим организациям до 500 человек на учёте, где нет кадровика: учёт ведёт директор или бухгалтер.
Когда нужно: военкомат или прокуратура запросили документы, наняли первого сотрудника, в конце года пора согласовать план на следующий год.</p></div>

<h2>Что в пакете</h2>
<div class="grid two">
<div class="card"><h3>1. Приказ об организации воинского учёта</h3><p class="small muted">С ответственным и замещающим, блоком согласования с военкоматом, листом ознакомления.</p></div>
<div class="card"><h3>2. Функциональные обязанности</h3><p class="small muted">Приложение к приказу со ссылками на пункты Положения № 719.</p></div>
<div class="card"><h3>3. План работы на {y} год</h3><p class="small muted">13 мероприятий со сроками, исполнителем и месяцем сверки. Гриф «Согласовано» и «Утверждаю».</p></div>
<div class="card"><h3>4. Журнал проверок</h3><p class="small muted">Готовая таблица с шапкой вашей организации.</p></div>
<div class="card"><h3>5. Письмо в военкомат</h3><p class="small muted">Сопроводительное письмо о согласовании приказа и плана.</p></div>
<div class="card"><h3>6. Памятка и напоминания</h3><p class="small muted">Что подписать и куда отнести, сроки «5 дней», файл напоминаний для календаря о сверке и плане на следующий год.</p></div>
</div>

<h2>Как это работает</h2>
<ol class="steps"><li>Заполняете анкету: реквизиты, руководитель, ответственный, военкомат. Данные сотрудников не нужны.</li>
<li>Смотрите предпросмотр приказа и проверяете данные.</li>
<li>Оплачиваете {p} картой или через СБП и сразу скачиваете архив с 6 документами и календарём.</li></ol>

<h2>Чем это лучше бесплатного образца</h2>
<ul class="check">
<li>Не нужно вписывать реквизиты вручную в шесть документов — всё заполнено одинаково и без опечаток.</li>
<li>Актуальные сроки: во многих образцах до сих пор «2 недели», а по п. 32 Положения в редакции 2026 года — 5 дней.</li>
<li>План со сроками под ваш год и выбранный месяц сверки, а не пустая таблица.</li>
<li>Напоминания в календаре о ежегодной сверке и плане на следующий год.</li>
</ul>

<h2>Честно об ограничениях</h2>
<ul class="check">
<li>Это шаблоны документов, а не юридическое сопровождение. Согласование с военкоматом проходите вы — пакет даёт готовые документы и письмо.</li>
<li>Не подходит для бронирования граждан и организаций, где на учёте 500 и более человек.</li>
<li>Карточки по форме № 10 заполняются по документам сотрудников — их мы не собираем и не храним.</li>
</ul>

<div class="card"><div class="price">{p}</div><p class="muted">за пакет для одной организации. Оплата после предпросмотра. Чек придёт на почту.</p>
<a class="btn block" href="/form">Собрать пакет</a></div>

<h2>Вопросы</h2>
<details><summary>Нужно ли вести воинский учёт, если в компании один директор?</summary>
<p>Да, если директор — работник организации и состоит на воинском учёте. Для небольших организаций руководитель может вести учёт сам: в анкете выберите «Руководитель ведёт сам».</p></details>
<details><summary>А индивидуальному предпринимателю?</summary>
<p>Положение о воинском учёте адресовано организациям, и большинство разъяснений исходит из того, что ИП формально не обязаны вести учёт.
На практике военкоматы иногда запрашивают сведения — уточните в своём военкомате до покупки.</p></details>
<details><summary>Военкомат попросил свою форму. Что делать?</summary>
<p>Перенесите данные из пакета в форму военкомата. Если документы вам не подошли, напишите в течение 7 дней — вернём деньги.</p></details>
<details><summary>Что вы делаете с моими данными?</summary>
<p>Используем только чтобы собрать документы и отправить чек. Анкеты без оплаты удаляются через {s.order_ttl_days} дней. Данные работников не запрашиваем.</p></details>
"""
    return layout(s, "Документы по воинскому учёту за 15 минут — ВУ·Пакет", body, goal="view_landing")


def _field(name: str, label: str, data: dict, errors: dict, hint: str = "", kind: str = "text", attrs: str = "") -> str:
    val = e(str(data.get(name, "") or ""))
    err = f'<div class="err">{e(errors[name])}</div>' if name in errors else ""
    cls = ' class="field-err"' if name in errors else ""
    hint_html = f' <span class="hint">{e(hint)}</span>' if hint else ""
    return (f'<div{cls}><label for="{name}">{e(label)}{hint_html}</label>'
            f'<input type="{kind}" id="{name}" name="{name}" value="{val}" {attrs}>{err}</div>')


def form_page(s: Settings, data: dict, errors: dict, action: str = "/order", edit: bool = False) -> str:
    today = date.today()
    data = dict(data)
    data.setdefault("year", default_year(today))
    data.setdefault("sverka_month", 3)
    data.setdefault("mode", "appoint")
    data.setdefault("submit_method", "epgu")
    data.setdefault("head_position", "Генеральный директор")
    err_top = ('<div class="alert err">Проверьте поля, отмеченные красным.</div>' if errors else "")
    years = "".join(f'<option value="{y}"{" selected" if int(data["year"]) == y else ""}>{y}</option>' for y in allowed_years(today))
    months = "".join(f'<option value="{m}"{" selected" if int(data["sverka_month"]) == m else ""}>{MONTHS_NOM[m].capitalize()}</option>' for m in range(1, 13))

    def radio(name, value, label, hint=""):
        chk = " checked" if data.get(name) == value else ""
        h = f'<br><span class="hint">{e(hint)}</span>' if hint else ""
        return f'<label class="radio"><input type="radio" name="{name}" value="{value}"{chk}><span>{e(label)}{h}</span></label>'

    def err(name):
        return f'<div class="err">{e(errors[name])}</div>' if name in errors else ""

    body = f"""
<h1>{'Изменить данные' if edit else 'Данные для документов'}</h1>
<p class="muted">Заполнение — 5–10 минут. Данные сотрудников не нужны. Оплата после предпросмотра.</p>
{err_top}
<form method="post" action="{e(action)}" novalidate>
<div class="card"><h3>Организация</h3>
{_field("org_full", "Полное наименование", data, errors, attrs='placeholder="Общество с ограниченной ответственностью «Ромашка»" autocomplete="organization"')}
{_field("org_short", "Сокращённое наименование", data, errors, attrs='placeholder="ООО «Ромашка»"')}
<div class="grid two">{_field("inn", "ИНН", data, errors, attrs='inputmode="numeric" maxlength="12" placeholder="10 цифр"')}
{_field("city", "Город (место издания приказа)", data, errors, attrs='placeholder="Москва"')}</div>
{_field("address", "Юридический адрес", data, errors, hint="для письма в военкомат, необязательно")}
<div class="grid two">{_field("staff_total", "Сколько работников", data, errors, kind="number", attrs='min="1" max="499" inputmode="numeric"')}
{_field("email", "Почта для чека", data, errors, kind="email", attrs='autocomplete="email" placeholder="buh@company.ru"')}</div>
</div>

<div class="card"><h3>Руководитель</h3>
<div class="grid two">{_field("head_position", "Должность", data, errors)}
{_field("head_name", "ФИО полностью", data, errors, attrs='placeholder="Иванов Иван Иванович"')}</div>
</div>

<div class="card"><h3>Кто ведёт воинский учёт</h3>
{radio("mode", "appoint", "Назначаем работника", "Например, бухгалтера или офис-менеджера — по совместительству")}
{radio("mode", "self", "Руководитель ведёт сам", "Подходит небольшим организациям")}{err("mode")}
<div id="resp-block"><div class="grid two">{_field("resp_position", "Должность ответственного", data, errors, attrs='placeholder="Бухгалтер"')}
{_field("resp_name", "ФИО ответственного", data, errors)}</div></div>
<div class="grid two">{_field("deputy_position", "Должность замещающего", data, errors, hint="необязательно")}
{_field("deputy_name", "ФИО замещающего", data, errors, hint="необязательно")}</div>
</div>

<div class="card"><h3>Военкомат и план</h3>
{_field("commissariat", "Наименование военного комиссариата", data, errors, hint="как в его документах", attrs='placeholder="Военный комиссариат Центрального района г. Москвы"')}
<div class="grid two"><div><label for="year">План на год</label><select id="year" name="year">{years}</select>{err("year")}</div>
<div><label for="sverka_month">Месяц ежегодной сверки</label><select id="sverka_month" name="sverka_month">{months}</select>{err("sverka_month")}</div></div>
<label>Как подаёте сведения в военкомат</label>
{radio("submit_method", "epgu", "Через Госуслуги (нужна УКЭП)")}
{radio("submit_method", "paper", "На бумаге — лично или почтой")}{err("submit_method")}
</div>

<label class="radio"><input type="checkbox" name="consent" value="yes"{' checked' if data.get('consent') == 'yes' else ''}>
<span>Согласен с <a href="/offer" target="_blank">офертой</a> и <a href="/privacy" target="_blank">обработкой персональных данных</a>, указанных в анкете</span></label>{err("consent")}
<p><button class="btn block" type="submit">{'Сохранить и посмотреть' if edit else 'Посмотреть документы'}</button></p>
</form>
<script>
(function(){{var b=document.getElementById('resp-block');function t(){{var r=document.querySelector('input[name=mode]:checked');
b.style.display=(r&&r.value==='self')?'none':'block';}}document.querySelectorAll('input[name=mode]').forEach(function(x){{x.addEventListener('change',t)}});t();}})();
</script>"""
    return layout(s, "Данные для документов — ВУ·Пакет", body, goal="view_form", noindex=True)


def preview_page(s: Settings, order: dict, preview_html: str, doc_titles: list[str], pay_error: str = "") -> str:
    token = e(order["token"])
    d = order["data"]
    p = price_str(order["price_rub"])
    docs = "".join(f"<li>{e(t)}</li>" for t in doc_titles)
    demo_note = ""
    if not s.payments_ready and s.demo_payments:
        demo_note = '<div class="alert warn">Демо-режим: ЮKassa не подключена, кнопка ниже имитирует оплату без списания денег.</div>'
    err = f'<div class="alert err">{e(pay_error)}</div>' if pay_error else ""
    body = f"""
<h1>Проверьте данные</h1>
<div class="card small"><b>{e(d['org_short'])}</b>, ИНН {e(d['inn'])} · {e(d['head_position'])}: {e(d['head_name'])}<br>
Военкомат: {e(d['commissariat'])} · План на {e(str(d['year']))} год · Чек на {e(d['email'])}<br>
<a href="/order/{token}/edit">Изменить данные</a></div>
<h2>Предпросмотр приказа</h2>
<div class="fade">{preview_html}</div>
<h2>В архиве после оплаты</h2>
<ul class="check">{docs}<li>Файл напоминаний для календаря (.ics)</li></ul>
{err}{demo_note}
<div class="sticky-pay"><form method="post" action="/order/{token}/pay"><button class="btn block" type="submit">Оплатить {p} и скачать</button></form>
<p class="small muted" style="text-align:center;margin:8px 0 0">Карта или СБП через ЮKassa · чек на почту · возврат в течение 7 дней</p></div>
<p class="small muted">Сохраните ссылку на эту страницу — по ней можно вернуться к заказу.</p>"""
    return layout(s, "Предпросмотр — ВУ·Пакет", body, goal="view_preview", noindex=True)


def pending_page(s: Settings, order: dict) -> str:
    token = e(order["token"])
    body = f"""<h1>Ждём подтверждение оплаты</h1>
<div class="card"><p>Обычно это занимает несколько секунд. Страница обновится сама.</p>
<p class="small muted">Если вы закрыли окно оплаты, не заплатив, — вернитесь к <a href="/order/{token}?retry=1">предпросмотру</a> и нажмите «Оплатить» ещё раз.</p></div>
<meta http-equiv="refresh" content="5">"""
    return layout(s, "Проверяем оплату — ВУ·Пакет", body, noindex=True)


def paid_page(s: Settings, order: dict) -> str:
    token = e(order["token"])
    support = e(s.seller_email) if s.seller_email else "[почта поддержки не задана]"
    demo = '<div class="alert warn">Демо-оплата: деньги не списывались.</div>' if order.get("demo") else ""
    body = f"""<h1>Готово — пакет оплачен</h1>{demo}
<div class="card"><p>Архив: 6 документов Word и файл напоминаний для календаря.</p>
<a class="btn block" href="/order/{token}/download">Скачать архив (.zip)</a>
<p class="small muted">Ссылка на эту страницу действует, пока вы её храните: сохраните её в закладки или письме себе.</p></div>
<div class="card"><h3>Дальше</h3><ol class="steps"><li>Проверьте реквизиты и подпишите приказ и план у руководителя.</li>
<li>Отнесите или отправьте в военкомат проект приказа и план с письмом (файл 05).</li>
<li>Импортируйте файл 07 в календарь, чтобы не пропустить сверку и план на следующий год.</li></ol>
<p class="small">Вопросы и возврат: {support}</p></div>"""
    return layout(s, "Пакет готов — ВУ·Пакет", body, goal="payment_succeeded", noindex=True)


def sample_page(s: Settings, docs_html: str) -> str:
    body = f"""<h1>Пример документов</h1>
<p class="lead">Так выглядит пакет для вымышленной организации ООО «Пример». В вашем будут ваши реквизиты.</p>
{docs_html}
<p><a class="btn block" href="/form">Собрать пакет для своей организации</a></p>"""
    return layout(s, "Пример документов — ВУ·Пакет", body, goal="view_sample")


def message_page(s: Settings, title: str, text: str) -> str:
    return layout(s, title, f'<h1>{e(title)}</h1><div class="card"><p>{e(text)}</p><p><a href="/">На главную</a></p></div>', noindex=True)


def _seller(s: Settings) -> str:
    if s.seller_ready:
        return f"{e(s.seller_name)}, ИНН {e(s.seller_inn)}, e-mail {e(s.seller_email)}"
    return "[ЗАПОЛНИТЬ: наименование/ФИО продавца, ИНН, e-mail — переменные VU_SELLER_*]"


def offer_page(s: Settings) -> str:
    p = price_str(s.price_rub)
    body = f"""<h1>Публичная оферта</h1><div class="card small">
<p><b>ЧЕРНОВИК — проверьте с юристом перед запуском.</b></p>
<p>1. Продавец: {_seller(s)}.</p>
<p>2. Предмет: предоставление доступа к комплекту электронных шаблонов документов по воинскому учёту, автоматически заполненных данными, которые покупатель указал в анкете (далее — пакет).</p>
<p>3. Цена пакета — {p} за одну организацию. Оплата через ЮKassa. Доступ к скачиванию предоставляется сразу после подтверждения оплаты.</p>
<p>4. Пакет — шаблоны документов, а не юридическая консультация. Покупатель самостоятельно проверяет реквизиты, согласует документы с военным комиссариатом и отвечает за их использование.</p>
<p>5. Возврат: в течение 7 календарных дней с момента оплаты покупатель может запросить возврат полной суммы, написав продавцу на e-mail. Возврат производится тем же способом, которым была произведена оплата.</p>
<p>6. Акцепт оферты — оплата пакета.</p></div>"""
    return layout(s, "Оферта — ВУ·Пакет", body)


def privacy_page(s: Settings) -> str:
    body = f"""<h1>Обработка персональных данных</h1><div class="card small">
<p><b>ЧЕРНОВИК — проверьте с юристом; до запуска подайте уведомление в Роскомнадзор как оператор ПДн.</b></p>
<p>Оператор: {_seller(s)}.</p>
<p>Какие данные: ФИО и должности руководителя, ответственного и замещающего, e-mail для чека, реквизиты организации. Данные работников, паспорта и документы воинского учёта не запрашиваются.</p>
<p>Цель: подготовка документов по анкете и отправка кассового чека. Данные передаются ЮKassa только в объёме, нужном для оплаты и чека (e-mail и сумма).</p>
<p>Срок: анкеты без оплаты удаляются через {s.order_ttl_days} дней; оплаченные заказы хранятся для исполнения обязательств и возвратов.</p>
<p>Аналитика: события воронки сохраняются без анкетных данных; Яндекс Метрика (если подключена) работает без Вебвизора.</p>
<p>Отзыв согласия и удаление данных — по запросу на e-mail оператора.</p></div>"""
    return layout(s, "Персональные данные — ВУ·Пакет", body)


def admin_page(s: Settings, funnel: list[dict], orders: list[dict], revenue: dict, days: int) -> str:
    order_names = ["view_landing", "view_sample", "view_form", "form_invalid", "order_created", "view_preview",
                   "pay_click", "payment_created", "payment_error", "payment_succeeded", "download"]
    by_src: dict[str, dict] = {}
    for row in funnel:
        by_src.setdefault(row["src"], {})[row["name"]] = row["n"]
    head = "".join(f"<th>{n}</th>" for n in order_names)
    rows = "".join(
        f"<tr><td>{e(src)}</td>" + "".join(f"<td>{vals.get(n, 0)}</td>" for n in order_names) + "</tr>"
        for src, vals in by_src.items()
    )
    orows = "".join(
        f"<tr><td>{e(o['created_at'])}</td><td>{e(o['status'])}{' (демо)' if o['demo'] else ''}</td><td>{o['price_rub']}</td>"
        f"<td>{e(o['email'])}</td><td>{e(o['utm_source'] or '')}</td><td>{o['downloads']}</td><td>{e(o['payment_id'] or '')}</td></tr>"
        for o in orders
    )
    body = f"""<h1>Статистика за {days} дн.</h1>
<div class="card"><b>Реальные оплаты:</b> {revenue['n']} на {price_str(int(revenue['rub']))}
<p class="small muted">Оплаты — это заказы со статусом paid без демо-флага. Регистрации и клики не считаются оплатами.</p></div>
<div class="card" style="overflow-x:auto"><table class="stats"><tr><th>Источник</th>{head}</tr>{rows}</table></div>
<div class="card" style="overflow-x:auto"><table class="stats"><tr><th>Создан</th><th>Статус</th><th>₽</th><th>Почта</th><th>utm</th><th>Скачиваний</th><th>Платёж</th></tr>{orows}</table></div>"""
    return layout(s, "Статистика", body, noindex=True)
