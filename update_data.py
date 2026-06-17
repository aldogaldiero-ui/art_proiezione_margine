import csv
import json
import re
import sys
from pathlib import Path
from datetime import datetime

CSV_PATH = "data.csv"
HTML_PATH = "index.html"

def parse_val(v):
    if not v or v.strip() in ("", "-", "- €", "#DIV/0!"):
        return 0
    v = v.strip()
    v = v.replace("€", "").replace(" ", "")
    if "," in v and "." in v:
        # Formato italiano "1.234,56" → rimuovi punto migliaia, converti virgola
        v = v.replace(".", "").replace(",", ".")
    elif "," in v:
        # Formato "664,00" → converti virgola in punto
        v = v.replace(",", ".")
    # Formato inglese "11.5" → lascia invariato
    try:
        return float(v)
    except:
        return 0

def load_csv(path):
    rows = []
    with open(path, encoding="utf-8-sig") as f:
        sample = f.read(1024)
        f.seek(0)
        sep = ";" if ";" in sample else ","
        reader = csv.DictReader(f, delimiter=sep)
        for row in reader:
            row = {k.strip().lower(): (v.strip() if v is not None else "") for k, v in row.items()}
           nome = row.get("nome campagna") or row.get("nome") or row.get("campagna", "")
                if not nome or nome.startswith("__"):
            continue
            rows.append({
                "nome":       nome,
                "cap":        parse_val(row.get("cap", "")),
                "payout":     parse_val(row.get("payout", "")),
                "volErogato": parse_val(row.get("vol. erogato") or row.get("vol erogato") or row.get("volerogato", "")),
                "speso":      parse_val(row.get("speso", "")),
                "cplOggi":    parse_val(row.get("cpl oggi") or row.get("cploggi") or row.get("cpl_oggi", "")),
                "mdOverride": parse_val(row.get("margine day") or row.get("margineday") or row.get("margine_day", "")) or None,
            })
    return rows

def load_meta(rows_raw):
    """Estrae metadati dalle righe speciali che iniziano con __"""
    meta = {}
    for row in rows_raw:
        nome = list(row.values())[0].strip()
        if nome.startswith("__") and nome.endswith("__"):
            key = nome.strip("_")
            val = list(row.values())[1] if len(row) > 1 else ""
            meta[key] = val.strip()
    return meta

def build_init(rows, giorni=10):
    version = datetime.now().strftime("%Y%m%d%H%M")
    lines = [
        f'const DATA_VERSION = "{version}";',
        f'const GIORNI_DEFAULT = {giorni};',
        "const INIT = ["
    ]
    for i, r in enumerate(rows):
        md = "null" if r["mdOverride"] is None or r["mdOverride"] == 0 else str(r["mdOverride"])
        lines.append(
            f'  {{ id:{i+1}, nome:{json.dumps(r["nome"], ensure_ascii=False)}, '
            f'cap:{r["cap"]}, payout:{r["payout"]}, '
            f'volErogato:{r["volErogato"]}, speso:{r["speso"]}, '
            f'cplOggi:{r["cplOggi"]}, mdOverride:{md} }},'
        )
    lines.append("];")
    return "\n".join(lines)

def update_html(html_path, new_init, rows):
    html = Path(html_path).read_text(encoding="utf-8")
    # Sostituisce INIT con eventuale DATA_VERSION precedente
    pattern = r'(?:const DATA_VERSION = "[^"]*";\n)?(?:const GIORNI_DEFAULT = \d+;\n)?const INIT = \[[\s\S]*?\];'
    if not re.search(pattern, html):
        print("❌ Blocco INIT non trovato nell'HTML")
        sys.exit(1)
    updated = re.sub(pattern, new_init, html)
    Path(html_path).write_text(updated, encoding="utf-8")
    print(f"✓ index.html aggiornato con {len(rows)} campagne")

if __name__ == "__main__":
    rows_raw = []
    with open(CSV_PATH, encoding="utf-8-sig") as f:
        sample = f.read(1024)
        f.seek(0)
        sep = ";" if ";" in sample else ","
        reader = csv.DictReader(f, delimiter=sep)
        for row in reader:
            rows_raw.append(dict(row))

    meta = load_meta(rows_raw)
    giorni = int(meta.get("giorni", 10))

    rows = load_csv(CSV_PATH)
    if not rows:
        print("❌ Nessuna riga trovata nel CSV")
        sys.exit(1)
    new_init = build_init(rows, giorni)
    update_html(HTML_PATH, new_init, rows)

