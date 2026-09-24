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
        is_scam = data["is_scam"]

        # Chuyển nhãn
        if is_scam == 0:
            label = "legitimate"
        else:
            label = "scam"

        # Escape dấu " trong text
        text = text.replace('"', '""')

        # Chỉ cột text có dấu "
        outfile.write(f'{id_},"{text}",{label}\n')

print("Đã chuyển thành công!")