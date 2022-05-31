import math
import re

import pandas as pd

pd.set_option("display.max_columns", None)

mixs_tsv = "../target/mixs6.tsv"

mixs_frame = pd.read_csv(mixs_tsv, sep="\t")

print(mixs_frame.shape)

stragglers = mixs_frame.loc[~mixs_frame.iloc[:, 13].isna()].copy()
canonical = mixs_frame.loc[mixs_frame.iloc[:, 13].isna()].copy()

stragglers["MIXS ID"] = stragglers["github ticket"]
stragglers["github ticket"] = stragglers["Unnamed: 13"]

reconstituted = pd.concat([canonical, stragglers])
# drop 14th column
# after nudging
reconstituted = reconstituted.iloc[
                :, [j for j, c in enumerate(reconstituted.columns) if j != 13]
                ]

print(reconstituted["Environmental package"].value_counts(dropna=False))
# this includes Environmental package * slot usage, sometimes with variants
# Expected value, Value syntax (plus parse), Example, Section (show NAs), Requirement, Preferred unit, Occurrence


print(reconstituted["Value syntax"].value_counts(dropna=False))

tidy_vs = list(reconstituted["Value syntax"])
tidy_vs = [i for i in tidy_vs if pd.isnull(i) is False]

# todo should we be applying this to non-uniqued Value syntaxes
abstractions = []
pattern = re.compile(r"({[^{}]*})")
# todo won't get {{text}|{float} {unit}};{float} {unit}
for i in tidy_vs:
    for match in pattern.finditer(i):
        abstractions.append(match.group(1))

print(pd.Series(abstractions).value_counts(dropna=False))

# ---

anonymous = reconstituted.iloc[
            :, [j for j, c in enumerate(reconstituted.columns) if j != 0]
            ].copy()

anonymous.drop_duplicates(inplace=True)

id_counts = (
    anonymous["MIXS ID"]
        .value_counts()
        .rename_axis("MIXS ID")
        .reset_index(name="variant_count")
)

anonymous = anonymous.merge(right=id_counts)

singletons = anonymous.loc[anonymous["variant_count"].eq(1)]

variants = anonymous.loc[anonymous["variant_count"].gt(1)]

var_id = list(set(variants["MIXS ID"]))
var_id.sort()

lod = []
for i in var_id:
    variant_count = id_counts.loc[id_counts["MIXS ID"].eq(i), "variant_count"].squeeze()
    current_row = {"MIXS ID": i, "variant_count": variant_count}
    temp = variants.loc[variants["MIXS ID"].eq(i)]
    temp = temp.to_dict(orient="dict")
    current_list = []
    for ok, ov in temp.items():
        unique_vals = set(ov.values())
        uv_count = len(unique_vals)
        if uv_count > 1:
            current_list.append(f"{ok}={uv_count}")
    current_list.sort()
    current_string = "|".join(current_list)
    current_row["variants"] = current_string
    lod.append(current_row)
evidence_frame = pd.DataFrame(lod)

print(evidence_frame)

merged_frame = reconstituted.merge(how="left", right=evidence_frame)

merged_frame.sort_values(
    by=["Structured comment name", "Environmental package"], inplace=True
)

merged_frame.to_csv("../target/mixs_variant_documentation.tsv", sep="\t", index=False)

mf_lod = merged_frame.to_dict(orient="records")

variants_long_lod = []
for i in mf_lod:
    if not pd.isnull(i["variants"]):
        variants = i["variants"].split("|")
        variants = [j.split("=")[0] for j in variants]
        for k in variants:
            variants_long_lod.append(
                {
                    "MIXS ID": i["MIXS ID"],
                    "scn_lc": i["Structured comment name"].lower(),
                    "Environmental package": i["Environmental package"],
                    "column": k,
                    "value": i[k],
                }
            )

variants_long_df = pd.DataFrame(variants_long_lod)
print(variants_long_df)

variants_long_df.to_csv("../target/variants_long.tsv", sep="\t", index=False)
