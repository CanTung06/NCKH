import pandas as pd
import csv

df = pd.read_json(
    "../data/scam_dataset.jsonl",
    lines=True
)

df = df[["text", "label"]].copy()
df.insert(0, "id", range(1, len(df) + 1))

with open("scam_sms_dataset.csv", "w", encoding="utf-8-sig", newline="") as f:
    f.write("id,text,label\n")

    for row in df.itertuples(index=False):
        text = str(row.text).replace('"', '""')

        f.write(f'{row.id},"{text}",{row.label}\n')

print("Done!")