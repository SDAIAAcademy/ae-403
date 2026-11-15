# %% [markdown]
# @header
#
# AI policy: AI-tutor. An assistant may explain the CycloneDX fields; the admission rules and the licence allow list are yours.

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
import uuid
import model_signing
import pandas as pd
from cyclonedx.schema import SchemaVersion
from cyclonedx.validation.json import JsonStrictValidator

# %% [markdown]
# ## 1 · Write the ML-BOM and validate it
#
# A CycloneDX bill of materials lists what a release is made of. For a model it is a component
# of type `machine-learning-model` with its publisher, version, licence, the hash of each file and
# a model card. ✏️ **Exercise** · Write `make_bom(name)` for an artefact in `data/models/`, using
# its provenance record, and validate it against the CycloneDX 1.7 schema.

# %%
prov = {p["artefact"]: p for p in json.loads((U.MODELS / "provenance.json").read_text(encoding="utf-8"))}
work = U.workdir("lab_4_3")
validator = JsonStrictValidator(SchemaVersion.V1_7)


def make_bom(name: str) -> dict:
    # BEGIN SOLUTION
    p = prov[name]
    folder = U.MODELS / name
    files = [{"type": "file", "bom-ref": f"{name}/{f}", "name": f,
              "hashes": [{"alg": "SHA-256", "content": U.sha256_file(folder / f)}]} for f in U.model_files(folder)]
    return {
        "bomFormat": "CycloneDX", "specVersion": "1.7", "version": 1,
        "serialNumber": f"urn:uuid:{uuid.uuid5(uuid.NAMESPACE_URL, 'athar/' + name)}",
        "metadata": {"component": {"type": "application", "bom-ref": "athar", "name": "Athar"}},
        "components": [{
            "type": "machine-learning-model", "bom-ref": name, "name": name, "version": p["revision"][:12],
            "publisher": p["publisher"], "licenses": [{"license": {"id": p["licence"]}}
                                                      if not p["licence"].startswith("LicenseRef-") else {"license": {"name": p["licence"]}}],
            "modelCard": {"modelParameters": {"task": "text-generation"},
                          "considerations": {"useCases": ["fallback model for Athar's degraded mode"]}},
            "components": files}],
    }
    # END SOLUTION

# %%
try:
    bom = make_bom("athar-small-v1")
except NotImplementedError:
    bom = U.reference("lab_4_3_bom")
U.keep("lab_4_3_bom", bom)
text = json.dumps(bom, indent=1)
(work / "athar-small-v1.cdx.json").write_text(text, encoding="utf-8")
error = validator.validate_str(text)
print(text[:700], "…")
U.ok(error is None, f"the bill of materials validates against CycloneDX 1.7 ({error})")

# %% [markdown]
# ## 2 · Write the admission rules
#
# ✏️ **Exercise** · `admit(name)` returns a log record: the artefact, the decision `admit` or
# `reject`, and one entry per rule with `ok` and a reason. Rules, all of which must pass:
# 1. the signature in `data/models/signatures/<name>.sig` verifies with Rasael's release key
#    (`data/models/release_key.pub`, which the pipeline holds, not the model's source);
# 2. the bill of materials validates and each file hash in it equals the signed digest;
# 3. the licence is on the allow list (`Apache-2.0`, `MIT`);
# 4. no file type that runs code when loaded (`.bin`, `.pt`, `.pkl`, `.pickle`).

# %%
ALLOWED = {"Apache-2.0", "MIT"}
RELEASE_KEY = U.MODELS / "release_key.pub"


def admit(name: str) -> dict:
    # BEGIN SOLUTION
    folder, sig = U.MODELS / name, U.MODELS / "signatures" / f"{name}.sig"
    rules = []
    try:
        model_signing.verifying.Config().use_elliptic_key_verifier(public_key=str(RELEASE_KEY)).verify(folder, sig)
        rules.append({"rule": "signature", "ok": True, "reason": "verified with the release key"})
    except Exception as e:
        rules.append({"rule": "signature", "ok": False, "reason": str(e).split(":")[0][:80]})
    b = make_bom(name)
    signed = {r["name"]: r["digest"] for r in U.dsse_statement(sig)["predicate"]["resources"]}
    in_bom = {c["name"]: c["hashes"][0]["content"] for c in b["components"][0]["components"]}
    valid = validator.validate_str(json.dumps(b)) is None
    same = in_bom == signed
    rules.append({"rule": "bill of materials", "ok": valid and same,
                  "reason": "valid, hashes match the signed digests" if valid and same else
                  ("hashes differ from the signed digests: " + ", ".join(f for f in in_bom if in_bom[f] != signed.get(f)))})
    lic = prov[name]["licence"]
    rules.append({"rule": "licence", "ok": lic in ALLOWED, "reason": f"{lic} {'is' if lic in ALLOWED else 'is not'} on the allow list"})
    risky = [f for f in in_bom if f.endswith((".bin", ".pt", ".pkl", ".pickle"))]
    rules.append({"rule": "file types", "ok": not risky, "reason": "no executable formats" if not risky else ", ".join(risky)})
    return {"artefact": name, "decision": "admit" if all(r["ok"] for r in rules) else "reject", "rules": rules}
    # END SOLUTION

# %% [markdown]
# ## 3 · Run the gate on the three artefacts
#
# The pipeline writes one log line per artefact to `artifacts/lab_4_3/admission.log`.

# %%
try:
    records = [admit(n) for n in ("athar-small-v1", "athar-small-v1-mirror", "athar-tiny-q4")]
except NotImplementedError:
    records = U.reference("lab_4_3_records")
U.keep("lab_4_3_records", records)
with (work / "admission.log").open("w", encoding="utf-8") as f:
    for r in records:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
decisions = {r["artefact"]: r["decision"] for r in records}
print(decisions)
U.ok(decisions == {"athar-small-v1": "admit", "athar-small-v1-mirror": "reject", "athar-tiny-q4": "reject"},
     "the gate admits the valid artefact and rejects the tampered and the unlicensed one")

# %% [markdown]
# ## 4 · Read the logs as the auditor would
#
# An auditor reads the log, not your code. Every rejection must say which rule failed and why.

# %%
rows = [{"artefact": r["artefact"], "decision": r["decision"], "rule": x["rule"], "ok": x["ok"], "reason": x["reason"]}
        for r in records for x in r["rules"]]
log = pd.DataFrame(rows)
print(log.to_string(index=False))
failed = log[~log.ok].groupby("artefact").rule.apply(list).to_dict()
U.ok(failed.get("athar-small-v1-mirror", [])[:1] == ["signature"] and failed.get("athar-tiny-q4") == ["licence"],
     "the mirror fails on its signature and the research model on its licence")

# %% [markdown]
# **Look at** the research model: its signature is valid and its files are intact. Integrity
# is not permission. The licence rule is the one that protects Rasael from shipping a model it
# may not use commercially.
#
# ✱ **Stretch** · Map each rule to `release/kyverno-model-admission.yaml`: which rules does the
# cluster enforce by itself, and which does it trust the gate's annotations for?

# %% [markdown]
# ## Check yourself
#
# 1. Why must the release key come from the pipeline's configuration?
#    <details><summary>Answer</summary>A key shipped with the model can be replaced with the model: the attacker signs the tampered files with their own key.</details>
# 2. The research model verifies. Why is it rejected?
#    <details><summary>Answer</summary>Its licence allows research use only; the gate checks permission as well as integrity.</details>
# 3. What does the bill of materials add to the signature?
#    <details><summary>Answer</summary>A standard, readable record of what the release contains (components, versions, licences, hashes) that other tools and auditors can check.</details>
#
# **Carry forward** · The admission log is the LO5 evidence; the capstone shows the same run in a pipeline.
