import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report
)

# 1. Đọc dữ liệu
train_df = pd.read_csv("../../data/split/train.csv")
val_df = pd.read_csv("../../data/split/validation.csv")
test_df = pd.read_csv("../../data/split/test.csv")

# 2. TF-IDF
vectorizer = TfidfVectorizer()

X_train = vectorizer.fit_transform(train_df["text"])
X_val = vectorizer.transform(val_df["text"])
X_test = vectorizer.transform(test_df["text"])

# 3. Label
y_train = train_df["label"]
y_val = val_df["label"]
y_test = test_df["label"]

# 4. Tạo Logistic Regression
model = LogisticRegression(
    max_iter=1000
)

# 5. Huấn luyện
model.fit(X_train, y_train)

# 6. Dự đoán Validation
y_val_pred = model.predict(X_val)

# 7. Kiểm tra
print("===== KẾT QUẢ =====")
print("Số lượng dự đoán:", len(y_val_pred))
print("\n10 dự đoán đầu tiên:")
print(y_val_pred[:10])

print("\n10 đáp án thật:")
print(y_val.values[:10])

# 8. Đánh giá Validation
accuracy = accuracy_score(y_val, y_val_pred)
precision = precision_score(y_val, y_val_pred)
recall = recall_score(y_val, y_val_pred)
f1 = f1_score(y_val, y_val_pred)

print("\n===== ĐÁNH GIÁ VALIDATION =====")

print("Accuracy :", accuracy)
print("Precision:", precision)
print("Recall   :", recall)
print("F1-score :", f1)

print("\n===== CLASSIFICATION REPORT =====")
print(
    classification_report(
        y_val,
        y_val_pred,
        target_names=["Normal", "Scam"]
    )
)