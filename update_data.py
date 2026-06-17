import csv
import json
import re
import sys
from pathlib import Path

CSV_PATH = "data.csv"   # percorso del CSV nella repo
HTML_PATH = "index.html"  # percorso dell'HTML nella repo

def parse_val(v):
    if not v or v.strip() in ("", "-", "- €", "#DIV/0!"):
        return 0
    v = v.replace("€", "").replace(" ", "").replace(".", "").replace(",", ".")
    try:
        return float(v)
    except:
        return 0

def load_csv(path):
    rows = []
    with open(path, encoding="utf-8-sig") as f:
        # Rileva separatore
        sample = f.read(1024)
        f.seek(0)
        sep = ";" if ";" in sample else ","
        reader = csv.DictReader(f, delimiter=sep)
        for row in reader:
            # Normalizza chiavi (lowercase, strip)
            row = {k.strip().lower(): v.strip() for k, v in row.items()}
            nome = row.get("nome campagna") or row.get("nome") or row.get("campagna", "")
            if not nome:
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

def build_init(rows):
    lines = ["const INIT = ["]
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

def update_html(html_path, new_init):
    html = Path(html_path).read_text(encoding="utf-8")
    # Sostituisce tutto il blocco INIT
    pattern = r"const INIT = \[[\s\S]*?\];"
    if not re.search(pattern, html):
        print("❌ Blocco INIT non trovato nell'HTML")
        sys.exit(1)
    updated = re.sub(pattern, new_init, html)
    Path(html_path).write_text(updated, encoding="utf-8")
    print(f"✓ index.html aggiornato con {len(rows)} campagne")

if __name__ == "__main__":
    rows = load_csv(CSV_PATH)
    if not rows:
        print("❌ Nessuna riga trovata nel CSV")
        sys.exit(1)
    new_init = build_init(rows)
    update_html(HTML_PATH, new_init)