import os

def append_new_companies(file_path, companies):

    if not companies:
        return

    existing = set()

    if os.path.exists(file_path):
        with open(file_path) as f:
            existing = {line.strip() for line in f if line.strip()}

    new = [c for c in companies if c not in existing]

    if not new:
        return

    with open(file_path, "a") as f:
        for c in new:
            f.write(c + "\n")