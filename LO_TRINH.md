# LỘ TRÌNH XÂY DỰNG SẢN PHẨM "AI CẢNH BÁO LỪA ĐẢO" (TIẾNG VIỆT)

> Tài liệu định hướng cho đề tài NCKH — phát hiện & cảnh báo tin nhắn lừa đảo tiếng Việt.
> Số liệu trong tài liệu được **kiểm chứng trực tiếp trên dữ liệu thực tế trong repo** ngày 25/09/2026.

---

## 0. TÓM TẮT NHANH (TL;DR)

- **Sản phẩm mục tiêu**: ứng dụng web dán tin nhắn (SMS/Zalo/FB) → hệ thống trả lời: **có phải lừa đảo không? → loại lừa đảo nào? → mức rủi ro? → dấu hiệu nào cho thấy vậy?** kèm khuyến nghị hành động.
- **Dữ liệu sẵn có**: ~25.800 tin đã gán nhãn (scam/legitimate/fake_news/spam) + ~22.700 tin có nhãn loại lừa đảo & mức rủi ro. Chất lượng tốt, đã khử trùng lặp, 100% tiếng Việt.
- **Lộ trình kỹ thuật**: TF-IDF + LogisticRegression (baseline, tuần 1) → fine-tune **PhoBERT** trên GPU RTX 4060 8GB (tuần 2–4) → đa nhiệm vụ (loại lừa đảo + mức rủi ro) → **FastAPI + Streamlit** ra sản phẩm (tuần 5–6) → kiểm thử độc lập + báo cáo NCKH (tuần 7–8).
- **Mục tiêu chất lượng**: Recall lớp scam ≥ 0,97, F1 ≥ 0,95 trên tập test (tham khảo, vì nhiều tin cùng khuôn mẫu).
- **Việc đầu tiên làm ngay**: chạy GĐ0 (cài thư viện còn thiếu) và GĐ1 (hợp nhất 3 file dữ liệu → 1 file chuẩn + chia train/val/test).

---

## 1. SẢN PHẨM CUỐI CÙNG LÀ GÌ?

### 1.1 Tầm nhìn & người dùng

**Tên gợi ý**: ScamGuard VN — "Trợ lý cảnh báo lừa đảo tiếng Việt".

| Người dùng | Nhu cầu |
|---|---|
| Người dùng phổ thông (ông bà, phụ huynh) | Dán tin nhắn lạ vào → biết ngay có lừa đảo hay không, hiểu vì sao |
| Người trẻ | Kiểm tra tin nhắn mượn tiền, trúng thưởng, việc làm, đầu tư |
| Người làm báo cáo NCKH | Có kết quả thực nghiệm, mô hình, số liệu để viết báo cáo |

**Phạm vi (scope) — nói rõ để không bị "phình" đề tài**:
- ✅ ĐẦU VÀO: text tiếng Việt (SMS, tin nhắn Zalo/FB, bài đăng ngắn) do người dùng **dán vào**.
- ✅ ĐẦU RA: nhị phân lừa đảo + loại lừa đảo + mức rủi ro + giải thích + khuyến nghị.
- ❌ KHÔNG làm (để làm sau nếu còn thời gian): đọc SMS tự động trên Android, nhận diện giọng nói cuộc gọi giả danh, kiểm tra URL/phishing web, mở rộng đa ngôn ngữ.

> Kinh nghiệm quan trọng nhất của mọi đề tài NCKH: **làm hẹp nhưng sâu và chạy được thật** tốt hơn làm rộng nhưng dở.

### 1.2 Kiến trúc tổng thể của sản phẩm

```
Người dùng dán tin nhắn
        │
        ▼
┌──────────────────────┐
│ Web demo (Streamlit) │  ← giao diện đơn giản, demo dễ
└─────────┬────────────┘
          │ HTTP
          ▼
┌──────────────────────┐
│ API (FastAPI)        │  ← POST /predict {"text": "..."}
└─────────┬────────────┘
          ▼
┌───────────────────────────────────────────────┐
│ Pipeline suy luận (src/infer.py)               │
│ 1) Tiền xử lý: NFC, bỏ ký tự ẩn, tách từ       │
│ 2) Mô hình PhoBERT đã fine-tune                │
│    ├─ Head 1: scam / không scam (+ độ tin)     │
│    ├─ Head 2: loại lừa đảo (category)          │
│    └─ Head 3: mức rủi ro (risk level)          │
│ 3) Explainer (rule-based): tô sáng URL lạ, SĐT,│
│    từ khóa gây áp lực, mạo danh thương hiệu     │
└─────────┬─────────────────────────────────────┘
          ▼
┌───────────────────────────────────────────────┐
│ KẾT QUẢ HIỂN THỊ:                              │
│ ⚠ CẢNH BÁO LỪA ĐẢO — loại: lừa vay nặng lãi    │
│ Mức rủi ro: CAO (điểm 0.87)                    │
│ Dấu hiệu: URL lạ "vaynhanh90.info", yêu cầu    │
│ đăng ký gấp, hứa lãi suất thấp bất thường      │
│ Khuyến nghị: KHÔNG bấm link, KHÔNG chuyển      │
│ tiền, chặn số, báo tổng đài 156 (CS QHCS ANM)  │
└───────────────────────────────────────────────┘
```

**Vì sao thiết kế 3 đầu ra thay vì chỉ 1 nhãn?** Một câu trả lời "đây là lừa đảo" chưa đủ thuyết phục người dùng. Cho biết **loại** và **dấu hiệu** giúp người dùng tin và hành động — đây cũng chính là "điểm mới" của sản phẩm so với bài báo chỉ phân loại nhị phân.


---

## 2. HIỆN TRẠNG DỮ LIỆU (đã kiểm chứng bằng script `data/scripts/eda_stats.py`)

### 2.1 Ba file dữ liệu đang có

| File | Số dòng | Nhãn chính | Nhãn phụ | Ghi chú |
|---|---|---|---|---|
| `data/scam_sms_dataset.csv` | **25.829** | `label` 5 lớp: legitimate 13.958 · scam 10.639 · fake_news 721 · spam 478 · reference 33 | — | Đã khử trùng lặp, không null. Độ dài trung vị 101 ký tự (max 18.181 — bài báo dài) |
| `Hieu/dataset_master_corpus/vietnamese_master_unified_dataset.csv` | **22.762** | `is_scam`: 1 = 12.555 · 0 = 10.207 | `category` (17+ loại), `risk_level` (SAFE/HIGH/CRITICAL…), `channel` (sms 17.250 · social_post 4.896 · news_case 533 · voice_call 27 · chat_dialogue 23) | **Giàu nhãn nhất — nên làm dataset huấn luyện chính** |
| `Hieu/dataset_sms_corpus/vietnamese_unified_scam_sms_corpus.csv` | **9.972** | `is_scam`: 0 = 7.244 · 1 = 2.728 | `category`, `risk_level` | Phần lớn trùng / nằm trong 2 file trên |

**Số chuỗi trùng nhau giữa các file** (quan trọng — xem mục 9 Rủi ro):
- `data/scam_sms` ↔ `Hieu/master`: **18.482**
- `data/scam_sms` ↔ `Hieu/sms_corpus`: 2.073
- `Hieu/master` ↔ `Hieu/sms_corpus`: 2.581

### 2.2 Các loại lừa đảo trong `Hieu/master` (cột `category`)

`general_online_scam` 6.120 · `loan_scam` 2.570 · `lottery_prize` 1.177 · `banking_phishing` 1.124 · `authority_impersonation` (giả danh công an) 985 · `fake_employment` (việc làm giả) 529 · `financial_investment` 37 · … Nhóm hợp pháp: `legitimate_daily_chat` 7.987 · `legitimate_banking_otp` 1.407 · `legitimate_telecom_service` 813.

### 2.3 Quyết định về dữ liệu (khuyến nghị)

1. **Gộp 3 file thành 1 file chuẩn** `data/processed/master_final.csv` với các cột:
   `text · label (5 lớp) · is_scam · category · risk_level · channel · source · split`
   - Dòng trùng giữa các file → **giữ bản có nhiều nhãn nhất** (bản từ `Hieu/master` có category + risk_level, join thêm `label` 5 lớp từ `data/scam_sms` theo key).
2. **Khử trùng lặp bằng key chuẩn hóa** (lowercase + gộp khoảng trắng — giống logic MD5 trong `to_csv_normalize.py`) **TRƯỚC KHI** chia train/val/test → chống rò rỉ dữ liệu (data leakage).
3. **Chia stratified 70/15/15** theo `is_scam` (nhiều lớp category quá nhỏ nên stratify theo `is_scam` là đủ).
4. `reference` (33 dòng — bài báo cảnh báo) → **không đưa vào huấn luyện**, để riêng làm "kiến thức tra cứu" (hướng phát triển RAG nếu mở rộng).
5. Lưu `random_state=42` để mọi thí nghiệm **tái lập được**.

> ⚠️ Lưu ý kỹ thuật khi đọc file: nhiều bản ghi chứa xuống dòng bên trong (file `scam_sms_dataset.csv` có 38.012 dòng vật lý nhưng chỉ 25.829 bản ghi). Luôn đọc bằng `pd.read_csv(...)`, không đếm dòng bằng text editor.

---

## 3. THIẾT KẾ BÀI TOÁN MACHINE LEARNING

### 3.1 Chọn nhiệm vụ

| Nhiệm vụ | Kiểu | Nhãn | Ưu tiên |
|---|---|---|---|
| N1 — Phát hiện lừa đảo | Phân loại nhị phân | `is_scam` | **Chính** — làm trước, phải tốt |
| N2 — Loại lừa đảo | Phân loại đa lớp (chỉ tin là scam) | `category` (gộp còn ~7–8 lớp chính) | Phụ — tăng giá trị sản phẩm |
| N3 — Mức rủi ro | Phân loại thứ tự | `risk_level` (LOW/MEDIUM/HIGH/CRITICAL) | Phụ — có thể suy ra từ N1 + N2 |

**Chiến lược 2 bước (cascade)** — đơn giản, dễ làm, dễ giải thích:
1. Mô hình N1 chấm điểm 0–1 cho mọi tin.
2. Nếu điểm ≥ ngưỡng → mô hình N2 phân loại loại lừa đảo; mức rủi ro suy từ loại + điểm.

> Làm N1 thật tốt trước. N2/N3 chỉ làm khi N1 đã đạt mục tiêu. Với NCKH: N1 tốt + N2 thô + demo chạy thật là đủ xuất sắc.

### 3.2 Chọn ngưỡng quyết định — nghĩ theo "chi phí sai lầm"

- **Bỏ sót lừa đảo (False Negative)**: người dùng mất tiền → RẤT tốn kém.
- **Báo nhầm tin thật (False Positive)**: người dùng khó chịu, mất niềm tin → ít tốn hơn.

→ Chọn ngưỡng sao cho **Recall lớp scam cao (~0,97–0,98) dù chấp nhận Precision thấp hơn (~0,90)**. Vẽ đường Precision–Recall trên tập val và chọn ngưỡng từ đó — đừng mặc định 0,5.


---

## 4. KIẾN THỨC NỀN CẦN NẮM (học song song với lộ trình)

> Không cần học hết trước khi làm. Mỗi giai đoạn trong mục 5 chỉ rõ cần đọc gì. Tổng thời gian tự học ước tính ~25–35 giờ.

### 4.1 Bậc 1 — Machine Learning cổ điển với scikit-learn (cần cho GĐ2)

| Khái niệm | Ý nghĩa trong đề tài | Đọc ở đâu |
|---|---|---|
| Bag-of-Words / TF-IDF | Biến text thành vector số; biết từ nào "đặc trưng" cho lớp nào | sklearn docs: *Text feature extraction* |
| N-gram (word 1–2, char 3–5) | Bắt cụm "khoan vay", "gui tien ngay"; char n-gram chống lỗi chính tả/vòng tránh từ khóa | sklearn `TfidfVectorizer(ngram_range=...)` |
| Logistic Regression | Baseline mạnh cho text, cho biết trọng số từng từ | sklearn docs |
| Naive Bayes, Linear SVM | 2 baseline so sánh | sklearn docs |
| Train/Val/Test, stratified split | Đánh giá trung thực khi lớp không cân bằng | `train_test_split(stratify=...)` |
| Precision / Recall / F1 / Confusion matrix | Đo đúng bài toán cảnh báo; F1 nào (macro/weighted/binary) dùng khi nào | `classification_report` |
| Cross-validation (k-fold) | Đánh giá ổn định với dữ liệu ~25k | `cross_val_score` |

**Mục tiêu tự kiểm**: giải thích được vì sao "Recall cao quan trọng hơn Precision" trong bài toán lừa đảo, và vì sao phải khử trùng lặp TRƯỚC khi chia train/test.

### 4.2 Bậc 2 — Deep Learning & Transformer (cần cho GĐ3)

| Khái niệm | Ý nghĩa | Đọc ở đâu |
|---|---|---|
| Word embedding, self-attention | Biểu diễn từ theo ngữ cảnh — "nhận" khác "nhận tiền mặt" | *The Illustrated Transformer* (Jay Alammar) |
| Fine-tuning | Lấy PhoBERT huấn luyện sẵn → train thêm 3–5 epoch trên dữ liệu lừa đảo | HuggingFace NLP Course chương 1–3 (miễn phí) |
| **PhoBERT** | BERT tiếng Việt (VinAI 2020) — cần **tách từ** trước | Paper arXiv:2003.00744 + model card `vinai/phobert-base` |
| XLM-RoBERTa | Lựa chọn thay thế đa ngôn ngữ, không cần tách từ | arXiv:1911.02116 |
| Tokenizer, max_len, padding | SMS ngắn (~30–60 token), bài FB dài → max_len 256 an toàn cho 8GB | HF Course chương 6 |
| AdamW, lr 2e-5, early stopping | Siêu tham số fine-tune chuẩn | HF Course chương 3 |
| fp16, gradient accumulation | Vừa GPU 8GB: batch 16–32 | PyTorch `autocast` |
| Tách từ tiếng Việt | `underthesea.word_sent("chào bạn")` | GitHub `underthesea` |

**Chuỗi học gợi ý**: video Transformer 15 phút → HF Course chương 1–3 với model nhỏ → lướt paper PhoBERT → fine-tune trên chính dữ liệu của bạn theo GĐ3.

### 4.3 Bậc 3 — Đánh giá mô hình nâng cao (cần cho GĐ4–GĐ5)

- **Precision–Recall curve & chọn ngưỡng**: `precision_recall_curve`, `PrecisionRecallDisplay`.
- **Bất cân bằng lớp**: `class_weight="balanced"`, oversampling nhẹ, hoặc chỉ cần chọn ngưỡng — dữ liệu của bạn 55/45 nên không nghiêm trọng.
- **Phân tích lỗi (error analysis)**: in 20–50 mẫu sai, đọc tay, phân nhóm nguyên nhân → việc **cải thiện nhanh nhất** và là "phân tích sâu" đẹp trong báo cáo.
- **Calibration**: muốn xuất "điểm rủi ro 0–87%" cần mô hình hiệu chỉnh (`CalibratedClassifierCV` cho baseline; Brier score để kiểm tra).
- **Kiểm thử ngoài (out-of-sample)**: tự thu 30–50 tin MỚI (tin ngân hàng thật, tin gia đình, lừa đảo mới trên báo) → thước đo "thực chiến" trung thực nhất.

### 4.4 Bậc 4 — Đóng gói sản phẩm (cần cho GĐ6)

- **FastAPI**: tutorial chính thức (12 bài ngắn) — đủ viết `/predict`.
- **Streamlit**: docs "Get started" + `st.text_area`, `st.button`, `st.metric` — demo trong 1 buổi.
- **ONNX export**: `transformers.onnx` / `optimum` — chạy nhanh trên CPU khi demo.
- **Git cơ bản**: commit mỗi khi chạy được một bước; tag `v0.1-baseline`, `v0.2-phobert`…

### 4.5 Danh mục tài liệu nên đọc (theo thứ tự)

1. HuggingFace NLP Course — https://huggingface.co/learn (miễn phí, có thực hành)
2. sklearn — *Text feature extraction*: https://scikit-learn.org/stable/
3. Paper PhoBERT (arXiv:2003.00744) + model `vinai/phobert-base` trên HuggingFace
4. Blog *The Illustrated Transformer* — Jay Alammar
5. Repo CLEDIAN (nguồn dữ liệu chính của bạn) — đọc để trích dẫn & so sánh: https://github.com/shironguyen2507/CLEDIAN
6. Google Scholar: `"SMS phishing detection Vietnamese"`, `"scam message classification BERT"` — 5–10 bài gần nhất cho phần "Tổng quan" báo cáo NCKH
7. (Tùy chọn nâng cao) *Designing Machine Learning Systems* — Chip Huyen, chương 1–4


---

## 5. QUY TRÌNH 8 GIAI ĐOẠN (làm theo đúng thứ tự)

> Mỗi giai đoạn có: **Mục tiêu → Việc cần làm → Sản phẩm đầu ra → Tiêu chí "đạt"**. Không chuyển giai đoạn khi chưa đạt tiêu chí.

### GĐ0 — Chuẩn bị môi trường (1 buổi)

**Hiện trạng máy** (đã kiểm tra): Python 3.13.5 · pandas 2.3.2 · scikit-learn 1.8.0 · **torch 2.11 + CUDA hoạt động (RTX 4060 8GB)** · fastapi ✅. **Còn thiếu**: transformers, datasets, accelerate, underthesea, streamlit, onnxruntime.

Cài phần còn thiếu (chạy từ thư mục gốc `D:\nckh\NCKH`):

```powershell
python -m pip install -U "transformers[torch]" datasets accelerate underthesea
python -m pip install streamlit onnxruntime onnx jupyterlab
python -m pip freeze > requirements.txt
git add requirements.txt; git commit -m "GD0: khoa phan mem"
```

Kiểm tra GPU PyTorch nhận đúng:

```powershell
python -c "import torch; print(torch.cuda.get_device_name(0))"
```

**Tiêu chí đạt**: các import không lỗi, GPU in ra tên card, `requirements.txt` đã commit.

---

### GĐ1 — Hợp nhất dữ liệu thành 1 file chuẩn + chia tách (2–3 buổi)

**Việc cần làm** — viết `src/prepare_data.py` (cấu trúc repo xem mục 6):

1. Đọc 3 file CSV (đều `encoding="utf-8-sig"`).
2. Tạo cột key chuẩn hóa: `key = " ".join(text.split()).lower()`.
3. Merge: bắt đầu từ `Hieu/master` (giàu nhãn nhất) → join `label` 5 lớp từ `data/scam_sms` theo key → append các dòng **chưa từng xuất hiện** từ `data/scam_sms` và `Hieu/sms_corpus`.
4. Loại `reference` (33 dòng) khỏi tập huấn luyện — lưu riêng `data/processed/reference_knowledge.csv`.
5. Điền mặc định: thiếu `category` → `"unknown"`; thiếu `risk_level` → suy từ nhãn (scam → HIGH, còn lại → SAFE).
6. Chia **stratified theo `is_scam`** 70/15/15 với `random_state=42` → lưu `train.csv / val.csv / test.csv` + in thống kê.

Khung code:

```python
import pandas as pd
from sklearn.model_selection import train_test_split

def norm_key(t: str) -> str:
    return " ".join(str(t).split()).lower()

master = pd.read_csv(r"Hieu/dataset_master_corpus/vietnamese_master_unified_dataset.csv",
                     encoding="utf-8-sig")
five = pd.read_csv(r"data/scam_sms_dataset.csv", encoding="utf-8-sig")
five["key"] = five["text"].map(norm_key)
label_map = dict(zip(five["key"], five["label"]))

master["key"] = master["text"].map(norm_key)
master["label"] = master["key"].map(label_map)

seen = set(master["key"])
extra = five[~five["key"].isin(seen)].copy()
extra["is_scam"] = (extra["label"] == "scam").astype(int)
extra["category"] = extra["label"].map(
    {"scam": "general_online_scam"}).fillna("unknown")
extra["risk_level"] = extra["is_scam"].map({1: "HIGH", 0: "SAFE"})
# ... can bu cac cot con thieu cua extra, gop master + extra -> df

df = pd.concat([master, extra_renamed], ignore_index=True)
df = df.drop_duplicates("key")
df = df[df["label"].fillna("reference") != "reference"]
tr, tmp = train_test_split(df, test_size=0.30, stratify=df["is_scam"], random_state=42)
va, te = train_test_split(tmp, test_size=0.50, stratify=tmp["is_scam"], random_state=42)
```

**Sản phẩm**: `data/processed/master_final.csv`, `train/val/test.csv`, notebook `notebooks/01_eda.ipynb` (biểu đồ phân bố nhãn, độ dài, top từ khóa lớp scam).

**Tiêu chí đạt**:
- [ ] train ∩ val ∩ test = ∅ theo key chuẩn hóa (kiểm tra bằng set)
- [ ] Không null ở `text`, `is_scam`
- [ ] Tỷ lệ lớp trong 3 tập chênh < 1 điểm %
- [ ] Notebook EDA có ≥ 3 biểu đồ (phân bố nhãn, độ dài, word-cloud/top-20 từ khóa lớp scam)

---

### GĐ2 — Baseline cổ điển: TF-IDF + Logistic Regression (3–4 buổi)

**Vì sao phải làm baseline dù muốn dùng AI hiện đại ngay**: baseline (i) cho con số sàn để biết transformer đáng tiền không, (ii) chạy nhanh để thử ý tưởng tiền xử lý, (iii) là điểm so sánh bắt buộc trong báo cáo NCKH.

**Việc cần làm** — viết `src/train_baseline.py`:

```python
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.metrics import classification_report

tr = pd.read_csv("data/processed/train.csv", encoding="utf-8-sig")
va = pd.read_csv("data/processed/val.csv", encoding="utf-8-sig")

pipe = make_pipeline(
    TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, min_df=2),
    LogisticRegression(max_iter=2000, class_weight="balanced", C=2.0),
)
pipe.fit(tr["text"], tr["is_scam"])
print(classification_report(va["is_scam"], pipe.predict(va["text"])))
```

Thử nghiệm có kiểm soát (đổi MỖI lần 1 thứ, ghi bảng `results/baseline_results.md`):
- word n-gram (1,2) vs (1,3); thêm/không `char` n-gram (3,5)
- `LogisticRegression` vs `MultinomialNB` vs `LinearSVC`
- tiền xử lý: giữ nguyên dấu (khuyên dùng) vs `underthesea.word_sent`

**Sản phẩm**: script chạy lại được + bảng ≥ 3 mô hình + model `models/baseline.joblib`.

**Tiêu chí đạt** (tham khảo — dữ liệu nhiều tin cùng khuôn mẫu nên thường đạt dễ):
- [ ] F1 lớp scam trên val ≥ 0,92; Recall ≥ 0,92
- [ ] Bảng so sánh ≥ 3 baseline
- [ ] Vẽ được Precision–Recall curve trên val + chọn ngưỡng thô


---

### GĐ3 — Fine-tune PhoBERT (1 tuần — trái tim của đề tài)

**Kiến thức bắt buộc trước khi làm**: mục 4.2 (HF Course chương 3).

**Chọn model** (thử theo thứ tự, giữ model tốt nhất):

| Model trên HuggingFace | Tách từ | VRAM | Ghi chú |
|---|---|---|---|
| `vinai/phobert-base` | **CẦN** `underthesea.word_sent` | ~1.1GB | Tốt nhất cho tiếng Việt thuần |
| `xlm-roberta-base` | không cần | ~1.1GB | Chống lỗi chính tả / vòng tránh từ tốt hơn |
| `distilbert-base-multilingual-cased` | không cần | ~0.7GB | Nhẹ, nhanh, đủ dùng |

**Việc cần làm** — viết `src/train_phobert.py`:

```python
import pandas as pd
from underthesea import word_sent
from transformers import (AutoTokenizer, AutoModelForSequenceClassification,
                          TrainingArguments, Trainer, DataCollatorWithPadding)
from datasets import Dataset

MODEL = "vinai/phobert-base"
tr = pd.read_csv("data/processed/train.csv", encoding="utf-8-sig")
va = pd.read_csv("data/processed/val.csv", encoding="utf-8-sig")

# PhoBERT yeu cau tach tu: "Anh gui tien ho" -> "Anh gui tien_ho"
tr["text_seg"] = tr["text"].astype(str).map(lambda s: " ".join(word_sent(s)))
va["text_seg"] = va["text"].astype(str).map(lambda s: " ".join(word_sent(s)))

tok = AutoTokenizer.from_pretrained(MODEL)
enc = lambda d: tok(d["text_seg"], truncation=True, max_length=256)
tr_ds = Dataset.from_pandas(tr[["text_seg", "is_scam"]]).map(enc, batched=True)
va_ds = Dataset.from_pandas(va[["text_seg", "is_scam"]]).map(enc, batched=True)

model = AutoModelForSequenceClassification.from_pretrained(MODEL, num_labels=2)
args = TrainingArguments(
    output_dir="models/phobert", learning_rate=2e-5,
    per_device_train_batch_size=16, per_device_eval_batch_size=32,
    num_train_epochs=4, fp16=True,               # RTX 4060 8GB: bat fp16
    eval_strategy="epoch", save_strategy="epoch", save_total_limit=2,
    load_best_model_at_end=True, metric_for_best_model="f1", seed=42,
)
def metrics(p):
    from sklearn.metrics import precision_recall_fscore_support
    y, yh = p.label_ids, p.predictions.argmax(-1)
    pr, rc, f1, _ = precision_recall_fscore_support(y, yh, average="binary")
    return {"precision": pr, "recall": rc, "f1": f1}

Trainer(model=model, args=args, train_dataset=tr_ds, eval_dataset=va_ds,
        tokenizer=tok, compute_metrics=metrics).train()
```

**Mẹo cho GPU 8GB**: batch 16 + `fp16=True`; hết VRAM → giảm batch còn 8 + `gradient_accumulation_steps=2`, hoặc `max_length` 256 → 128 · 3–5 epoch là đủ (nhiều hơn quá khớp) · luôn `load_best_model_at_end`.

**Sản phẩm**: checkpoint tốt nhất trong `models/phobert/` + đồ thị loss/F1 theo epoch + bảng so sánh **baseline vs PhoBERT** (`results/model_comparison.md`).

**Tiêu chí đạt**:
- [ ] F1 val ≥ 0,95 và cao hơn baseline ≥ 2 điểm
- [ ] Có đồ thị train/val theo epoch
- [ ] Chạy lại với đúng seed → kết quả chênh ≤ 0,5 điểm

---

### GĐ4 — Đánh giá sâu + phân tích lỗi (3–4 buổi)

**Việc cần làm** — viết `src/evaluate.py`:
1. Đánh giá trên **test** (chỉ chạm 1 lần cuối — không chỉnh gì sau khi nhìn kết quả test).
2. Confusion matrix (heatmap seaborn) + `classification_report` đầy đủ.
3. Precision–Recall curve → **chọn ngưỡng** theo mục 3.2 (ưu tiên Recall scam ≥ 0,97).
4. In 50 mẫu dự đoán sai trên test → đọc tay → phân nhóm nguyên nhân: (a) tin thật báo nhầm, (b) lừa đảo bỏ sót — kiểu gì, (c) nhãn gốc sai?, (d) tin dịch máy gây nhiễu…
5. Ghi "sổ lỗi" `results/error_analysis.md`: mỗi nhóm lỗi + 1 ý tưởng khắc phục.

**Sản phẩm**: `results/test_report.md` (confusion matrix + F1 + ngưỡng chọn + 50 lỗi phân nhóm).

**Tiêu chí đạt**: báo cáo trên + ≥ 3 ý tưởng cải tiến có bằng chứng (chọn 1 cái mạnh nhất làm ở GĐ5).

---

### GĐ5 — Nâng cấp: loại lừa đảo + mức rủi ro + điểm tin cậy (1 tuần)

Chọn **MỘT** trong 2 hướng (ít thời gian → chọn A):

**Hướng A — Cascade 2 model (khuyến nghị)**:
- Model 1 = PhoBERT binary (đã có từ GĐ3).
- Model 2 = PhoBERT phân loại `category`, **chỉ train trên dòng `is_scam=1`**, gộp lớp < 100 dòng vào `other_scam`. Bộ lớp gợi ý: `loan_scam · lottery_prize · banking_phishing · authority_impersonation · fake_employment · general_online_scam · other_scam`.
- Mức rủi ro = bảng quy tắc từ (category, xác suất model 1) → LOW/MEDIUM/HIGH/CRITICAL.

**Hướng B — Multi-task 1 model (học thuật hơn)**: 1 backbone + 3 đầu ra (binary + category + risk), loss = w1·L1 + w2·L2 + w3·L3. Viết thành "điểm mới" trong báo cáo; khó hơn, dễ sai số.

**Sản phẩm**: `src/infer.py` — hàm duy nhất:

```python
def predict(text: str) -> dict:
    return {"is_scam": 1, "prob": 0.97, "category": "loan_scam",
            "risk_level": "HIGH", "signals": [...], "advice": "..."}
```

**Tiêu chí đạt**:
- [ ] `predict("Chuc mung ban trung thuong 50 trieu, goi 09xx...")` trả dict đúng ý nghĩa
- [ ] Accuracy category trên các dòng scam của test ≥ 0,75
- [ ] Quy tắc risk ghi rõ trong file (để trích dẫn báo cáo)

<!--CONT-->




