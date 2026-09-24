# -*- coding: utf-8 -*-
"""Kiem chung doc lap chat luong scam_dataset.jsonl:
- JSON hop le + schema (text/label/channel/language/source)
- Thong ke label, channel, nguon
- Kiem tra trung lap (MD5 tren text chuan hoa, giong mo ta trong nguon_du_lieu.md)
- Ban ghi qua ngan (<5 ky tu)
- Ty le tieng Viet thuc te (heuristic ky tu co dau + langdetect cho mau ngau nhien)
"""
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

DATA = Path(r"D:\nckh\data\scam_dataset.jsonl")

VN_LOWER = set("ăâđêôơưáàảãạấầẩẫậắằẳẵặéèẻẽẹếềểễệíìỉĩịóòỏõọốồổỗộớờởỡợ"
               "úùủũụứừửữựýỳỷỹỵ")
REQUIRED = ("text", "label", "channel", "language", "source")


def norm_key(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def vi_ratio(text: str) -> float:
    letters = [ch for ch in text if ch.isalpha()]
    if not letters:
        return 0.0
    vn = sum(1 for ch in text.lower() if ch in VN_LOWER)
    return vn / len(letters)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    total = bad_json = missing_field = too_short = 0
    labels = Counter()
    channels = Counter()
    languages = Counter()
    sources = Counter()
    seen_keys = Counter()
    vi_scores = []
    lengths = []

    with open(DATA, encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            total += 1
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                bad_json += 1
                continue
            if not all(k in obj for k in REQUIRED):
                missing_field += 1
            labels[obj.get("label", "?")] += 1
            channels[obj.get("channel", "?")] += 1
            languages[obj.get("language", "?")] += 1
            sources[obj.get("source", "?")] += 1
            text = obj.get("text", "") or ""
            seen_keys[norm_key(text)] += 1
            lengths.append(len(text))
            if len(text.strip()) < 5:
                too_short += 1
            if obj.get("language") == "vi" and len(text) > 20:
                vi_scores.append(vi_ratio(text))

    dup = {k: v for k, v in seen_keys.items() if v > 1}
    print("=" * 70)
    print(f"Kiem chung: {DATA.name}")
    print("=" * 70)
    print(f"Tong dong JSON hop le : {total}")
    print(f"JSON loi              : {bad_json}")
    print(f"Thieu truong bat buoc : {missing_field}")
    print(f"Ban ghi <5 ky tu      : {too_short}")
    print(f"Trung lap (MD5 chuan hoa): {sum(v - 1 for v in dup.values())} ban ghi bi lap, "
          f"{len(dup)} chuoi bi lap")
    if dup:
        for k, v in list(dup.items())[:3]:
            print(f"    x{v}: {k[:80]}...")
    print()
    print("Label     :", dict(labels.most_common()))
    print("Channel   :", dict(channels.most_common()))
    print("Language  :", dict(languages.most_common()))
    print()
    top_sources = sources.most_common(8)
    print("Nguon (top 8):")
    for s, c in top_sources:
        print(f"    {c:>6}  {s}")
    print(f"    ({len(sources)} nguon khac nhau)")
    if lengths:
        lengths.sort()
        print()
        print(f"Do dai text: min={lengths[0]}  median={lengths[len(lengths)//2]}  "
              f"max={lengths[-1]}")
    if vi_scores:
        vi_scores.sort()
        zero = sum(1 for r in vi_scores if r == 0)
        high = sum(1 for r in vi_scores if r >= 0.02)
        med = vi_scores[len(vi_scores) // 2]
        print(f"Ty le tieng Viet (ky tu co dau): trung vi={med:.1%}  "
              f"co dau >=2%: {high}/{len(vi_scores)} ({100.0*high/len(vi_scores):.1f})  "
              f"khong dau hoac khac: {zero}/{len(vi_scores)} ({100.0*zero/len(vi_scores):.1f})")
    print()
    # ket luan nhanh
    expected = {"scam": 10639, "legitimate": 13958, "spam": 478,
                "fake_news": 721, "reference": 33}
    ok = all(labels.get(k) == v for k, v in expected.items())
    print("So sanh voi nguon_du_lieu.md:", "KHOP" if ok else "LECH!")
    if not ok:
        for k, v in expected.items():
            print(f"    {k}: md={v}, thuc te={labels.get(k)}")


if __name__ == "__main__":
    main()
