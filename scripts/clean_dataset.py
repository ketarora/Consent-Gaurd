#!/usr/bin/env python3
import sys
import json
import re
from collections import Counter

if len(sys.argv) < 3:
    print("Usage: scripts/clean_dataset.py INPUT_JSON OUTPUT_JSON")
    sys.exit(1)

input_path = sys.argv[1]
output_path = sys.argv[2]

with open(input_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

messages = data.get('messages', [])
counts = Counter()
for m in messages:
    m['text'] = re.sub(r"\bYour your\b", "Your", m.get('text', ''))
    m['text'] = re.sub(r"\s+", ' ', m['text']).strip()
    counts[m.get('category', 'unknown')] += 1

# update header counts
data['counts'] = dict(counts)
data['total_messages'] = len(messages)

a = json.dumps(data, ensure_ascii=False, indent=2)
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(a)

print('Wrote cleaned dataset to', output_path)
print('Category counts:')
for k, v in counts.items():
    print(k, v)
