# Nguồn dữ liệu — AI Cảnh báo Lừa đảo cho người Việt

Dự án gồm **2 file**:
- `scam_dataset.csv` — toàn bộ dữ liệu huấn luyện (1 file CSV duy nhất, đã chuẩn hóa)
- `nguon_du_lieu.md` — file này (liệt kê nguồn + link)

## 1. File dữ liệu: `scam_dataset.csv`

Chuyển từ JSONL gốc sang CSV và chuẩn hóa bằng `scripts/to_csv_normalize.py`
(Unicode NFC, dọn khoảng trắng, khử trùng lặp MD5, mã hóa nhãn). Các cột:

| Cột | Ý nghĩa |
|---|---|
| `id` | MD5 của text chuẩn hóa (khóa khử trùng lặp) |
| `label` | `scam` / `legitimate` / `spam` / `fake_news` / `reference` |
| `label_id` | 0=fake_news, 1=legitimate, 2=reference, 3=scam, 4=spam |
| `is_scam` | 1=scam, 0=còn lại (bài toán nhị phân) |
| `channel` | `sms` / `social_post` / `news` |
| `text` | Nội dung tin nhắn/bài đăng (tiếng Việt, giữ nguyên dấu) |
| `char_len`, `word_len` | Độ dài text (ký tự / từ) |
| `note` | Ghi chú gốc (nếu có) |

| Nhãn | Ý nghĩa | Số lượng |
|---|---|---|
| `scam` | tin nhắn/lời nhắn lừa đảo thật | 10,639 |
| `legitimate` | tin nhắn bình thường, tin thật | 13,958 |
| `spam` | tin rác quảng cáo (dịch máy sang tiếng Việt) | 478 |
| `fake_news` | bài đăng Facebook tin giả (chọn lọc `label=1`) | 721 |
| `reference` | bài báo cảnh báo thủ đoạn lừa đảo VN — **không phải tin nhắn lừa đảo**, dùng cho RAG/knowledge | 33 |

Kênh (`channel`): `sms` 21,515 · `social_post` 4,281 · `news` 33. **Tổng: 25,829 bản ghi, 100% tiếng Việt.**

Đọc dữ liệu và chia train/val/test khi huấn luyện:
```python
import pandas as pd
from sklearn.model_selection import train_test_split

df = pd.read_csv(r"D:\nckh\NCKH\data\scam_dataset.csv", encoding="utf-8-sig")
X, y = df["text"], df["label_id"]          # hoặc df["is_scam"] cho bài toán nhị phân
X_tr, X_tmp, y_tr, y_tmp = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
X_val, X_te, y_val, y_te = train_test_split(X_tmp, y_tmp, test_size=0.5, random_state=42, stratify=y_tmp)
```

## 2. Nguồn đã dùng trong `scam_dataset.jsonl`

| # | Nguồn | Link | License | Đóng góp |
|---|---|---|---|---|
| 1 | **CLEDIAN** — hệ thống phát hiện tin nhắn lừa đảo tiếng Việt | https://github.com/shironguyen2507/CLEDIAN (`datasets/raw/manual_scam.csv`, `manual_safe.csv`, `fake_news.csv`) | Chưa khai báo (repo nghiên cứu) | 9,912 SMS scam + 4,725 SMS an toàn + 4,281 bài đăng FB (721 tin giả) |
| 2 | **vietnamese_sms_dataset** — SMS ngân hàng VN (0=thật, 1=lừa đảo) | https://huggingface.co/datasets/trannguyenthaituan/vietnamese_sms_dataset | CC-BY-4.0 | 2,597 SMS |
| 3 | **vietnamese_sms_phishing_sample** — 300 SMS phishing VN | https://huggingface.co/datasets/trannguyenthaituan/vietnamese_sms_phishing_sample | CC-BY-4.0 | 17 duy nhất (283 trùng nguồn #2 sau dedup) |
| 4 | **Vietnamese-SMS-Spam-Detection** — SMS spam dịch máy sang tiếng Việt | https://github.com/HuynhPhong385/Vietnamese-SMS-Spam-Detection (`data/dataset/dataset.csv`) | Chưa khai báo | 4,264 SMS (spam 478 + ham 3,786) |
| 5 | **Bài báo cảnh báo lừa đảo VN** — Bộ CA, VnExpress, Tuổi Trẻ… (tìm qua Bing RSS) | https://bocongan.gov.vn , https://vnexpress.net , https://tuoitre.vn | Báo chí công khai | 33 bài `reference` |

## 3. Nguồn đề xuất bổ sung (chưa có trong file, link để mở rộng)

| Nguồn | Link | Ghi chú |
|---|---|---|
| **PhishVN** — 53,116 URL phishing tiếng Việt (2,587 phishing / 16,410 thật đã người xác minh) | https://doi.org/10.17632/b97hxbxtpd.4 (bài: doi.org/10.1016/j.dib.2026.113195) | CC BY 4.0; Mendeley chặn tải tự động (403) → tải thủ công trên trang, rồi thêm vào file với `channel: "url"` |
| Vietnamese_Scam_Conversation | https://huggingface.co/datasets/hoang2501/Vietnamese_Scam_Conversation | Repo mới, chưa upload file dữ liệu — theo dõi sau |
| Phần mềm phát hiện lừa đảo VN (tham khảo pattern) | https://github.com/baolam/society-fraudent , https://github.com/ductn90/La-Chan-Gia-Dinh | Dữ liệu nhúng trong vector store, chưa chuẩn hóa |

### Corpus tiếng Anh (nếu sau này muốn đa ngôn ngữ — chưa đưa vào file hiện tại)
- sidzzz07/scamshield-dataset (~85k SMS, MIT) · FredZhang7/all-scam-spam (42k email, Apache-2.0) · ealvaradob/phishing-dataset (590MB, Apache-2.0) · huynq3Cyradar/Phishing_Detection_Dataset (URL 7.5GB) · pirocheto/phishing-url (11k URL, GPL-3.0) · zefang-liu/phishing-email-dataset (18k, LGPL) · David-Egea/phishing-texts (20k, MIT) · BothBosu/scam-dialogue + multi-agent (hội thoại scam) · mytestaccforllm/final_scam (57k, Apache-2.0) · UCI SMS Spam (5.5k)
- Reddit r/scams, r/phishing qua archive công khai: https://arctic-shift.photon-reddit.com/api/posts/search

## 4. Phương pháp & lưu ý
- Chỉ dùng nguồn công khai; không cào nền tảng yêu cầu đăng nhập (Facebook/Zalo — vi phạm ToS).
- Khử trùng lặp bằng MD5 trên text lowercase chuẩn hóa khoảng trắng; loại bản ghi <5 ký tự.
- Nhãn giữ **trung thực**: bài báo mô tả lừa đảo được gán `reference` (không phải `scam`); tin giả gán riêng `fake_news`; nguồn dịch máy có chú thích trong `source`.
- Bộ 10,000 SMS an toàn của CLEDIAN còn 4,725 bản ghi duy nhất sau dedup (nhiều tin lặp mẫu) — đã loại trùng để tránh bias.
- Trước khi huấn luyện nên ẩn danh hóa số tài khoản/SĐT xuất hiện trong text nếu công bố mô hình.
