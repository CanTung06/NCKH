from pathlib import Path
import re
import unicodedata

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "eda"
EXPECTED_LABELS = {0, 1}  # 0 = legitimate, 1 = scam (per 01_merge_file.py)


def section(title: str) -> None:
    print(f"\n{'=' * 12} {title} {'=' * 12}")


def normalize_text(value: object) -> str:
    """Normalize text for duplicate checks without changing source data."""
    if pd.isna(value):
        return ""
    value = unicodedata.normalize("NFC", str(value)).lower()
    return re.sub(r"\s+", " ", value).strip()


def find_column(columns, candidates):
    lookup = {str(column).strip().lower(): column for column in columns}
    for candidate in candidates:
        if candidate in lookup:
            return lookup[candidate]
    return None


def inspect_files() -> list[Path]:
    section("1. Dataset trong data/processed")
    if not DATA_DIR.exists():
        print(f"Không tìm thấy thư mục: {DATA_DIR}")
        return []

    files = sorted(path for path in DATA_DIR.iterdir() if path.is_file())
    if not files:
        print(f"Thư mục rỗng: {DATA_DIR}")
        return []

    for path in files:
        print(f"- {path.name}: {path.stat().st_size:,} bytes")
    csv_files = [path for path in files if path.suffix.lower() == ".csv"]
    if len(csv_files) != len(files):
        print("Lưu ý: thư mục có file không phải CSV; script chỉ đọc CSV.")
    return csv_files


def load_csv(path: Path) -> pd.DataFrame:
    # utf-8-sig handles both UTF-8 and files exported with a BOM.
    try:
        return pd.read_csv(path, encoding="utf-8-sig", low_memory=False)
    except UnicodeDecodeError:
        print("Không đọc được UTF-8; thử encoding cp1258.")
        return pd.read_csv(path, encoding="cp1258", low_memory=False)


def inspect_dataset(path: Path, df: pd.DataFrame) -> None:
    section(f"2. Tổng quan: {path.name}")
    print(f"Kích thước: {df.shape[0]:,} dòng × {df.shape[1]} cột")
    print("Cột:", ", ".join(map(str, df.columns)))
    print("\nKiểu dữ liệu: \n", df.dtypes.to_string())
    print("\nGiá trị thiếu theo cột:\n", df.isna().sum().to_string())
    print(f"\nSố dòng trùng toàn bộ: {df.duplicated().sum():,}")

    text_col = find_column(df.columns, ("text", "message", "content", "sms"))
    label_col = find_column(df.columns, ("label", "target", "class", "is_scam"))

    if text_col is not None:
        text = df[text_col].fillna("").astype(str)
        char_lengths = text.str.len()
        word_lengths = text.str.split().str.len()
        print(f"\nCột nội dung: {text_col}")
        print(f"Nội dung rỗng: {(text.str.strip() == '').sum():,}")
        print(f"Trùng nội dung chuẩn hóa: {text.map(normalize_text).duplicated().sum():,}")
        print("Độ dài ký tự (mô tả):\n", char_lengths.describe(
            percentiles=[0.25, 0.5, 0.75, 0.95]
        ).round(2).to_string())
        print("Độ dài từ (mô tả):\n", word_lengths.describe(
            percentiles=[0.25, 0.5, 0.75, 0.95]
        ).round(2).to_string())
        print("\nMột số mẫu nội dung:")
        for i, value in enumerate(text[text.str.strip().ne("")].head(5), start=1):
            print(f"{i}. {value[:300]!r}")
    else:
        print("\nKhông nhận diện được cột nội dung (text/message/content/sms).")

    if label_col is not None:
        inspect_labels(df, label_col, text_col)
    else:
        print("\nKhông nhận diện được cột nhãn (label/target/class/is_scam).")

    make_charts(df, path.stem, text_col, label_col)


def inspect_labels(df: pd.DataFrame, label_col, text_col) -> None:
    section("3. Chất lượng nhãn")
    labels = df[label_col]
    missing = labels.isna() | labels.astype("string").str.strip().eq("")
    present = labels[~missing]
    counts = present.value_counts(dropna=False)
    print(f"Cột nhãn: {label_col}")
    print(f"Nhãn thiếu/rỗng: {missing.sum():,} ({missing.mean():.2%})")
    print("Phân bố nhãn:\n", counts.to_string())
    if len(present):
        print("Tỷ lệ nhãn (%):\n", (counts / len(present) * 100).round(2).to_string())

    normalized = present.astype(str).str.strip().str.lower()
    observed = set(normalized.unique())
    if observed.issubset({"0", "1"}):
        print("\nNhãn dạng nhị phân. Quy ước dự án: 0 = legitimate, 1 = scam.")
        unexpected = observed - {str(value) for value in EXPECTED_LABELS}
    else:
        print("\nNhãn dạng phân loại; cần đối chiếu từ điển nhãn với quy ước dự án.")
        unexpected = set()
    if unexpected:
        print("CẢNH BÁO: giá trị nhãn ngoài quy ước:", sorted(unexpected))

    if text_col is None:
        return
    text = df[text_col].fillna("").map(normalize_text)
    labeled = pd.DataFrame({"text_key": text, "label_key": normalized.reindex(present.index)})
    labeled = labeled[labeled["text_key"].ne("")]
    conflicts = labeled.groupby("text_key")["label_key"].nunique()
    conflict_keys = conflicts[conflicts > 1].index
    print(f"\nNội dung trùng nhưng mang nhãn khác nhau: {len(conflict_keys):,} nhóm")
    if len(conflict_keys):
        conflict_rows = labeled[labeled["text_key"].isin(conflict_keys)].head(10)
        print("Ví dụ cần rà soát thủ công (tối đa 10 dòng):")
        for row in conflict_rows.itertuples(index=False):
            print(f"- label={row.label_key!r}: {row.text_key[:180]!r}")


def make_charts(df: pd.DataFrame, stem: str, text_col, label_col) -> None:
    """Save useful plots when matplotlib is installed; keep console EDA usable without it."""
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("\nBỏ qua biểu đồ: chưa cài matplotlib.")
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    created = []
    if label_col is not None:
        counts = df[label_col].fillna("<missing>").astype(str).value_counts()
        ax = counts.plot(kind="bar", figsize=(8, 4), color="#4472C4")
        ax.set(title="Phân bố nhãn", xlabel="Nhãn", ylabel="Số dòng")
        plt.xticks(rotation=30, ha="right")
        plt.tight_layout()
        out = OUTPUT_DIR / f"{stem}_label_distribution.png"
        plt.savefig(out, dpi=150)
        plt.close()
        created.append(out.name)

    if text_col is not None:
        lengths = df[text_col].fillna("").astype(str).str.len()
        plt.figure(figsize=(8, 4))
        plt.hist(lengths.clip(upper=lengths.quantile(0.99)), bins=40, color="#70AD47")
        plt.title("Phân bố độ dài nội dung (cắt tại percentile 99)")
        plt.xlabel("Số ký tự")
        plt.ylabel("Số dòng")
        plt.tight_layout()
        out = OUTPUT_DIR / f"{stem}_text_length.png"
        plt.savefig(out, dpi=150)
        plt.close()
        created.append(out.name)
    if created:
        print(f"\nĐã cấu hình lưu biểu đồ tại {OUTPUT_DIR}: {', '.join(created)}")


def main() -> None:
    csv_files = inspect_files()
    if not csv_files:
        return
    for path in csv_files:
        try:
            df = load_csv(path)
        except Exception as exc:
            print(f"\nKhông thể đọc {path.name}: {exc}")
            continue
        inspect_dataset(path, df)


if __name__ == "__main__":
    main()
