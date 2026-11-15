# %% [markdown]
# # Setup check
#
# Run this notebook once before Day 1, in Google Colab or on your laptop. It imports every
# library the labs use, reads one data file per day and runs the engine simulator once. Nothing
# downloads a model and no key is needed. Every line should print ✅.

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

# %%
import importlib
for mod in ["numpy", "pandas", "matplotlib", "yaml", "cryptography", "model_signing", "cyclonedx"]:
    try:
        importlib.import_module(mod)
        print("✅", mod)
    except Exception as e:
        print("❌", mod, type(e).__name__, e)

# %%
import relia as U
print("✅ relia, quick mode:", U.QUICK)
for name in ["telemetry_week", "overload_trace", "replay_day", "taqdir_checklist"]:
    df = U.load(name)
    print("✅", name, len(df), "rows")
print("✅ model artefacts:", sorted(p.name for p in U.MODELS.iterdir() if p.is_dir()))

# %%
run = U.Engine().closed_loop(8, duration_s=30, warmup_s=5)
U.ok(len(run) > 20, f"engine simulator: {len(run)} requests at 8 concurrent, goodput {U.goodput(run, 25)} a second")
answer, source = U.live_answer("What is the fee for a domestic parcel in Riyadh?", recorded="(recorded answer)")
print("✅ answers come from:", source, "(set OPENROUTER_API_KEY to try a free hosted model; the labs do not need it)")
