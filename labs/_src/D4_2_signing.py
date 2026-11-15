# %% [markdown]
# @header
#
# AI policy: AI-tutor. An assistant may explain the signature bundle; key handling decisions are yours.

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
import shutil
import model_signing
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec

# %% [markdown]
# ## 1 · Generate a key pair
#
# OpenSSF Model Signing (the `model_signing` package) signs a model folder as a manifest of
# hashed files. It can sign keylessly through Sigstore (an identity from a sign-in, recorded in a
# public transparency log) or with a key you hold. The lab uses a key: no account, no network.
#
# ✏️ **Exercise** · Create an elliptic-curve P-256 key pair and write `key.priv` and `key.pub`
# (PEM) into the lab's work folder. Never commit a private key: it lives in `artifacts/`, which the
# course's `.gitignore` excludes; the cell below checks that git really ignores it.

# %%
work = U.workdir("lab_4_2")
model = work / "athar-small-v1"
shutil.copytree(U.MODELS / "athar-small-v1", model)


def make_keys(folder: Path):
    # BEGIN SOLUTION
    key = ec.generate_private_key(ec.SECP256R1())
    (folder / "key.priv").write_bytes(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                                                        serialization.NoEncryption()))
    (folder / "key.pub").write_bytes(key.public_key().public_bytes(serialization.Encoding.PEM,
                                                                   serialization.PublicFormat.SubjectPublicKeyInfo))
    return folder / "key.priv", folder / "key.pub"
    # END SOLUTION

# %%
try:
    priv, pub = make_keys(work)
    own_key = True
except NotImplementedError:
    priv, pub, own_key = None, U.MODELS / "release_key.pub", False
print("public key:", pub.name, "· own key:", own_key)
ignored = subprocess.run(["git", "check-ignore", "-q", str(work / "key.priv")], cwd=U.LABS).returncode == 0
print("git ignores the private key:", ignored)

# %% [markdown]
# ## 2 · Sign the model folder
#
# ✏️ **Exercise** · Sign `model` with your private key into `work / "model.sig"`:
# `model_signing.signing.Config().use_elliptic_key_signer(private_key=...).sign(model, sig)`.

# %%
sig = work / "model.sig"


def sign(model: Path, priv: Path, sig: Path):
    # BEGIN SOLUTION
    model_signing.signing.Config().use_elliptic_key_signer(private_key=str(priv)).sign(model, sig)
    # END SOLUTION

# %%
try:
    sign(model, priv, sig)
except (NotImplementedError, TypeError):
    shutil.copy(U.MODELS / "signatures" / "athar-small-v1.sig", sig)   # the publisher's signature, with release_key.pub
print("signature bundle:", sig.stat().st_size, "bytes")

# %% [markdown]
# ## 3 · Read the signed statement
#
# The bundle carries an in-toto statement inside a DSSE envelope: the statement is what was
# signed. ✏️ **Exercise** · Return the predicate type and a dictionary file → digest from the
# statement's `predicate.resources`.

# %%
def signed_files(sig: Path) -> tuple[str, dict]:
    # BEGIN SOLUTION
    st = U.dsse_statement(sig)
    return st["predicateType"], {r["name"]: r["digest"] for r in st["predicate"]["resources"]}
    # END SOLUTION

# %%
try:
    ptype, files = signed_files(sig)
except NotImplementedError:
    st = U.dsse_statement(sig)
    ptype, files = st["predicateType"], {r["name"]: r["digest"] for r in st["predicate"]["resources"]}
print(ptype)
for f, d in files.items():
    print(f"  {f:36s} {d[:16]}…")
U.ok(all(files[f] == U.sha256_file(model / f) for f in files), "every file's digest in the statement matches the file")

# %% [markdown]
# ## 4 · Verify, change one file, verify again
#
# ✏️ **Exercise** · Write `verify(model, sig, pub)` that returns `(True, "")` or `(False, reason)`
# (`model_signing.verifying.Config().use_elliptic_key_verifier(public_key=...).verify(model, sig)`
# raises on failure). Verify, change one byte of the tokenizer, verify again.

# %%
def verify(model: Path, sig: Path, pub: Path) -> tuple[bool, str]:
    # BEGIN SOLUTION
    try:
        model_signing.verifying.Config().use_elliptic_key_verifier(public_key=str(pub)).verify(model, sig)
        return True, ""
    except Exception as e:
        return False, str(e)[:160]
    # END SOLUTION

# %%
def verify_safe(*a):
    try:
        return verify(*a)
    except NotImplementedError:
        try:
            model_signing.verifying.Config().use_elliptic_key_verifier(public_key=str(a[2])).verify(a[0], a[1])
            return True, ""
        except Exception as e:
            return False, str(e)[:160]

before = verify_safe(model, sig, pub)
tok = model / "tokenizer.json"
tok.write_text(tok.read_text(encoding="utf-8").replace("32000", "32001"), encoding="utf-8", newline="\n")
after = verify_safe(model, sig, pub)
print("before:", before)
print("after: ", after)
U.ok(before[0] and not after[0], "the signature verifies, and fails once one file changes")

# %% [markdown]
# ## 5 · Verify against the wrong key
#
# Restore the file, then verify with a key that did not sign: Rasael's release key if you signed
# with your own, or a fresh key otherwise.

# %%
shutil.copy(U.MODELS / "athar-small-v1" / "tokenizer.json", tok)
other = work / "other"
other.mkdir()
k = ec.generate_private_key(ec.SECP256R1())
(other / "key.pub").write_bytes(k.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo))
right, wrong = verify_safe(model, sig, pub), verify_safe(model, sig, other / "key.pub")
print("right key:", right)
print("wrong key:", wrong)
U.ok(right[0] and not wrong[0], "only the signer's public key verifies")

# %% [markdown]
# **Look at** what verification proved: these files are the ones the holder of the key signed.
# Not that the model is good, safe or licensed for your use, and not who holds the key: that is
# key management, or an identity with Sigstore's keyless signing.
#
# ✱ **Stretch** · Sign only the files the engine loads (`ignore_paths` in the signing
# configuration) and say what that leaves out.

# %% [markdown]
# ## Check yourself
#
# 1. What does a valid signature over a model folder prove?
#    <details><summary>Answer</summary>That every file is byte for byte what the key holder signed; nothing about quality, safety or licence.</details>
# 2. Why sign a manifest of file hashes rather than one archive?
#    <details><summary>Answer</summary>Models are many large files; a manifest lets each file be hashed separately, in parallel, and names the file that changed.</details>
# 3. Where must the public key used at admission come from?
#    <details><summary>Answer</summary>From a trusted channel configured in the pipeline, never from the same place as the model and its signature.</details>
#
# **Carry forward** · Lab 4.3's gate verifies the supplied signatures with `data/models/release_key.pub`.
