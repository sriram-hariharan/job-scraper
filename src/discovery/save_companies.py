def save_companies(companies, path):

    existing = set()

    try:
        with open(path) as f:
            existing = set(x.strip() for x in f.readlines())
    except:
        pass

    new = set(companies) - existing

    with open(path, "a") as f:
        for c in new:
            f.write(c + "\n")

    print("New Ashby companies:", len(new))