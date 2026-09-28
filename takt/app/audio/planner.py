"""Выбор мест склейки так, чтобы трек стал нужной длины.

Сокращение: перепрыгиваем вперёд с границы i на границу j (j > i), выкидывая [b_i, b_j).
Удлинение: прыгаем назад (j < i) и повторяем фрагмент [b_j, b_i).
Остаток погрешности добираем незаметным изменением темпа (±3 %).
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .analysis import Analysis

MAX_STRETCH = 0.03        # максимум изменения темпа
STRETCH_WEIGHT = 6.0      # штраф за 1 % темпа = 0.06
EXTRA_JUMP = 0.12         # штраф за каждую дополнительную склейку


@dataclass
class Plan:
    segments: list[tuple[float, float]]            # отрезки исходника, по порядку
    seams: list[tuple[int, int]] = field(default_factory=list)  # (i, j) границы
    seam_costs: list[float] = field(default_factory=list)
    stretch: float = 1.0                           # out_len / target
    kind: str = "cut"                              # cut | extend | stretch | fade
    score: float = 0.0
    fade_out: float = 0.0                          # длительность затухания в конце, с
    rhythm_errors: list = field(default_factory=list)  # самопроверка ритма на стыках (после рендера)

    @property
    def length(self) -> float:
        return sum(b - a for a, b in self.segments)


def boundary_novelty(d: np.ndarray, w: int = 2) -> np.ndarray:
    """Новизна на каждой границе (Foote): насколько блок единиц до границы отличается от блока после."""
    n = len(d)
    nov = np.zeros(n + 1)
    for k in range(1, n):
        a0, b1 = max(k - w, 0), min(k + w, n)
        cross = d[a0:k, k:b1].mean()
        within = (d[a0:k, a0:k].mean() + d[k:b1, k:b1].mean()) / 2
        nov[k] = cross - within
    return nov


def jump_costs(an: Analysis) -> np.ndarray:
    """C[i, j] — насколько заметен прыжок с начала единицы i на начало единицы j (0 — незаметно).

    Два способа сделать стык незаметным:
      1) «похожесть»: после склейки звучит то же, что звучало бы без неё (повтор припева и т. п.);
      2) «граница раздела»: и в i, и в j музыка и так меняется (конец куплета → начало финального
         припева) — слушатель ждёт смену, поэтому стык звучит как задуманный переход.
    """
    d = an.dist
    n = len(d)
    C = np.zeros((n, n))
    W = np.zeros((n, n))
    # (сдвиг контекста, вес): такт после склейки и такт до неё важнее дальних
    for off, w in ((0, 1.0), (-1, 1.0), (1, 0.5), (-2, 0.5)):
        idx = np.arange(n)
        src = idx + off
        ok = (src >= 0) & (src < n)
        s = src[ok]
        C[np.ix_(idx[ok], idx[ok])] += w * d[np.ix_(s, s)]
        W[np.ix_(idx[ok], idx[ok])] += w
    C = C / np.maximum(W, 1e-9)
    # стык на границах разделов
    nov = boundary_novelty(d)[:n]
    rank = np.argsort(np.argsort(nov)) / max(n - 1, 1)          # 0..1, 1 — самая яркая граница
    sec = 0.42 + 0.35 * ((1 - rank)[:, None] + (1 - rank)[None, :]) / 2
    # гармония: такт перед склейкой и такт после не должны «спорить» по тональности
    sec += 0.15 * np.clip(d[np.r_[0, np.arange(n - 1)]][:, :] - 0.6, 0, 1)
    C = np.minimum(C, sec)
    # скачок громкости сверх естественного
    loud = an.rms_db
    prev = np.r_[loud[0], loud[:-1]]                # громкость единицы перед границей i
    natural = np.abs(prev - loud)                   # как меняется громкость без склейки
    jump = np.abs(prev[:, None] - loud[None, :])
    allowed = np.maximum(natural[:, None], natural[None, :])
    C += 0.03 * np.maximum(jump - allowed - 2.0, 0)
    # темп в точке ухода и в точке входа должен совпадать (живые записи «гуляют»)
    if len(an.beats) > 8:
        ibi = np.diff(an.beats)
        centers = an.beats[1:]
        starts = an.bounds[:n]
        idx = np.clip(np.searchsorted(centers, starts), 2, len(ibi) - 3)
        local = np.array([np.median(ibi[max(k - 4, 0):k + 4]) for k in idx])
        ratio = np.abs(np.log(local[:, None] / local[None, :]))
        C += 4.0 * np.maximum(ratio - 0.015, 0)
    # музыкальные фразы: прыжки на кратное 4/8 тактам звучат естественнее
    if an.unit == "bar":
        delta = np.abs(np.arange(n)[:, None] - np.arange(n)[None, :])
        C += np.where(delta % 4 != 0, 0.2, np.where(delta % 8 != 0, 0.04, 0.0))
    np.fill_diagonal(C, np.inf)
    return C


def _stretch_ok(length: float, target: float) -> bool:
    return abs(length / target - 1) <= MAX_STRETCH + 1e-9


def _score(costs: list[float], length: float, target: float) -> float:
    return float(sum(costs) + EXTRA_JUMP * max(len(costs) - 1, 0) + STRETCH_WEIGHT * abs(length / target - 1))


def _protected(an: Analysis, target: float) -> tuple[int, int]:
    """Индексы границ, между которыми разрешено резать (сохраняем вступление и финал)."""
    b = an.bounds
    head = min(8.0, 0.1 * target)
    tail = min(10.0, 0.12 * target)
    lo = int(np.searchsorted(b, an.music_start + head))
    hi = int(np.searchsorted(b, an.music_end - tail, side="right")) - 1
    lo = max(lo, 1)
    hi = min(hi, len(b) - 2)
    return lo, hi


def _dp_shorten(an: Analysis, C: np.ndarray, target: float, max_jumps: int = 3, q: float = 0.1,
                top_k: int = 48) -> list[Plan]:
    """Лучшая цепочка прыжков вперёд (1–max_jumps) с итоговой длиной ≈ target.

    Динамика по границам единиц: f[k, t, c] — минимальная «заметность» склеек, если мы стоим
    на границе k, уже проиграли t (в шагах q секунд) и сделали c прыжков. После прыжка
    обязательно звучат ≥ 2 единицы, чтобы склейки не шли подряд.
    """
    b, ms, me = an.bounds, an.music_start, an.music_end
    n = len(b) - 1                       # число единиц
    lo, hi = _protected(an, target)
    if hi - lo < 2 or n < 4:
        return []
    head = b[0] - ms                     # затакт до первой сильной доли
    tail = me - b[n]
    lo_len, hi_len = target * (1 - MAX_STRETCH), target * (1 + MAX_STRETCH)
    T = int(np.ceil((hi_len - head - tail) / q)) + 1
    if T <= 0:
        return []
    dur = np.diff(b)
    step = np.maximum(np.round(dur / q).astype(int), 1)
    INF = np.inf
    f = np.full((n + 1, T, max_jumps + 1), INF)
    # указатели для восстановления: откуда пришли (k, t, c) и был ли прыжок
    pk = np.full((n + 1, T, max_jumps + 1), -1, dtype=np.int32)
    pt = np.zeros((n + 1, T, max_jumps + 1), dtype=np.int32)
    pc = np.zeros((n + 1, T, max_jumps + 1), dtype=np.int8)
    f[0, 0, 0] = 0.0
    # кандидаты прыжков из каждой границы: лучшие top_k по стоимости
    cand: list[np.ndarray] = []
    for k in range(n + 1):
        if lo <= k <= hi:
            js = np.arange(k + 2, min(hi, n - 2) + 1)
            js = js[np.isfinite(C[k, js])] if k < len(C) else js[:0]
            if len(js) > top_k:
                js = js[np.argsort(C[k, js])[:top_k]]
        else:
            js = np.array([], dtype=int)
        cand.append(js)
    for k in range(n):
        row = f[k]
        if not np.isfinite(row).any():
            continue
        s = step[k]
        # просто играем единицу k
        if s < T:
            src = row[:T - s]
            dst = f[k + 1, s:]
            better = src < dst
            if better.any():
                dst[better] = src[better]
                tt, cc = np.nonzero(better)
                pk[k + 1, tt + s, cc] = k
                pt[k + 1, tt + s, cc] = tt
                pc[k + 1, tt + s, cc] = cc
        # прыжок k → j и затем две единицы j, j+1
        for j in cand[k]:
            cost = C[k, j]
            s2 = step[j] + step[j + 1]
            if s2 >= T:
                continue
            for c in range(max_jumps):
                src = row[:T - s2, c] + cost
                dst = f[j + 2, s2:, c + 1]
                better = src < dst
                if better.any():
                    dst[better] = src[better]
                    tt = np.nonzero(better)[0]
                    pk[j + 2, tt + s2, c + 1] = -(k + 2)      # отрицательное — признак прыжка
                    pt[j + 2, tt + s2, c + 1] = tt
                    pc[j + 2, tt + s2, c + 1] = c
    plans = []
    ts = np.arange(T) * q + head + tail
    ok_t = (ts >= lo_len) & (ts <= hi_len)
    for c in range(1, max_jumps + 1):
        tot = f[n, :, c] + STRETCH_WEIGHT * np.abs(ts / target - 1) + EXTRA_JUMP * (c - 1)
        tot[~ok_t] = INF
        t_best = int(np.argmin(tot))
        if not np.isfinite(tot[t_best]):
            continue
        # восстановление пути
        seams, costs = [], []
        k, t, cc = n, t_best, c
        while k > 0:
            prev = pk[k, t, cc]
            if prev == -1 and not (k == 0):
                break
            if prev < -1:
                src_k = -prev - 2
                jj = k - 2
                seams.append((int(src_k), int(jj)))
                costs.append(float(C[src_k, jj]))
                t, cc, k = int(pt[k, t, cc]), int(pc[k, t, cc]), src_k
            else:
                t, cc, k = int(pt[k, t, cc]), int(pc[k, t, cc]), int(prev)
        if k != 0:
            continue
        seams.reverse(); costs.reverse()
        segs, cur = [], ms
        for i, j in seams:
            segs.append((cur, b[i]))
            cur = b[j]
        segs.append((cur, me))
        length = sum(e - a for a, e in segs)
        if abs(length / target - 1) > MAX_STRETCH + 0.008:   # погрешность дискретизации времени
            continue
        plans.append(Plan(segments=segs, seams=seams, seam_costs=costs, stretch=length / target, kind="cut",
                          score=_score(costs, length, target)))
    return plans


def _plans_shorten(an: Analysis, C: np.ndarray, target: float, n_plans: int = 3) -> list[Plan]:
    """Несколько разных цепочек: после каждой найденной «штрафуем» её места склеек и ищем снова."""
    Cw = C.copy()
    out: list[Plan] = []
    radius = 4 if an.unit == "bar" else 10
    for _ in range(n_plans + 2):
        found = _dp_shorten(an, Cw, target)
        if not found:
            break
        found.sort(key=lambda p: p.score)
        best = found[0]
        # стоимость считаем по исходной матрице (без штрафов за разнообразие)
        best.seam_costs = [float(C[i, j]) for i, j in best.seams]
        best.score = _score(best.seam_costs, best.length, target)
        out.append(best)
        for i, j in best.seams:
            Cw[max(i - radius, 0):i + radius + 1, :] += 0.6
            Cw[:, max(j - radius, 0):j + radius + 1] += 0.6
        if len(out) >= n_plans:
            break
    return out


def _plans_extend(an: Analysis, C: np.ndarray, target: float) -> list[Plan]:
    b, ms, me = an.bounds, an.music_start, an.music_end
    L = me - ms
    lo, hi = _protected(an, target)
    if hi - lo < 4:
        lo, hi = 1, len(b) - 2
    amin, amax = target * (1 - MAX_STRETCH) - L, target * (1 + MAX_STRETCH) - L
    plans: list[Plan] = []
    idx = np.arange(lo, hi + 1)
    I, J = np.meshgrid(idx, idx, indexing="ij")
    loop = b[I] - b[J]
    ok = (J < I) & (I - J >= 4) & (loop >= 4.0) & np.isfinite(C[I, J])
    for i, j in zip(I[ok], J[ok]):
        i, j = int(i), int(j)
        seg = b[i] - b[j]
        # сколько раз повторить фрагмент
        for k in range(1, 9):
            added = k * seg
            if added > amax:
                break
            if added >= amin:
                segs = [(ms, b[i])] + [(b[j], b[i])] * (k - 1) + [(b[j], me)]
                length = L + added
                c = [float(C[i, j])] * k
                plans.append(Plan(segments=segs, seams=[(i, j)] * k, seam_costs=c, stretch=length / target,
                                  kind="extend", score=_score(c, length, target) - 0.05 * (k - 1)))
    return plans


def _plan_stretch(an: Analysis, target: float) -> list[Plan]:
    L = an.music_end - an.music_start
    if _stretch_ok(L, target):
        return [Plan(segments=[(an.music_start, an.music_end)], stretch=L / target, kind="stretch",
                     score=_score([], L, target))]
    return []


def plan_fade(an: Analysis, target: float) -> Plan:
    """Начало трека + затухание, конец — на границе такта."""
    b, ms = an.bounds, an.music_start
    fade = float(np.clip(0.08 * target, 2.5, 6.0))
    ideal = ms + target
    cands = b[(b > ms + 0.5 * target)]
    end = ideal
    if len(cands):
        k = int(np.argmin(np.abs(cands - ideal)))
        if _stretch_ok(cands[k] - ms, target):
            end = float(cands[k])
    end = min(end, an.music_end)
    length = end - ms
    return Plan(segments=[(ms, end)], stretch=length / target, kind="fade", fade_out=fade,
                score=0.9 + STRETCH_WEIGHT * abs(length / target - 1))


def _diverse(p: Plan, chosen: list[Plan], an: Analysis) -> bool:
    min_gap = 4 if an.unit == "bar" else 8
    for q in chosen:
        if p.kind != q.kind or len(p.seams) != len(q.seams):
            continue
        if not p.seams:
            return False
        gap = sum(abs(a[0] - c[0]) + abs(a[1] - c[1]) for a, c in zip(sorted(set(p.seams)), sorted(set(q.seams))))
        if gap < min_gap:
            return False
    return True


def make_plans(an: Analysis, target: float, n: int = 3, ending: str = "natural") -> list[Plan]:
    """Возвращает до n разных вариантов, лучший первым."""
    L = an.music_end - an.music_start
    C = jump_costs(an)
    cands = _plan_stretch(an, target)
    if L > target:
        cands += _plans_shorten(an, C, target)
    else:
        cands += _plans_extend(an, C, target)
    cands.sort(key=lambda p: p.score)
    chosen: list[Plan] = []
    want = n - 1 if ending == "fade" and L > target else n
    for p in cands:
        if len(chosen) >= want:
            break
        if _diverse(p, chosen, an):
            chosen.append(p)
    if L > target and (ending == "fade" or len(chosen) < n):
        fade = plan_fade(an, target)
        if ending == "fade":
            chosen.insert(0, fade)
        else:
            chosen.append(fade)
    if not chosen:  # удлинить не вышло ни одним способом — просто растягиваем в допустимых пределах
        chosen = [Plan(segments=[(an.music_start, an.music_end)], stretch=L / target, kind="stretch", score=9)]
    return chosen[:n]
