import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

# 1. Đọc dữ liệu
train_df = pd.read_csv("../../data/split/train.csv")
val_df = pd.read_csv("../../data/split/validation.csv")
test_df = pd.read_csv("../../data/split/test.csv")

# 2. Tạo TF-IDF
vectorizer = TfidfVectorizer()

X_train = vectorizer.fit_transform(train_df["text"])

X_val = vectorizer.transform(val_df["text"])

X_test = vectorizer.transform(test_df["text"])

# 3. Lấy label
y_train = train_df["label"]

y_val = val_df["label"]

y_test = test_df["label"]

# 4. Kiểm tra
print("===== KẾT QUẢ TF-IDF =====")

print("X_train:", X_train.shape)
print("X_val:", X_val.shape)
print("X_test:", X_test.shape)

print("\ny_train:", y_train.shape)
print("y_val:", y_val.shape)
print("y_test:", y_test.shape)

print("\nSố lượng từ/vocabulary:", len(vectorizer.vocabulary_))