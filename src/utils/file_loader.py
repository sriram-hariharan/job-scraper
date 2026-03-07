def load_lines(path: str):

    items = []

    with open(path) as f:
        for line in f:
            val = line.strip()
            if val:
                items.append(val)

    return items