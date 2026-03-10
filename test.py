import re

valid = []

with open("data/workday_companies.txt") as f:
    for line in f:
        line = line.strip()

        if re.match(r"https://.*\.myworkdayjobs\.com/.*", line):
            valid.append(line)

valid = sorted(set(valid))

with open("data/workday_companies.txt", "w") as f:
    for v in valid:
        f.write(v + "\n")