import json

with open("data/company_crawl_state.json", "r") as f:
    data = json.load(f)

count = 0
print(len(data))
for d in data:
    if "description_snippet" in d:
        count += 1
print(count)