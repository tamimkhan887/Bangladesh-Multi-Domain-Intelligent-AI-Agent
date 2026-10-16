import pandas as pd
df = pd.read_csv("hf://datasets/Mahadih534/Institutional-Information-of-Bangladesh/data.csv")
df.to_csv("data/institution.csv", index=False)

df=pd.read_csv("hf://datasets/Mahadih534/all-bangladeshi-hospitals/all-bangladesh-hosptals.csv")
df.to_csv("data/hospitals.csv", index=False)

df = pd.read_csv("hf://datasets/Mahadih534/Bangladeshi-Restaurant-Data/restaurants.csv")
df.to_csv("data/restaurants.csv", index=False)