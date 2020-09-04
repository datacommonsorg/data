import pandas as pd

## PART 1: JUST THE RESOLVER

df = pd.read_csv("geos_resolved.csv")
df.errors = df.errors.str[:25] + "..."
df['namespace'] = df['dcid'].map(lambda x: str(x).split('/')[0])

print("""
PLACE RESOLUTION STATISTICS

This only tracks the resolution statistics from `tools/place_name_resolver/`.

The final mapping used by the OECD datasets overrides the `place_name_resolver`
mapping for special cases such as NUTS codes, USA states, etc., where we know
the OECD Region ID corresponds with a well-known standard, such as NUTS or
FIPS. To see changes in the final mapping, just use diffs in regid2dcid.json.

To regenerate this file, run `python3 gen_place_mapping_stats.py > stats.txt`
""")

print("\n1. Summary of resolution errors (NaN = no error):\n")
print(df.errors.value_counts(dropna=False))

print("""
2. Number of OECD places mapped to each DCID. Observe N to 1 issues. (NaN =
   places that failed to resolve to DCID):
""")
print(df.dcid.value_counts(dropna=False).head(40))

print("""
3. Number of OECD places mapped to each DCID, grouped by namespace (only those
   with N to 1 issues):
""")
with pd.option_context('display.max_rows', None):
    print(
        df.groupby(['namespace', 'dcid']).filter(lambda x: len(x) > 1).groupby(
            ['namespace', 'dcid']).size())

print("\n4. Number of resolved DCIDs by namespace (ignoring N to 1 issues):")
print(df.namespace.value_counts())
## PART 2: Including hardcoding for nuts, USA, etc.
#  Just use the diffs in regid2dcid.json.
