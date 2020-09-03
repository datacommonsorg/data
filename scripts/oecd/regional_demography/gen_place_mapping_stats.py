import pandas as pd

## PART 1: JUST THE RESOLVER

df = pd.read_csv("geos_resolved.csv")

print("\nOECD->DCID resolved\n")
print(df.dcid.value_counts(dropna=False).head(40))

print("\nOECD->DCID errors\n")
print(df.errors.value_counts(dropna=False))

print("\nOECD->DCID errors summary\n")
df.errors = df.errors.str[:20]
print(df.errors.value_counts(dropna=False))


## PART 2: With hardcoding for nuts, USA, etc.


