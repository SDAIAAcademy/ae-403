"""Sign the supplied model artefacts with a one-time release key (run once by the course author).

    uv run python _tools/sign_artifacts.py

Writes data/models/signatures/<artefact>.sig and data/models/release_key.pub. The private key is
created in memory and thrown away, so nobody can sign again with it. The mirror carries the
publisher's signature of the original files: its changed shard must then fail verification.
"""
import shutil
import tempfile
from pathlib import Path

import model_signing
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec

LABS = Path(__file__).resolve().parents[1]
MODELS = LABS / "data" / "models"
SIGS = MODELS / "signatures"
SIGS.mkdir(exist_ok=True)

with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)
    key = ec.generate_private_key(ec.SECP256R1())
    (tmp / "key.priv").write_bytes(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                                                    serialization.NoEncryption()))
    (MODELS / "release_key.pub").write_bytes(key.public_key().public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo))
    cfg = model_signing.signing.Config().use_elliptic_key_signer(private_key=str(tmp / "key.priv"))
    for name in ("athar-small-v1", "athar-tiny-q4"):
        cfg.sign(MODELS / name, SIGS / f"{name}.sig")
    shutil.copy(SIGS / "athar-small-v1.sig", SIGS / "athar-small-v1-mirror.sig")
print("signed:", sorted(p.name for p in SIGS.iterdir()))
