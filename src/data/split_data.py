import pandas as pd
from sklearn.model_selection import train_test_split
from pathlib import Path


# =========================
# 1. Đường dẫn
# =========================

input_file = Path("../../data/raw/dataset.csv")
output_dir = Path("../../data/split")

# Tạo thư mục split nếu chưa có
output_dir.mkdir(parents=True, exist_ok=True)


# =========================
# 2. Đọc dataset
# =========================

df = pd.read_csv(input_file)

print("Tổng số dữ liệu:", len(df))


# =========================
# 3. Chia Train và Temp
# =========================

train_df, temp_df = train_test_split(
    df,
    test_size=0.30,
    random_state=42,
    stratify=df["label"]
)


# =========================
# 4. Chia Validation và Test
# =========================

val_df, test_df = train_test_split(
    temp_df,
    test_size=0.50,
    random_state=42,
    stratify=temp_df["label"]
)


# =========================
# 5. Lưu dữ liệu
# =========================

train_df.to_csv(
    output_dir / "train.csv",
    index=False,
    encoding="utf-8-sig"
)

val_df.to_csv(
    output_dir / "validation.csv",
    index=False,
    encoding="utf-8-sig"
)

test_df.to_csv(
    output_dir / "test.csv",
    index=False,
    encoding="utf-8-sig"
)


# =========================
# 6. Kiểm tra kết quả
# =========================

print("\n===== KẾT QUẢ =====")

print("Train:", len(train_df))
print("Validation:", len(val_df))
print("Test:", len(test_df))

print("Tổng:", len(train_df) + len(val_df) + len(test_df))


print("\n===== LABEL TRAIN =====")
print(train_df["label"].value_counts())


print("\n===== LABEL VALIDATION =====")
print(val_df["label"].value_counts())


print("\n===== LABEL TEST =====")
print(test_df["label"].value_counts())


print("\nĐã lưu dữ liệu vào:")
print(output_dir)