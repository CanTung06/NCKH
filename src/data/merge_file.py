import pandas as pd

# Đường dẫn 2 file
file1 = "scam_sms_dataset.csv"
file2 = "scam_sms_dataset(1).csv"

# Đọc 2 file
df1 = pd.read_csv(file1)
df2 = pd.read_csv(file2)

# Chỉ lấy text và label
df1 = df1[["text", "label"]]
df2 = df2[["text", "label"]]

# Gộp 2 dataset
df = pd.concat([df1, df2], ignore_index=True)

# Chuẩn hóa label
df["label"] = df["label"].astype(str).str.strip().str.lower()

# Chỉ giữ legitimate và scam
df = df[df["label"].isin(["legitimate", "scam"])].copy()

# Chuyển label thành số
# legitimate = 0
# scam = 1
df["label"] = df["label"].map({
    "legitimate": 0,
    "scam": 1
})

# Đánh lại ID từ 1
df.insert(0, "id", range(1, len(df) + 1))

# Xuất file
df.to_csv(
    "dataset.csv",
    index=False,
    encoding="utf-8-sig"
)

print("Đã gộp thành công!")
print("Tổng số dữ liệu:", len(df))
print("\nPhân bố label:")
print(df["label"].value_counts().sort_index())

print("\nCác cột:")
print(df.columns.tolist())