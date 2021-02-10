from rexfw.pdfs import normal

with open("data.csv") as f:
    data = f.readlines()

pdf = normal.Normal()
