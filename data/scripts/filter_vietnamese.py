# -*- coding: utf-8 -*-
"""Loc du lieu scam/phishing theo ngon ngu: giu lai ban ghi TIENG VIET,
loai bo tieng Anh / ngon ngu khac (AI cho nguoi Viet).

Cach dung (chay tu thu muc D:\\nckh\\data):
  python -X utf8 scripts/filter_vietnamese.py --audit              # khao sat % ngon ngu tung nguon
  python -X utf8 scripts/filter_vietnamese.py --filter             # loc that su -> processed/<nguon>/
  python -X utf8 scripts/filter_vietnamese.py --filter --only sms_spam_uci
  python -X utf8 scripts/filter_vietnamese.py --filter --max-records 500

Quy tac phan loai:
  1) Ty le ky tu tieng Viet (co dau) >= 2% so chu cai             -> 'vi'
  2) Van ban ngan (<60 chu cai) co it nhat 1 ky tu tieng Viet     -> 'vi'
  3) Nguoc lai dung langdetect (seed=42, ket qua on dinh)         -> 'vi'/'en'/'es'/'other'
  4) Qua ngan / khong co chu cai (URL, so, gibberish)             -> 'unknown'
Nguon JSONL sidzzz07 co san truong 'language' -> dung truc tiep.
Nguon parquet (URL feature) khong phai van ban -> bo qua.
"""
import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path

from langdetect import DetectorFactory, detect_langs

DetectorFactory.seed = 42

# mot so ban ghi CSV rat dai (email, HTML) -> nang gioi han field cua module csv
try:
    csv.field_size_limit(1 << 27)  # ~134 MB
except (OverflowError, ValueError):
    pass

RAW = Path(r"D:\nckh\data\raw")
OUT = Path(r"D:\nckh\data\processed")

SAMPLE_PER_FILE = 2000              # so mau toi da moi file trong che do audit
AUDIT_MAX_CHARS = 64 * 1024 * 1024  # gioi han ky tu doc moi file khi audit
DETECT_SLICE = 600                  # chi detect tren 600 ky tu dau
MIN_LANG_PROB = 0.50

# cac ky tu dac trung cua ban chu cai tieng Viet (chu thuong)
VN_LOWER = set("ăâđêôơưáàảãạấầẩẫậắằẳẵặéèẻẽẹếềểễệíìỉĩịóòỏõọốồổỗộớờởỡợ"
               "úùủũụứừửữựýỳỷỹỵ")

CSV_TEXT_NAMES = ("text", "email text", "dialogue", "sms", "message", "body", "content")


def vi_ratio(text: str) -> float:
    """Ty le ky tu tieng Viet tren tong so chu cai."""
    letters = 0
    vn = 0
    for ch in text:
        if ch.isalpha():
            letters += 1
            if ch.lower() in VN_LOWER:
                vn += 1
    if letters == 0:
        return 0.0
    return vn / letters


def classify(text: str, pre_lang: str = None) -> str:
    """Tra ve 'vi' | 'en' | 'es' | 'other' | 'unknown'."""
    t = (text or "").strip()
    if pre_lang:
        p = pre_lang.strip().lower()
        if p in ("vi", "vietnamese"):
            return "vi"
        if p in ("en", "english"):
            return "en"
    if len(t) < 8:
        return "unknown"
    letters = sum(1 for ch in t if ch.isalpha())
    if letters < 10:
        return "unknown"
    r = vi_ratio(t)
    if r >= 0.02:
        return "vi"
    if r > 0 and letters <= 60:
        return "vi"
    try:
        langs = detect_langs(t[:DETECT_SLICE])
    except Exception:
        return "unknown"
    if langs and langs[0].prob >= MIN_LANG_PROB:
        best = langs[0].lang
        return best if best in ("vi", "en", "es") else "other"
    return "unknown"


# ---------------------------------------------------------------- doc du lieu

def discover_sources():
    """Tra ve [(ten_nguon, duong_dan, kieu)] tu thu muc raw."""
    out = []
    for sub in sorted(RAW.iterdir()):
        if not sub.is_dir():
            continue
        for p in sorted(sub.iterdir()):
            if p.name.startswith("_") or p.stat().st_size == 0:
                continue
            if p.suffix == ".parquet":
                kind = "url"
            elif p.suffix == ".jsonl":
                kind = "jsonl"
            elif p.suffix == ".json":
                kind = "json"
            elif p.name == "SMSSpamCollection":
                kind = "csv_tab"
            elif p.suffix in (".csv", ".partial", ".part"):
                kind = "csv"
            else:
                continue
            out.append((sub.name, p, kind))
    return out


def iter_csv(path: Path, delimiter: str, sample: int = None, max_chars: int = None):
    """Sinh (text, meta) tu file CSV/TSV. Tu do cot van ban, giu nguyen row goc."""
    with open(path, newline="", encoding="utf-8", errors="replace") as f:
        rd = csv.reader(f, delimiter=delimiter)
        probe = []
        for i, row in enumerate(rd):
            probe.append(row)
            if i >= 29:
                break
    if not probe or all(not r for r in probe):
        return
    first = probe[0]
    header_like = (
        all(len(c.strip()) < 40 for c in first)
        and any(c.strip().lower() in CSV_TEXT_NAMES for c in first)
    )
    if header_like:
        name_idx = {c.strip().lower(): i for i, c in enumerate(first)}
        text_idx = next((name_idx[nm] for nm in CSV_TEXT_NAMES if nm in name_idx), None)
        skip = 1
    else:
        rest = [r for r in probe if any(c.strip() for c in r)]
        ncols = max(len(r) for r in rest)
        lens = [0.0] * ncols
        cnt = [0] * ncols
        for r in rest:
            for i, c in enumerate(r):
                lens[i] += len(c)
                cnt[i] += 1
        text_idx = max(range(ncols), key=lambda i: lens[i] / (cnt[i] or 1))
        skip = 0

    chars = 0
    n = 0
    with open(path, newline="", encoding="utf-8", errors="replace") as f:
        rd = csv.reader(f, delimiter=delimiter)
        for i, row in enumerate(rd):
            if i < skip:
                continue
            if not row or len(row) <= text_idx:
                continue
            yield row[text_idx], {"_row": row,
                                  "_header": first if header_like else None,
                                  "_delim": delimiter}
            n += 1
            chars += len(row[text_idx]) + 8
            if sample and n >= sample:
                return
            if max_chars and chars >= max_chars:
                return


def _obj_text(obj):
    """Lay chuoi van ban dai nhat tu object (hoac chinh chuoi do)."""
    if isinstance(obj, str):
        return obj if obj.strip() else None
    if isinstance(obj, dict):
        best = None
        for v in obj.values():
            if isinstance(v, str) and v.strip():
                if best is None or len(v) > len(best):
                    best = v
        return best
    return None


def iter_json_array(path: Path, sample: int = None, max_chars: int = None):
    """Sinh (text, meta) tu mang JSON, doc tung phan tu khong nap ca file."""
    dec = json.JSONDecoder()
    ws = " \t\r\n,"
    n = 0
    read_chars = 0
    with open(path, encoding="utf-8", errors="replace") as f:
        buf = ""
        pos = 0
        eof = False
        while True:
            while pos < len(buf) and buf[pos] in ws:
                pos += 1
            if pos >= len(buf):
                if eof:
                    return
                chunk = f.read(8 << 20)
                if not chunk:
                    return
                read_chars += len(chunk)
                buf = buf[pos:]
                pos = 0
                buf += chunk
                if max_chars and read_chars >= max_chars:
                    eof = True
                continue
            c = buf[pos]
            if c == "]":
                return
            if c == "[":
                pos += 1  # nhay qua dau mang, chi decode tung phan tu
                continue
            try:
                obj, npos = dec.raw_decode(buf, pos)
            except json.JSONDecodeError:
                if eof:
                    pos += 1  # bo qua ky tu loi
                    continue
                chunk = f.read(8 << 20)
                if not chunk:
                    eof = True
                    continue
                read_chars += len(chunk)
                buf = buf[pos:]
                pos = 0
                buf += chunk
                if max_chars and read_chars >= max_chars:
                    eof = True
                continue
            pos = npos
            text = _obj_text(obj)
            if text is not None:
                yield text, {"_obj": obj}
                n += 1
                if sample and n >= sample:
                    return


def iter_jsonl(path: Path, sample: int = None, max_chars: int = None):
    n = 0
    chars = 0
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            text = _obj_text(obj) or ""
            pre_lang = obj.get("language") if isinstance(obj, dict) else None
            yield text, {"_obj": obj, "_lang": pre_lang}
            n += 1
            chars += len(line)
            if sample and n >= sample:
                return
            if max_chars and chars >= max_chars:
                return


def iter_records(path: Path, kind: str, sample: int = None, max_chars: int = None):
    if kind == "csv":
        yield from iter_csv(path, ",", sample, max_chars)
    elif kind == "csv_tab":
        yield from iter_csv(path, "\t", sample, max_chars)
    elif kind == "json":
        yield from iter_json_array(path, sample, max_chars)
    elif kind == "jsonl":
        yield from iter_jsonl(path, sample, max_chars)


# ------------------------------------------------------------------- audit

def run_audit(sample: int):
    sources = discover_sources()
    print(f"Khao sat ngon ngu trong {len(sources)} file tai {RAW}\n")
    report = {}
    for name, path, kind in sources:
        if kind == "url":
            print(f"[URL   ] {name}/{path.name}  -> dataset URL/feature, khong phan loai ngon ngu")
            report[f"{name}/{path.name}"] = {"kind": "url", "note": "bo qua"}
            continue
        cnt = Counter()
        for text, meta in iter_records(path, kind, sample=sample, max_chars=AUDIT_MAX_CHARS):
            cnt[classify(text, meta.get("_lang"))] += 1
        total = sum(cnt.values())
        key = f"{name}/{path.name}"
        if total == 0:
            print(f"[EMPTY ] {key}")
            report[key] = {"kind": kind, "sampled": 0}
            continue

        def pc(lang):
            return 100.0 * cnt.get(lang, 0) / total

        print(f"[{kind:<6}] {key}")
        print(f"         mau={total}  VI={pc('vi'):.1f}%  EN={pc('en'):.1f}%  ES={pc('es'):.1f}%  "
              f"khac={pc('other'):.1f}%  khong ro={pc('unknown'):.1f}%")
        report[key] = {"kind": kind, "sampled": total,
                       "vi": round(pc("vi"), 2), "en": round(pc("en"), 2),
                       "es": round(pc("es"), 2), "other": round(pc("other"), 2),
                       "unknown": round(pc("unknown"), 2)}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "_language_audit.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nDa luu bao cao: {OUT / '_language_audit.json'}")


# ------------------------------------------------------------------ filter

def run_filter(only: str = None, max_records: int = None):
    total_report = {}
    for name, path, kind in discover_sources():
        if only and only.lower() not in name.lower():
            continue
        if kind == "url":
            print(f"[SKIP ] {name}: dataset URL/feature, khong ap dung loc ngon ngu")
            continue
        dest_dir = OUT / name
        dest_dir.mkdir(parents=True, exist_ok=True)
        suffix = path.suffix if path.suffix else ".tsv"
        out_path = dest_dir / f"{path.stem}_vi{suffix}"
        delim = "\t" if kind == "csv_tab" else ","
        seen = kept = 0
        lang_cnt = Counter()
        header_written = False
        first_json = True
        with open(out_path, "w", encoding="utf-8", newline="") as out:
            wcsv = csv.writer(out, delimiter=delim) if kind in ("csv", "csv_tab") else None
            if kind == "json":
                out.write("[")
            for text, meta in iter_records(path, kind):
                seen += 1
                lang = classify(text, meta.get("_lang"))
                lang_cnt[lang] += 1
                if lang != "vi":
                    if seen % 50000 == 0:
                        print(f"    ... {name}/{path.name}: da xem {seen}, giu {kept}")
                    continue
                kept += 1
                if kind in ("csv", "csv_tab"):
                    if meta.get("_header") and not header_written:
                        wcsv.writerow(meta["_header"])
                        header_written = True
                    wcsv.writerow(meta["_row"])
                elif kind == "jsonl":
                    out.write(json.dumps(meta["_obj"], ensure_ascii=False) + "\n")
                elif kind == "json":
                    out.write(("\n" if first_json else ",\n")
                              + json.dumps(meta["_obj"], ensure_ascii=False, indent=2))
                    first_json = False
                if max_records and kept >= max_records:
                    break
            if kind == "json":
                out.write("\n]")
        print(f"[{kind:<6}] {name}/{path.name} -> {out_path.name}  (xem {seen}, giu {kept})")
        total_report[f"{name}/{path.name}"] = {
            "seen": seen, "kept_vi": kept,
            "dropped": {k: v for k, v in lang_cnt.items() if k != "vi"},
            "output": str(out_path) if kept else None,
        }
        if kept == 0:
            out_path.unlink(missing_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "_filter_report.json").write_text(
        json.dumps(total_report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nDa luu bao cao: {OUT / '_filter_report.json'}")


def main():
    ap = argparse.ArgumentParser(description="Loc du lieu giu tieng Viet")
    ap.add_argument("--audit", action="store_true", help="khao sat %% ngon ngu tung nguon")
    ap.add_argument("--filter", action="store_true", help="loc giu ban ghi tieng Viet")
    ap.add_argument("--only", default=None, help="chi xu ly nguon co ten chua chuoi nay")
    ap.add_argument("--sample", type=int, default=SAMPLE_PER_FILE, help="so mau moi file khi audit")
    ap.add_argument("--max-records", type=int, default=None, help="gioi han so ban ghi giu moi file")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    if args.audit:
        run_audit(args.sample)
    elif args.filter:
        run_filter(args.only, args.max_records)
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
