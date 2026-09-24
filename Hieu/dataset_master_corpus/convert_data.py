import json

input_file = "vietnamese_unified_master_dataset.jsonl"
output_file = "scam_sms_dataset(1).csv"

with open(input_file, "r", encoding="utf-8") as infile, \
     open(output_file, "w", encoding="utf-8-sig", newline="") as outfile:

    # Header
    outfile.write("id,text,label\n")

    for line in infile:
        data = json.loads(line)

        id_ = data["id"]
        text = data["text"]
        label = data["is_scam"]

        # Escape dấu " nếu text có chứa
        text = text.replace('"', '""')

        # Chỉ cột text được bao bởi một cặp "
        outfile.write(f'{id_},"{text}",{label}\n')

print("Đã chuyển thành công!")