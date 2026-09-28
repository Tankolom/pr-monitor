"""Слепой тест для тренеров/музыкантов: папка с перемешанными вариантами + страница оценки.

python -m eval.blind <папка результатов run_eval> <куда сложить тест>

Откройте <куда>/index.html в браузере (или отправьте папку архивом). Оценщик слушает каждый
вариант, жмёт «к склейке», ставит оценку; в конце — «Скопировать результаты» (CSV).
Ключ соответствия хранится в <куда>/key.json — оценщику его не отправляйте.
"""
from __future__ import annotations


import json
import os
import random
import sys

import soundfile as sf

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.audio import io  # noqa: E402


def main(src: str, dst: str) -> None:
    os.makedirs(os.path.join(dst, "audio"), exist_ok=True)
    items = []
    for name in sorted(os.listdir(src)):
        mp = os.path.join(src, name, "meta.json")
        if not os.path.exists(mp):
            continue
        meta = json.load(open(mp))
        for v in meta["variants"]:
            items.append((name, v))
    random.Random(42).shuffle(items)
    key, cards = {}, []
    for n, (name, v) in enumerate(items, 1):
        code = f"T{n:03d}"
        y, sr = sf.read(os.path.join(src, name, f"v{v['index']}.flac"), dtype="float32", always_2d=True)
        io.encode(y, os.path.join(dst, "audio", f"{code}.mp3"), bitrate="192k")
        key[code] = {"track": name, "variant": v["index"], "kind": v["kind"], "quality": v["quality"],
                     "costs": [s["cost"] for s in v["seams"]]}
        seams = [s["t"] for s in v["seams"]]
        btns = "".join(f'<button onclick="jump(\'{code}\',{max(s - 3, 0):.1f})">к склейке {k + 1}</button>'
                       for k, s in enumerate(seams)) or "<i>без склеек</i>"
        cards.append(f"""<div class=c id={code}><b>{code}</b> <audio id=a{code} controls preload=none src="audio/{code}.mp3"></audio>
<div>{btns}</div><div class=r>
<label><input type=radio name={code} value=ready> готово к выступлению</label>
<label><input type=radio name={code} value=needs_fix> нужны правки</label>
<label><input type=radio name={code} value=bad> брак</label>
<input class=cm placeholder="комментарий" data-c={code}></div></div>""")
    json.dump(key, open(os.path.join(dst, "key.json"), "w"), ensure_ascii=False, indent=1)
    page = f"""<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>Слепой тест склеек</title><style>body{{font:16px system-ui;margin:16px;max-width:760px}}
.c{{border:1px solid #ddd;border-radius:12px;padding:12px;margin:10px 0}}audio{{width:100%;margin:6px 0}}
button{{margin:2px 6px 2px 0}}.r label{{display:block}}.cm{{width:100%;margin-top:6px;padding:6px}}</style>
<h1>Слепой тест: {len(items)} фрагментов</h1>
<p>Послушайте каждый фрагмент целиком и отдельно место склейки. Оцените: можно ли отдать эту музыку на выступление
без правок? Порядок и источники перемешаны.</p>
{''.join(cards)}
<p><button onclick="exportCsv()">Скопировать результаты</button></p><textarea id=out rows=8 style="width:100%"></textarea>
<script>
function jump(c,t){{const a=document.getElementById('a'+c);a.currentTime=t;a.play();}}
const S='blind-'+location.pathname;
function save(){{const d={{}};document.querySelectorAll('.c').forEach(c=>{{const r=c.querySelector('input[type=radio]:checked');
d[c.id]={{r:r?r.value:'',m:c.querySelector('.cm').value}};}});try{{localStorage.setItem(S,JSON.stringify(d))}}catch(e){{}}}}
function load(){{let d={{}};try{{d=JSON.parse(localStorage.getItem(S)||'{{}}')}}catch(e){{}}for(const[k,v]of Object.entries(d)){{
const c=document.getElementById(k);if(!c)continue;if(v.r){{const i=c.querySelector('input[value='+v.r+']');if(i)i.checked=true;}}
c.querySelector('.cm').value=v.m||'';}}}}
document.addEventListener('change',save);document.addEventListener('input',save);load();
function exportCsv(){{const rows=['code,rating,comment'];document.querySelectorAll('.c').forEach(c=>{{
const r=c.querySelector('input[type=radio]:checked');rows.push([c.id,r?r.value:'','"'+c.querySelector('.cm').value.replace(/"/g,'""')+'"'].join(','));}});
const t=document.getElementById('out');t.value=rows.join('\\n');t.select();try{{navigator.clipboard.writeText(t.value)}}catch(e){{}}}}
</script>"""
    open(os.path.join(dst, "index.html"), "w").write(page)
    print(f"{len(items)} фрагментов → {dst}/index.html (ключ: key.json)")


def score(key_path: str, csv_path: str) -> None:
    """Сводка: доля «готово» по оценке алгоритма (great/ok/check/fade)."""
    import csv

    key = json.load(open(key_path))
    by: dict[str, list[str]] = {}
    for row in csv.DictReader(open(csv_path)):
        if row["rating"]:
            by.setdefault(key[row["code"]]["quality"], []).append(row["rating"])
    for q, rs in sorted(by.items()):
        ready = sum(r == "ready" for r in rs)
        print(f"{q:>6}: {ready}/{len(rs)} готово ({ready / len(rs):.0%}), правки {rs.count('needs_fix')}, брак {rs.count('bad')}")



if __name__ == "__main__":
    if sys.argv[1] == "score":
        score(sys.argv[2], sys.argv[3])
    else:
        main(sys.argv[1], sys.argv[2])
