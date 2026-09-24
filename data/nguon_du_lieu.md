# Nguồn dữ liệu — AI Cảnh báo Lừa đảo cho người Việt

Dự án gồm **2 file**:
- `scam_dataset.jsonl` — toàn bộ dữ liệu huấn luyện (1 file duy nhất)
- `nguon_du_lieu.md` — file này (liệt kê nguồn + link)

## 1. File dữ liệu: `scam_dataset.jsonl`

Mỗi dòng 1 JSON, đã khử trùng lặp (MD5 trên text chuẩn hóa) và xáo trộn seed=42:

```json
{"text": "...", "label": "...", "channel": "...", "language": "vi", "source": "..."}
```

| Nhãn | Ý nghĩa | Số lượng |
|---|---|---|
| `scam` | tin nhắn/lời nhắn lừa đảo thật | 10,639 |
| `legitimate` | tin nhắn bình thường, tin thật | 13,958 |
| `spam` | tin rác quảng cáo (dịch máy sang tiếng Việt) | 478 |
| `fake_news` | bài đăng Facebook tin giả (chọn lọc `label=1`) | 721 |
| `reference` | bài báo cảnh báo thủ đoạn lừa đảo VN — **không phải tin nhắn lừa đảo**, dùng cho RAG/knowledge | 33 |

Kênh (`channel`): `sms` 21,515 · `social_post` 4,281 · `news` 33. **Tổng: 25,829 bản ghi, 100% tiếng Việt.**

Chia train/val/test khi huấn luyện (tự chia, seed=42):
```python
import json, random
rows = [json.loads(l) for l in open(r"D:\nckh\data\scam_dataset.jsonl", encoding="utf-8")]
random.seed(42); random.shuffle(rows)
n = len(rows); train, val, test = rows[:int(n*.8)], rows[int(n*.8):int(n*.9)], rows[int(n*.9):]
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
