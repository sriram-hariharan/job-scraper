comp = []
with open ("data/greenhouse_companies.txt", "r") as f:
    for line in f:
        comp.append(line.strip())

print(len(comp))
print(len(set(comp)))

