import pandas as pd

## PART 1: JUST THE RESOLVER

df = pd.read_csv("geos_resolved.csv")
df.errors = df.errors.str[:25] + "..."

print("\n1. Summary of resolution errors (NaN = no error):\n")
print(df.errors.value_counts(dropna=False))

print("\n2. Number of OECD places mapped to each DCID. Observe N to 1 issues.")
print("(NaN = places that failed to resolve to DCID):\n")
print(df.dcid.value_counts(dropna=False).head(40))

print(
    "\n3. Number of OECD places mapped to each DCID, grouped by namespace (only those with N to 1 issues):\n"
)
df['namespace'] = df['dcid'].map(lambda x: str(x).split('/')[0])
with pd.option_context('display.max_rows', None):
    print(
        df.groupby(['namespace', 'dcid']).filter(lambda x: len(x) > 1).groupby(
            ['namespace', 'dcid']).size())

## PART 2: Including hardcoding for nuts, USA, etc.
#  Just use the diffs in regid2dcid.json.
