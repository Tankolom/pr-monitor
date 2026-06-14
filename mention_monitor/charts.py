from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone

from .helpers import (
    add_months,
    compact_number,
    complete_period_rows,
    default_from_iso,
    display_date,
    display_period,
    esc,
    parse_date_only,
    pct,
    query_href,
    today_iso,
)

def tone_link(params: dict, sentiment: str) -> str:
    next_params = dict(params)
    next_params["sentiment"] = sentiment
    next_params.pop("feed_page", None)
    return query_href("/", next_params) + "#feed"


def tone_stack(pos: int, neu: int, neg: int, query_params: dict | None = None) -> str:
    total = max(pos + neu + neg, 1)
    pos_pct = pct(pos, total)
    neu_pct = pct(neu, total)
    neg_pct = max(0, 100 - pos_pct - neu_pct)
    balance = max(-100, min(100, pos_pct - neg_pct))
    params = query_params or {}
    return f"""
    <div class="card tone-card">
      <div class="chart-title"><h3>Репутационный фон <span class="help-dot" data-tip="Нажмите на позитив, нейтрально или негатив, чтобы открыть соответствующие публикации в ленте.">?</span></h3><span>{total} упоминаний · баланс {balance:+d}</span></div>
      <div class="tone-segments" role="img" aria-label="Позитив {pos_pct}%, нейтрально {neu_pct}%, негатив {neg_pct}%">
        <a class="tone-seg-pos" href="{esc(tone_link(params, 'positive'))}" style="width:{pos_pct}%"><span class="sr-only">Позитив</span></a>
        <a class="tone-seg-neu" href="{esc(tone_link(params, 'neutral'))}" style="width:{neu_pct}%"><span class="sr-only">Нейтрально</span></a>
        <a class="tone-seg-neg" href="{esc(tone_link(params, 'negative'))}" style="width:{neg_pct}%"><span class="sr-only">Негатив</span></a>
      </div>
      <div class="tone-funnel-metrics">
        <a class="tone-stage tone-stage-link positive" href="{esc(tone_link(params, 'positive'))}"><span>Позитив</span><b>{pos}</b><small>{pos_pct}% публикаций</small></a>
        <a class="tone-stage tone-stage-link" href="{esc(tone_link(params, 'neutral'))}"><span>Нейтрально</span><b>{neu}</b><small>{neu_pct}% публикаций</small></a>
        <a class="tone-stage tone-stage-link negative" href="{esc(tone_link(params, 'negative'))}"><span>Негатив</span><b>{neg}</b><small>{neg_pct}% публикаций</small></a>
      </div>
    </div>
    """


def daily_period_range(value: str, bucket: str) -> tuple[str, str]:
    if bucket == "month":
        match = re.match(r"(\d{4})-(\d{2})", value or "")
        if match:
            year, month = map(int, match.groups())
            start = datetime(year, month, 1, tzinfo=timezone.utc).date()
            end = (add_months(start, 1) - timedelta(days=1))
            return start.isoformat(), end.isoformat()
    if bucket == "week":
        match = re.match(r"(\d{4})-W(\d{1,2})", value or "")
        if match:
            year, week = map(int, match.groups())
            try:
                start = datetime.strptime(f"{year}-W{week:02d}-1", "%Y-W%W-%w").date()
                return start.isoformat(), (start + timedelta(days=6)).isoformat()
            except ValueError:
                pass
    day = parse_date_only(value)
    if day:
        return day.isoformat(), day.isoformat()
    return "", ""


def daily_period_href(value: str, bucket: str, params: dict) -> str:
    start, end = daily_period_range(value, bucket)
    next_params = dict(params)
    if start:
        next_params["collected_from"] = start
    if end:
        next_params["collected_to"] = end
    next_params.pop("feed_page", None)
    return query_href("/", next_params) + "#feed"


def daily_chart(rows, days: int = 14, bucket: str = "day", query_params: dict | None = None) -> str:
    rows = list(rows)
    max_value = max([int(row["n"]) for row in rows], default=0) or 1
    total_value = sum(int(row["n"]) for row in rows)
    width = 760
    height = 260
    left = 52
    right = 24
    top = 28
    bottom = 44
    plot_w = width - left - right
    plot_h = height - top - bottom
    grid = ""
    for step in range(4):
        ratio = step / 3
        y = top + plot_h - plot_h * ratio
        label_value = round(max_value * ratio)
        grid += f"<line class='daily-grid' x1='{left}' x2='{width - right}' y1='{y:.1f}' y2='{y:.1f}'/>"
        grid += f"<text x='{left - 12}' y='{y + 4:.1f}' text-anchor='end'>{label_value}</text>"
    bars_svg = ""
    x_labels = ""
    if rows:
        slot = plot_w / max(1, len(rows))
        bar_w = min(34, max(6, slot * 0.60))
        label_indexes = sorted({0, len(rows) // 2, len(rows) - 1} if len(rows) > 2 else set(range(len(rows))))
        for index, row in enumerate(rows):
            value = int(row["n"])
            period = str(row["day"] or "")
            label = display_period(period, bucket, period)
            bar_h = 2 if value <= 0 else max(4, value / max_value * plot_h)
            x = left + slot * index + (slot - bar_w) / 2
            y = top + plot_h - bar_h
            href = daily_period_href(period, bucket, query_params or {})
            bar_class = "daily-bar daily-bar-zero" if value <= 0 else "daily-bar"
            bars_svg += (
                f"<a href='{esc(href)}'><rect class='{bar_class}' x='{x:.1f}' y='{y:.1f}' "
                f"width='{bar_w:.1f}' height='{bar_h:.1f}' rx='3'><title>{esc(label)}: {value}</title></rect></a>"
            )
            if index in label_indexes:
                x_labels += f"<text x='{x + bar_w / 2:.1f}' y='{height - 12}' text-anchor='middle'>{esc(label)}</text>"
    daily_svg = (
        f"<svg class='daily-svg' viewBox='0 0 {width} {height}' preserveAspectRatio='none' role='img' aria-label='Динамика по датам'>"
        f"{grid}<line class='daily-axis' x1='{left}' x2='{width - right}' y1='{top + plot_h:.1f}' y2='{top + plot_h:.1f}'/>"
        f"{bars_svg}{x_labels}</svg>"
    ) if rows else '<span class="muted">нет данных</span>'
    params = query_params or {}
    hidden = "".join(
        f'<input type="hidden" name="{esc(key)}" value="{esc(value)}">'
        for key, value in params.items()
        if key not in {"daily_days", "daily_bucket", "collected_from", "collected_to", "feed_page"}
    )
    collected_from = str(params.get("collected_from") or default_from_iso(90))
    collected_to = str(params.get("collected_to") or today_iso())
    bucket_options = "".join(
        f'<option value="{value}" {"selected" if bucket == value else ""}>{label}</option>'
        for value, label in [("day", "по дням"), ("week", "по неделям"), ("month", "по месяцам")]
    )
    period_label = f"{display_date(collected_from)} — {display_date(collected_to)}"
    nonzero_rows = [dict(row) for row in rows if int(row["n"]) > 0]
    peak = max(nonzero_rows, key=lambda row: int(row["n"]), default=None)
    active_count = len(nonzero_rows)
    avg_value = round(total_value / max(1, active_count), 1) if rows else 0
    last_active = nonzero_rows[-1] if nonzero_rows else None
    peak_label = display_period(str(peak["day"]), bucket, str(peak["day"])) if peak else "нет"
    peak_value = int(peak["n"]) if peak else 0
    peak_href = daily_period_href(str(peak["day"]), bucket, params) if peak else "#feed"
    last_label = display_period(str(last_active["day"]), bucket, str(last_active["day"])) if last_active else "нет"
    top_days = sorted(nonzero_rows, key=lambda row: int(row["n"]), reverse=True)[:3]
    top_day_rows = "".join(
        f"<a href='{esc(daily_period_href(str(row['day']), bucket, params))}'>"
        f"<span>{esc(display_period(str(row['day']), bucket, str(row['day'])))}</span><b>{int(row['n'])}</b></a>"
        for row in top_days
    )
    daily_insights = f"""
      <div class='daily-insights'>
        <a class='daily-insight daily-insight-peak' href='{esc(peak_href)}'>
          <span>Пик периода</span><b>{esc(peak_label)}</b><em>{peak_value} публикаций</em>
        </a>
        <div class='daily-insight'>
          <span>Активные дни</span><b>{active_count}</b><em>из {len(rows) or 0}</em>
        </div>
        <div class='daily-insight'>
          <span>Среднее</span><b>{avg_value}</b><em>публикаций в активный день</em>
        </div>
        <div class='daily-insight'>
          <span>Последняя активность</span><b>{esc(last_label)}</b><em>{int(last_active['n']) if last_active else 0} публикаций</em>
        </div>
      </div>
      <div class='daily-top-days'>
        <div><b>Топ дней</b><span>быстрый переход к ленте</span></div>
        <nav>{top_day_rows or '<span class="muted">нет активных дней</span>'}</nav>
      </div>
    """
    return f"""
    <div class='card'>
      <div class='widget-title'>
        <h3>Динамика по датам</h3>
        <div class='widget-tools'>
          <button class='gear' type='button' title='Настроить период' aria-label='Настроить период'><svg viewBox='0 0 24 24' width='18' height='18' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='M12 15.5a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7Z'/><path d='M19.4 15a1.7 1.7 0 0 0 .34 1.88l.05.05a2 2 0 1 1-2.83 2.83l-.05-.05A1.7 1.7 0 0 0 15 19.37a1.7 1.7 0 0 0-1 .58V20a2 2 0 1 1-4 0v-.07a1.7 1.7 0 0 0-1-.56 1.7 1.7 0 0 0-1.88.34l-.05.05a2 2 0 1 1-2.83-2.83l.05-.05A1.7 1.7 0 0 0 4.63 15a1.7 1.7 0 0 0-.58-1H4a2 2 0 1 1 0-4h.07a1.7 1.7 0 0 0 .56-1 1.7 1.7 0 0 0-.34-1.88l-.05-.05a2 2 0 1 1 2.83-2.83l.05.05A1.7 1.7 0 0 0 9 4.63a1.7 1.7 0 0 0 1-.58V4a2 2 0 1 1 4 0v.07a1.7 1.7 0 0 0 1 .56 1.7 1.7 0 0 0 1.88-.34l.05-.05a2 2 0 1 1 2.83 2.83l-.05.05A1.7 1.7 0 0 0 19.37 9c.2.35.4.7.58 1H20a2 2 0 1 1 0 4h-.07a1.7 1.7 0 0 0-.53 1Z'/></svg></button>
          <form class='widget-settings' method='get' action='/' data-scroll-target='analytics'>
            {hidden}
            <h4>Период графика</h4>
            <div class='field'>
              <label>С</label>
              <input class='input' type='date' name='collected_from' value='{esc(collected_from)}'>
            </div>
            <div class='field'>
              <label>По</label>
              <input class='input' type='date' name='collected_to' value='{esc(collected_to)}'>
            </div>
            <div class='field'>
              <label>Группировка</label>
              <select class='select' name='daily_bucket'>{bucket_options}</select>
            </div>
            <button class='btn' type='submit'>Применить</button>
            <div class='mini-help'>Настройка меняет только этот виджет, остальные фильтры сохраняются.</div>
          </form>
        </div>
      </div>
      <div class='period-summary'><span>период: <b>{esc(period_label)}</b></span><span>сумма: <b>{total_value}</b></span><span>{esc(trend_label(bucket))}</span></div>
      <div class='spark-scroll'>{daily_svg}</div>
      {daily_insights}
    </div>
    """


def trend_label(bucket: str) -> str:
    return {"day": "по дням", "week": "по неделям", "month": "по месяцам"}.get(bucket, "по месяцам")


def compact_period_label(value: str, bucket: str) -> str:
    return display_period(value, bucket, value)


def trend_scale_labels(values, bucket: str) -> list[str]:
    if not values:
        return []
    labels = [compact_period_label(values[0][0], bucket)]
    if len(values) > 2:
        labels.append(compact_period_label(values[len(values) // 2][0], bucket))
    if len(values) > 1:
        labels.append(compact_period_label(values[-1][0], bucket))
    return labels


def smooth_svg_path(points: list[tuple[float, float, str, int]]) -> str:
    if not points:
        return ""
    if len(points) == 1:
        x, y, _, _ = points[0]
        return f"M {x:.1f},{y:.1f}"
    path = f"M {points[0][0]:.1f},{points[0][1]:.1f}"
    for index in range(len(points) - 1):
        x0, y0, _, _ = points[index]
        x1, y1, _, _ = points[index + 1]
        dx = (x1 - x0) * 0.42
        path += f" C {x0 + dx:.1f},{y0:.1f} {x1 - dx:.1f},{y1:.1f} {x1:.1f},{y1:.1f}"
    return path


def mention_trend_chart(rows, bucket: str, months: int, query_params: dict | None = None) -> str:
    values = [(row["period"] or "нет даты", int(row["n"])) for row in rows]
    total_value = sum(value for _, value in values)
    params = query_params or {}
    hidden = "".join(
        f'<input type="hidden" name="{esc(key)}" value="{esc(value)}">'
        for key, value in params.items()
        if key not in {"trend_bucket", "trend_months", "collected_from", "collected_to", "feed_page"}
    )
    collected_from = str(params.get("collected_from") or default_from_iso(90))
    collected_to = str(params.get("collected_to") or today_iso())
    bucket_options = "".join(
        f'<option value="{value}" {"selected" if bucket == value else ""}>{label}</option>'
        for value, label in [("month", "месяц"), ("week", "неделя"), ("day", "день")]
    )
    if not values:
        chart = '<div class="trend-chart"><span class="muted">нет данных для выбранного периода</span></div>'
    else:
        width = 980
        height = 310
        left = 58
        right = 34
        top = 34
        bottom = 42
        plot_w = width - left - right
        plot_h = height - top - bottom
        max_value = max([value for _, value in values], default=1) or 1
        min_value = min([value for _, value in values], default=0)
        if len(values) == 1:
            points = [(left + plot_w / 2, top + plot_h - (values[0][1] / max_value * plot_h * 0.82), values[0][0], values[0][1])]
        else:
            points = []
            for index, (period, value) in enumerate(values):
                x = left + (plot_w * index / (len(values) - 1))
                y = top + plot_h - (value / max_value * plot_h * 0.82)
                points.append((x, y, period, value))
        line = smooth_svg_path(points)
        area = f"M {points[0][0]:.1f},{top + plot_h:.1f} L " + line[2:] + f" L {points[-1][0]:.1f},{top + plot_h:.1f} Z"
        max_point = max(points, key=lambda point: point[3])
        min_point = min(points, key=lambda point: point[3])
        active_index = points.index(max_point)
        dot_points = {0, len(points) - 1, active_index, points.index(min_point)}
        grid = ""
        for step in range(5):
            ratio = step / 4
            y = top + plot_h - plot_h * ratio
            label_value = round(max_value * ratio)
            grid += f"<line class='trend-grid' x1='{left}' x2='{width - right}' y1='{y:.1f}' y2='{y:.1f}'/>"
            grid += f"<text class='trend-y-label' x='{left - 14}' y='{y + 4:.1f}' text-anchor='end'>{label_value}</text>"
        dots = ""
        tooltip_w = 128
        tooltip_h = 54
        for index, (x, y, period, value) in enumerate(points):
            point_label = compact_period_label(period, bucket)
            point_tip_x = min(max(left, x - tooltip_w / 2), width - right - tooltip_w)
            point_tip_y = max(8, y - tooltip_h - 20)
            point_band_x = max(left, x - 20)
            point_pointer = f"M {x - 7:.1f},{point_tip_y + tooltip_h - 1:.1f} L {x:.1f},{point_tip_y + tooltip_h + 9:.1f} L {x + 7:.1f},{point_tip_y + tooltip_h - 1:.1f} Z"
            attrs = (
                f"data-x='{x:.1f}' data-y='{y:.1f}' data-label='{esc(point_label)}' data-value='{value}' "
                f"data-tip-x='{point_tip_x:.1f}' data-tip-y='{point_tip_y:.1f}' data-band-x='{point_band_x:.1f}' "
                f"data-pointer='{esc(point_pointer)}'"
            )
            if index == active_index:
                dots += f"<circle class='trend-point trend-dot' {attrs} cx='{x:.1f}' cy='{y:.1f}' r='7'><title>{esc(point_label)}: {value}</title></circle>"
            elif index in dot_points:
                dots += f"<circle class='trend-point trend-dot-muted' {attrs} cx='{x:.1f}' cy='{y:.1f}' r='5'><title>{esc(point_label)}: {value}</title></circle>"
            else:
                dots += f"<circle class='trend-point trend-dot-muted' {attrs} cx='{x:.1f}' cy='{y:.1f}' r='4'><title>{esc(point_label)}: {value}</title></circle>"
        x_labels = ""
        label_indexes = sorted({0, len(points) // 2, len(points) - 1} if len(points) > 2 else set(range(len(points))))
        for index in label_indexes:
            x, _, period, _ = points[index]
            x_labels += f"<text class='trend-x-label' x='{x:.1f}' y='{height - 12}' text-anchor='middle'>{esc(compact_period_label(period, bucket))}</text>"
        active_x, active_y, active_period, active_value = max_point
        tooltip_x = min(max(left, active_x - tooltip_w / 2), width - right - tooltip_w)
        tooltip_y = max(8, active_y - tooltip_h - 20)
        pointer_x = active_x
        band_x = max(left, active_x - 20)
        summary = (
            f"<div class='trend-summary'><span>минимум: <b>{min_value}</b></span>"
            f"<span>максимум: <b>{max_value}</b></span></div>"
        )
        chart = f"""
        <div class="trend-chart">
          <svg viewBox="0 0 {width} {height}" preserveAspectRatio="none" role="img" aria-label="Динамика упоминаний">
            <defs>
              <linearGradient id="trendFill" x1="0" x2="0" y1="0" y2="1">
                <stop offset="0%" stop-color="#28457A" stop-opacity=".16"/>
                <stop offset="100%" stop-color="#28457A" stop-opacity="0"/>
              </linearGradient>
              <linearGradient id="trendPanel" x1="0" x2="1" y1="0" y2="1">
                <stop offset="0%" stop-color="#ffffff" stop-opacity=".28"/>
                <stop offset="100%" stop-color="#ffffff" stop-opacity=".10"/>
              </linearGradient>
              <linearGradient id="trendBand" x1="0" x2="0" y1="0" y2="1">
                <stop offset="0%" stop-color="#28457A" stop-opacity=".10"/>
                <stop offset="100%" stop-color="#28457A" stop-opacity="0"/>
              </linearGradient>
            </defs>
            <rect class="trend-panel-bg" x="0" y="0" width="{width}" height="{height}" rx="18"/>
            {grid}
            <rect class="trend-active-band" x="{band_x:.1f}" y="{top}" width="40" height="{plot_h}" rx="16"/>
            <path class="trend-area" d="{area}"/>
            <path class="trend-line" d="{line}"/>
            {dots}
            {x_labels}
            <g>
              <rect class="trend-tooltip trend-tooltip-box" x="{tooltip_x:.1f}" y="{tooltip_y:.1f}" width="{tooltip_w}" height="{tooltip_h}" rx="10"/>
              <path class="trend-tooltip trend-tooltip-pointer" d="M {pointer_x - 7:.1f},{tooltip_y + tooltip_h - 1:.1f} L {pointer_x:.1f},{tooltip_y + tooltip_h + 9:.1f} L {pointer_x + 7:.1f},{tooltip_y + tooltip_h - 1:.1f} Z"/>
              <text class="trend-tooltip-title" x="{tooltip_x + 16:.1f}" y="{tooltip_y + 20:.1f}">{esc(compact_period_label(active_period, bucket))}</text>
              <text class="trend-tooltip-value" x="{tooltip_x + 16:.1f}" y="{tooltip_y + 42:.1f}">{active_value}</text>
            </g>
          </svg>
        </div>
        {summary}
        <script>
        document.addEventListener('click', function(event) {{
          const point = event.target.closest('.trend-point');
          if (!point) return;
          const svg = point.closest('svg');
          if (!svg) return;
          svg.querySelectorAll('.trend-point').forEach(function(item) {{
            item.classList.remove('trend-dot');
            item.classList.add('trend-dot-muted');
            item.setAttribute('r', '4');
          }});
          point.classList.remove('trend-dot-muted');
          point.classList.add('trend-dot');
          point.setAttribute('r', '7');
          const band = svg.querySelector('.trend-active-band');
          const box = svg.querySelector('.trend-tooltip-box');
          const pointer = svg.querySelector('.trend-tooltip-pointer');
          const title = svg.querySelector('.trend-tooltip-title');
          const value = svg.querySelector('.trend-tooltip-value');
          const tipX = Number(point.dataset.tipX || 0);
          const tipY = Number(point.dataset.tipY || 0);
          if (band) band.setAttribute('x', point.dataset.bandX || point.getAttribute('cx'));
          if (box) {{
            box.setAttribute('x', tipX);
            box.setAttribute('y', tipY);
          }}
          if (pointer) pointer.setAttribute('d', point.dataset.pointer || '');
          if (title) {{
            title.textContent = point.dataset.label || '';
            title.setAttribute('x', tipX + 16);
            title.setAttribute('y', tipY + 20);
          }}
          if (value) {{
            value.textContent = point.dataset.value || '';
            value.setAttribute('x', tipX + 16);
            value.setAttribute('y', tipY + 42);
          }}
        }});
        </script>
        """
    return f"""
    <div class="card viz-wide trend-card">
      <div class="chart-title">
        <h3>Динамика упоминаний <span class="help-dot" data-tip="Период задается датами. Для длинного периода лучше выбрать группировку по неделям или месяцам.">?</span></h3>
        <form class="trend-controls" method="get" action="/" data-scroll-target="analytics">
          {hidden}
          <input class="input" type="date" name="collected_from" value="{esc(collected_from)}">
          <input class="input" type="date" name="collected_to" value="{esc(collected_to)}">
          <select class="select" name="trend_bucket">{bucket_options}</select>
          <button class="btn light" type="submit">Показать</button>
        </form>
      </div>
      <div class='period-summary'><span>период: <b>{esc(display_date(collected_from))} — {esc(display_date(collected_to))}</b></span><span>сумма: <b>{total_value}</b></span><span>{esc(trend_label(bucket))}</span></div>
      {chart}
    </div>
    """


def source_bucket(source: str, url: str | None = None) -> tuple[str, str, str]:
    lower = f"{source or ''} {url or ''}".lower()
    if any(x in lower for x in ["vk.com", "telegram", "t.me", "youtube", "instagram", "dzen.ru", "zen.yandex"]):
        return ("Соцплатформы", "S", "посты, каналы, видео")
    sports_markers = [
        "championat.com",
        "sports.ru",
        "sport24.ru",
        "sport-express.ru",
        "sportbox.ru",
        "matchtv.ru",
        "rsport.ria.ru",
        "stavkinasport",
        "ставкинаспорт",
        "небесная грация",
        "вфв",
        "всероссийская федерация волейбола",
    ]
    if any(x in lower for x in sports_markers):
        return ("Спортивные медиа", "P", "профильная спортивная повестка")
    if any(x in lower for x in ["ria.ru", "риа новости", "tass", "тасс", "interfax", "интерфакс", "rbc", "рбк", "lenta.ru", "лента.ру", "kommersant", "коммерсант", "vedomosti", "ведомости", "rg.ru", "российская газета", "iz.ru", "известия", "forbes", "форбс"]):
        return ("Федеральные СМИ", "F", "крупные федеральные площадки")
    if any(x in lower for x in ["клопс", "klops", "калининград", "kgd", "baltic", "область", "регион", "nia", "newkaliningrad", "новый калининград", "obltv", "orenburg", "нижегород", "тюмен"]):
        return ("Региональные СМИ", "R", "локальная и региональная повестка")
    if any(x in lower for x in ["google news", "news.google", "mail", "dzen", "яндекс", "yandex"]):
        return ("Агрегаторы", "A", "поисковая и новостная выдача")
    if any(x in lower for x in ["2gis", "reputation", "companium", "fbc.ru", "cataloxy", "yp.ru", "wikipedia"]):
        return ("Справочники", "D", "карточки, базы и каталоги")
    if any(x in lower for x in [".ru", ".рф", "news", "медиа", "газета"]):
        return ("Онлайн-СМИ", "M", "сайты и малые редакции")
    return ("Другие площадки", "O", "источники без классификации")


def source_mix_chart(mentions, query_params: dict | None = None) -> str:
    params = query_params or {}
    mix = {}
    unique_sources: dict[str, set[str]] = {}
    source_details: dict[str, dict[str, int]] = {}
    for item in mentions:
        label, icon, hint = source_bucket(item["source"] or "", item["url"] if "url" in item.keys() else "")
        if label not in mix:
            mix[label] = {"label": label, "icon": icon, "hint": hint, "n": 0}
            unique_sources[label] = set()
            source_details[label] = {}
        mix[label]["n"] += 1
        source_name = item["source"] or "unknown"
        unique_sources[label].add(source_name)
        source_details[label][source_name] = source_details[label].get(source_name, 0) + 1
    rows = sorted(mix.values(), key=lambda item: item["n"], reverse=True)
    total = sum(row["n"] for row in rows)
    dominant = rows[0] if rows else {"label": "нет данных", "n": 0, "icon": "◌", "hint": "запустите сбор"}
    cards = ""
    for row in rows[:6]:
        share = pct(row["n"], total)
        sources_count = len(unique_sources.get(row["label"], set()))
        detail_items = "".join(
            f"<li><a href='{esc(query_href('/', {**params, 'q': source, 'feed_page': ''}) + '#feed')}'>{esc(source)}</a><em>{count}</em></li>"
            for source, count in sorted(
                source_details.get(row["label"], {}).items(),
                key=lambda item: (-item[1], item[0].lower()),
            )[:10]
        )
        detail_more = max(0, sources_count - 10)
        cards += f"""
        <details class="source-orbit-card">
          <summary>
            <div class="source-orbit-icon">{esc(row["icon"])}</div>
            <div class="source-orbit-main">
              <div class="source-orbit-top"><b>{esc(row["label"])}</b><span>{share}%</span></div>
              <div class="source-orbit-track"><i style="width:{share}%"></i></div>
              <p>{esc(row["hint"])}</p>
              <small>{row["n"]} публикаций · {sources_count} источников · открыть список</small>
            </div>
          </summary>
          <div class="source-orbit-detail">
            <b>Площадки внутри типа</b>
            <ul>{detail_items}{f'<li><span>Еще источников</span><em>+{detail_more}</em></li>' if detail_more else ''}</ul>
          </div>
        </details>
        """
    return f"""
    <div class="card source-orbit viz-wide">
      <div class="chart-title"><h3>Карта медиа-поля</h3><span>{len(rows)} типов площадок · {total} публикаций</span></div>
      <div class="source-orbit-layout">
        <div class="source-orbit-core">
          <div class="source-ring" style="--p:{pct(dominant['n'], total)}">
            <span>{esc(dominant["icon"])}</span>
          </div>
          <b>{esc(dominant["label"])}</b>
          <p>{dominant["n"]} публикаций в ведущем типе</p>
        </div>
        <div class="source-orbit-list">{cards or '<span class="muted">Площадки появятся после сбора.</span>'}</div>
      </div>
    </div>
    """


def metrics_catalog() -> str:
    metrics = [
        (
            "Охват",
            "аудитория источника",
            "Показывает потенциальное количество людей, которые могли увидеть публикацию.",
            ["Нужны данные посещаемости СМИ, подписчики каналов, просмотры постов.", "В MVP пока считается только количество источников."],
        ),
        (
            "Влиятельность",
            "вес СМИ или канала",
            "Помогает отличить публикацию в крупном СМИ от записи в малом каталоге.",
            ["Нужен рейтинг источника: ИЦ, Similarweb, подписчики, PageRank или ручной вес.", "Можно добавить таблицу весов источников."],
        ),
        (
            "Заметность",
            "заголовок, главная роль, цитата",
            "Оценивает, насколько объект заметен внутри материала, а не просто упомянут мельком.",
            ["Нужно определять наличие бренда в заголовке, лид-абзаце и цитатах.", "Часть можно считать из текста уже сейчас."],
        ),
        (
            "Вовлеченность",
            "лайки, репосты, комментарии",
            "Ключевая метрика для соцсетей и Telegram: показывает реакцию аудитории.",
            ["Нужны API VK, Telegram/сторонний поиск, YouTube.", "После токенов можно сохранять лайки/репосты/комментарии."],
        ),
        (
            "Доля негатива",
            "репутационный риск",
            "Показывает, какая часть публикаций несет риск для репутации.",
            ["Сейчас уже есть базовая тональность.", "Для качества нужна ручная корректировка и словарь тональности."],
        ),
        (
            "Динамика",
            "рост/падение упоминаний",
            "Показывает всплески активности и эффект инфоповодов.",
            ["Сейчас считается по датам публикации/сбора.", "Нужно добавить сравнение с прошлым периодом."],
        ),
        (
            "География",
            "регионы и страны",
            "Показывает, где именно обсуждают объект.",
            ["Нужно извлекать регион источника и локации из текста.", "Можно начать со справочника источников."],
        ),
        (
            "Дубли",
            "перепечатки и первоисточник",
            "Нужны, чтобы отличать один инфоповод от десятков перепечаток.",
            ["Сейчас есть защита от одинаковых ссылок.", "Нужно добавить похожесть текстов и группировку сюжетов."],
        ),
    ]
    body = ""
    for name, desc, explanation, bullets in metrics:
        bullet_html = "".join(f"<li>{esc(item)}</li>" for item in bullets)
        body += (
            "<details class='metric-pill'>"
            f"<summary><b>{esc(name)}</b><span class='muted'>{esc(desc)}</span></summary>"
            f"<div class='metric-detail'><p>{esc(explanation)}</p><ul>{bullet_html}</ul></div>"
            "</details>"
        )
    return f"<div class='card viz-wide'><div class='chart-title'><h3>Какие метрики стоит смотреть дальше</h3><span>для полноценной PR-аналитики</span></div><div class='metric-list'>{body}</div></div>"


