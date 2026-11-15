# %% [markdown]
# @header
#
# AI policy: AI-tutor. An assistant may explain hashing; the finding and its wording for the release engineer are yours.

# %%
import os, sys, subprocess
from pathlib import Path

IN_COLAB = "google.colab" in sys.modules
if IN_COLAB:
    REPO_URL = "https://github.com/SDAIAAcademy/ae-403.git"
    if not Path("/content/ae-403").exists():
        subprocess.run(["git", "clone", "-q", REPO_URL, "/content/ae-403"], check=True)
    os.chdir("/content/ae-403/labs")
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-r", "requirements-colab.txt"], check=True)
else:
    while not Path("_tools").exists() and Path.cwd() != Path.cwd().parent:
        os.chdir("..")  # solutions/ notebooks run from labs/
sys.path.insert(0, os.getcwd())
import relia as U
import json
import pandas as pd

# %% [markdown]
# ## 1 · Read the three provenance records
#
# Shuaib Al-Qubaisi has three candidate artefacts for Athar's fallback model in
# `data/models/`. Each folder holds a configuration, a tokenizer, two weight shards, a licence
# and a model card. The weights are random bytes for the course, not a model: the integrity
# questions are the same. `provenance.json` records, for each artefact, its publisher, source,
# revision, where Rasael obtained it, its licence and the publisher's SHA-256 of every file.

# %%
prov = json.loads((U.MODELS / "provenance.json").read_text(encoding="utf-8"))
print(pd.DataFrame([{k: v for k, v in p.items() if k != "publisher_sha256"} for p in prov]).to_string(index=False))

# %% [markdown]
# ## 2 · Hash every file of each artefact
#
# ✏️ **Exercise** · Return one row per file: artefact, file, size in bytes and SHA-256
# (`U.model_files(folder)`, `U.sha256_file(path)`).

# %%
def hash_all(prov) -> pd.DataFrame:
    # BEGIN SOLUTION
    rows = []
    for p in prov:
        folder = U.MODELS / p["artefact"]
        for f in U.model_files(folder):
            rows.append({"artefact": p["artefact"], "file": f, "bytes": (folder / f).stat().st_size,
                         "sha256": U.sha256_file(folder / f)})
    return pd.DataFrame(rows)
    # END SOLUTION

# %%
try:
    hashes = hash_all(prov)
except NotImplementedError:
    hashes = U.reference("lab_4_1_hashes")
U.keep("lab_4_1_hashes", hashes)
print(hashes.assign(sha256=hashes.sha256.str[:16] + "…").to_string(index=False))

# %% [markdown]
# ## 3 · Compare with the publisher's list
#
# ✏️ **Exercise** · For each artefact, list the files whose hash differs from the publisher's,
# the files the publisher did not list, and the files that are missing.

# %%
def compare(prov, hashes: pd.DataFrame) -> pd.DataFrame:
    # BEGIN SOLUTION
    rows = []
    for p in prov:
        mine = dict(hashes[hashes.artefact == p["artefact"]][["file", "sha256"]].values)
        theirs = p["publisher_sha256"]
        rows.append({"artefact": p["artefact"], "obtained_from": p["obtained_from"],
                     "changed": sorted(f for f in mine if f in theirs and mine[f] != theirs[f]),
                     "unlisted": sorted(set(mine) - set(theirs)), "missing": sorted(set(theirs) - set(mine))})
    return pd.DataFrame(rows)
    # END SOLUTION

# %%
try:
    cmp = compare(prov, hashes)
except NotImplementedError:
    cmp = U.reference("lab_4_1_compare")
U.keep("lab_4_1_compare", cmp)
print(cmp.to_string(index=False))
bad = cmp[cmp.changed.apply(len) > 0]
U.ok(list(bad.artefact) == ["athar-small-v1-mirror"] and bad.changed.iloc[0] == ["model-00002-of-00002.safetensors"],
     "one file of the mirrored artefact differs from what the publisher released")

# %% [markdown]
# ## 4 · Write the finding for the release engineer
#
# ✏️ **Exercise** · Write the finding as a dictionary: artefact, file, expected and found hash
# (first 16 characters), what it means, and the decision. Keep it factual: a changed hash proves
# the bytes differ, not who changed them or why.

# %%
def finding(cmp, hashes, prov) -> dict:
    # BEGIN SOLUTION
    row = cmp[cmp.changed.apply(len) > 0].iloc[0]
    f = row.changed[0]
    p = next(x for x in prov if x["artefact"] == row.artefact)
    found = hashes[(hashes.artefact == row.artefact) & (hashes.file == f)].sha256.iloc[0]
    return {"artefact": row.artefact, "file": f, "expected": p["publisher_sha256"][f][:16], "found": found[:16],
            "meaning": "the bytes of this shard are not the ones the publisher released; the copy came from a third-party mirror",
            "decision": "do not admit; obtain the artefact from the publisher and verify its signature (Lab 4.2)"}
    # END SOLUTION

# %%
try:
    F = finding(cmp, hashes, prov)
except NotImplementedError:
    F = U.reference("lab_4_1_finding")
U.keep("lab_4_1_finding", F)
for k, v in F.items():
    print(f"{k:10s} {v}")
other = [p["licence"] for p in prov if p["artefact"] == "athar-tiny-q4"][0]
print("\nAlso note for Lab 4.3: athar-tiny-q4 hashes match, and its licence is", repr(other))

# %% [markdown]
# **Look at** the limit of this check: the publisher's list came in the same channel as the
# files. Anyone who can change a shard on a mirror can change a list on it too. A hash list
# proves integrity only when it is signed by the publisher: that is Lab 4.2.
#
# ✱ **Stretch** · Which file types can run code when loaded (a pickled `.bin` or `.pt`, a
# custom model class)? List the extensions your admission policy should refuse.

# %% [markdown]
# ## Check yourself
#
# 1. The mirror's provenance record lists the right hashes. Why does that not help?
#    <details><summary>Answer</summary>The record lists the publisher's hashes, but the file on the mirror is different; only hashing the file you received shows it.</details>
# 2. What does a matching hash not tell you?
#    <details><summary>Answer</summary>That the hash list itself is genuine, that the model is safe to load, or that its licence allows your use.</details>
# 3. Why hash every file, not only the weights?
#    <details><summary>Answer</summary>A changed tokenizer or configuration changes the model's behaviour as surely as changed weights.</details>
#
# **Carry forward** · The finding (`data/reference/lab_4_1_finding.json`) is the first rejected artefact in Lab 4.3's gate.
