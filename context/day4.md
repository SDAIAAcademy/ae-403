---
course: "Reliability Engineering for AI Services"
code: "AE-403"
version: "2027.2.0"
deck: "day4"
day: 4
language: "en"
view: "trainee"
source: "https://sdaiaacademy.github.io/ae-403/slides/day4.html"
---

# Reliability Engineering for AI Services

## Day 4: Integrity and readiness

Model provenance, signatures, bills of materials and production readiness reviews

#### [day4#title] Integrity and readiness

*SDAIA Academy · Reliability Engineering for AI Services*

Day 4: Model provenance, signatures, bills of materials and production readiness reviews

AI Engineering Track · 4 teaching days + capstone day · 4 sessions · 4 labs · AE-403

#### [day4#agenda] Integrity and readiness

*Today*

- **Session 1 · The model supply chain**: A model is files from somewhere; provenance and a hash for every file say which ones
- **Session 2 · Signing and verification**: A signed manifest of hashes binds every file to a signer; verification fails on any change
- **Session 3 · Bills of materials and admission**: A machine learning bill of materials and an admission policy reject unsigned or unlicensed models
- **Session 4 · Production readiness reviews**: A readiness review ranks findings by risk and sets launch conditions the owner can meet

#### [day4#review-day3] Which action closes INC-0731's biggest gap?

*Review of Day 3*

**Question:** INC-0731's review lists five contributing factors. Which corrective action would have stopped v2.4 before it reached all Arabic users?

- A. Remind release engineers to test Arabic carefully
- B. Shorten the alert's long window to 30 minutes
- C. Fix the digit normalisation in the prompt template
- D. Route every model release through a canary with a per-language quality gate

### Session 1: The model supply chain

#### [day4#s1] The model supply chain

*Session 1*

- Trace a model artefact to its source and revision
- Hash every file and compare with the publisher's list
- Name where tampering hides in a model folder

#### [day4#model-is-files] A model is a folder of files from somewhere

*The model supply chain*

1. **Publisher** trains and releases
2. **Hub or mirror** stores and serves copies
3. **Your registry** what the pipeline pulls
4. **Engine** loads it for users

Each hop is a place where a file can be swapped: weights, tokenizer, configuration, even the licence.

#### [day4#what-can-change] Every file in the folder changes behaviour, not only the weights

*Where tampering hides*

- **Weights.** A changed shard plants a behaviour that only some inputs trigger.
- **Tokenizer and config.** A changed vocabulary or setting silently changes every answer.
- **Loadable code.** Pickled formats can run code when loaded; safetensors stores tensors only.

#### [day4#provenance-record] Three candidate fallback models, three provenance records

*Lab 4.1 · provenance*

| Artefact | Publisher | Obtained from | Licence |
| --- | --- | --- | --- |
| `athar-small-v1` | Rasael ML platform team | the publisher | Apache-2.0 |
| `athar-small-v1-mirror` | Rasael ML platform team | a third-party mirror | Apache-2.0 |
| `athar-tiny-q4` | an external research group | the publisher | research use only |

#### [day4#hash-finding] One shard of the mirrored copy is not what the publisher released

*Lab 4.1 · the finding*

```
# file: Lab 4.1 finding
artefact   athar-small-v1-mirror
file       model-00002-of-00002.safetensors
expected   be1f25b1cc7b4c31...
found      eff1f6fb22ae544a...
decision   do not admit; obtain from the publisher and verify its signature
```

64 bytes of 24,576 differ. A hash proves the bytes differ, not who changed them or why.

#### [day4#hash-list-limit] A hash list from the same place as the files proves nothing

*What goes wrong*

- Whoever can change a shard on a mirror can change the list beside it
- The list must be signed by the publisher, and the key must reach you another way
- Then a change to any file, or to the list, fails verification

#### [day4#check-hash] The hashes match; is the model safe to admit?

*Checkpoint*

**Question:** Every file of a downloaded model matches the hash list published on the same mirror. What can you conclude?

- A. The files are the publisher's originals
- B. The files match that list, and nothing more until the list is verified
- C. The model may be used commercially
- D. The model will answer as well as the original

#### [day4#lab-4-1] Provenance and the tampered file

Lab 4.1 · 25 min

Trace the provenance of three model artefacts and find the tampered file by its hash.

[D4_1_provenance.ipynb](https://sdaiaacademy.github.io/ae-403/labs/D4_1_provenance.ipynb)

- [ ] Read the three provenance records (5 min)
- [ ] Hash every file of each artefact (6 min)
- [ ] Compare with the publisher's list (7 min)
- [ ] Write the finding for the release engineer (7 min)
- [ ] ✱ Stretch: Find which file types can run code when loaded

### Session 2: Signing and verification

#### [day4#s2] Signing and verification

*Session 2*

- Sign a model folder as a manifest of hashed files
- Verify the signature at admission
- Explain what a signature proves and what it does not

#### [day4#signed-manifest] Sign a manifest of every file's hash, not one archive

*Model signing*

1. **Hash** every file in the folder
2. **Statement** an in-toto list of files and digests
3. **Sign** in a DSSE envelope
4. **Bundle** a Sigstore bundle beside the model

#### [day4#key-or-keyless] Sign with a key you guard, or keylessly with an identity

*Two ways to sign*

- **A key.** An elliptic-curve key pair. Verification needs the public key from a trusted channel. The lab uses this: no account, no network.
- **Keyless (Sigstore).** A short-lived certificate for a sign-in identity, recorded in a public transparency log. Verification names the identity and its provider.

#### [day4#sign-code] Three lines sign; three lines verify

*Lab 4.2*

```
# file: Lab 4.2
model_signing.signing.Config().use_elliptic_key_signer(
    private_key="key.priv").sign(model, "model.sig")

model_signing.verifying.Config().use_elliptic_key_verifier(
    public_key="key.pub").verify(model, "model.sig")   # raises on failure
```

#### [day4#verify-results] Change one character, or use another key, and verification fails

*Lab 4.2 · results*

| Check | Result |
| --- | --- |
| signed folder, signer's public key | verified |
| `tokenizer.json` with one number changed | signature mismatch: hash mismatch for tokenizer.json |
| original folder, a different public key | key mismatch |

#### [day4#what-signature-proves] A signature proves who signed which bytes, nothing more

*Limits*

- **Proves:** every file is what the key holder signed
- **Does not prove:** that the model is good, safe or free of planted behaviour
- **Does not prove:** that you may use it: licences are a separate rule

- **Where the key comes from.** The pipeline holds the trusted public key. A key shipped beside the model can be replaced with the model.

#### [day4#check-signature] The signature verifies

*Checkpoint*

**Question:** A model folder and its signature bundle both came from a partner's file share, along with the public key to check them. The signature verifies. What has been shown?

- A. The partner released these exact files
- B. The model contains no planted behaviour
- C. Only that the files match whoever holds that key, which could be anyone with access to the share
- D. Rasael may deploy it in production

#### [day4#lab-4-2] Sign and verify a model folder

Lab 4.2 · 25 min

Sign a manifest of model files with a key, verify it, and show that a changed file fails verification.

[D4_2_signing.ipynb](https://sdaiaacademy.github.io/ae-403/labs/D4_2_signing.ipynb)

- [ ] Generate a key pair (3 min)
- [ ] Sign the model folder (6 min)
- [ ] Read the signed statement (5 min)
- [ ] Verify, change one file, verify again (7 min)
- [ ] Verify against the wrong key (4 min)
- [ ] ✱ Stretch: Sign only the files the engine loads and say what that leaves out

### Session 3: Bills of materials and admission

#### [day4#s3] Bills of materials and admission

*Session 3*

- Write a CycloneDX ML-BOM for a model
- Write an admission policy with logged reasons
- Run the gate on valid, tampered and unlicensed artefacts

#### [day4#ml-bom] A machine learning bill of materials says what the release contains

*Bills of materials*

```
# file: athar-small-v1.cdx.json (Lab 4.3)
"components": [{
  "type": "machine-learning-model", "name": "athar-small-v1",
  "publisher": "Rasael ML platform team",
  "licenses": [{"license": {"id": "Apache-2.0"}}],
  "modelCard": {"modelParameters": {"task": "text-generation"}},
  "components": [{"type": "file", "name": "model-00001-of-00002.safetensors",
                  "hashes": [{"alg": "SHA-256", "content": "750bb039..."}]}]
}]
```

#### [day4#admission-rules] Four rules, all of which must pass, each logged with its reason

*The admission gate*

1. The signature verifies with the release key the pipeline holds
2. The bill of materials validates, and its hashes equal the signed digests
3. The licence is on the allow list (Apache-2.0, MIT)
4. No file format that runs code when loaded

#### [day4#gate-run] The gate admits one artefact and rejects two, for different reasons

*Lab 4.3 · the pipeline run*

| Artefact | Signature | BOM | Licence | Decision |
| --- | --- | --- | --- | --- |
| athar-small-v1 | verified | matches | Apache-2.0 | admit |
| athar-small-v1-mirror | mismatch | shard 2 differs | Apache-2.0 | reject |
| athar-tiny-q4 | verified | matches | research only | reject |

#### [day4#cluster-admission] The cluster refuses any pod the gate did not admit

*In the cluster*

```
# file: release/kyverno-model-admission.yaml
validate:
  failureAction: Enforce
  pattern:
    metadata:
      annotations:
        models.rasael.example/signature: "verified"
        models.rasael.example/licence: "Apache-2.0 | MIT"
```

#### [day4#classification-note] The model's records are classified data too

*Data governance*

- Admission logs and BOMs name suppliers, versions and keys: classify them before sharing
- Telemetry with answers can hold personal data: it inherits the answers' classification
- Where the release key and the model store live is a cloud control to review

#### [day4#check-admission] Which artefact does the gate admit?

*Checkpoint*

**Question:** Four candidate models for the fallback mode. Rasael's allow list is Apache-2.0 and MIT. Which one passes all four rules?

- A. Apache-2.0, signature mismatch on one shard
- B. Research-only licence, signature verified
- C. MIT, signature verified, safetensors files, BOM hashes match
- D. Apache-2.0, signature verified, weights in a pickled .bin file

#### [day4#lab-4-3] Bill of materials and admission gate

Lab 4.3 · 25 min

Write a bill of materials for the valid artefact and a policy that rejects unsigned, tampered or unlicensed models, then run the gate on all three with logs.

[D4_3_bom_admission.ipynb](https://sdaiaacademy.github.io/ae-403/labs/D4_3_bom_admission.ipynb)

- [ ] Write the ML-BOM and validate it (8 min)
- [ ] Write the admission rules (7 min)
- [ ] Run the gate on the three artefacts (6 min)
- [ ] Read the logs as the auditor would (4 min)
- [ ] ✱ Stretch: Map each rule to the supplied Kyverno policy

### Session 4: Production readiness reviews

#### [day4#s4] Production readiness reviews

*Session 4*

- Apply a readiness checklist to another team's evidence
- Rank findings by likelihood and impact
- Set a launch decision with dated conditions

#### [day4#readiness-review] A readiness review decides whether another team's service may launch

*Readiness reviews*

- **Evidence.** Measured results, not claims: curves, logs, replays, drills.
- **Ranking.** Findings ordered by risk to users and to the organisation.
- **Decision.** Launch, launch with dated conditions, or not yet, and what would change it.

#### [day4#checklist-areas] Thirteen items in six areas: this week, as questions

*The checklist*

| Area | The question |
| --- | --- |
| Objectives | Per language, with burn-rate alerts? |
| Capacity | Load-tested to the busiest hour, with admission limits? |
| Degradation | Modes tested under faults, and disclosed? |
| Incidents | Roles, a decision log, the breach procedure? |
| Release | A canary with a quality gate; a tested rollback? |
| Integrity | A verified signature and a bill of materials? |

#### [day4#read-the-claim] Read every claim: "met" is the team's word, not the review's

*Lab 4.4 · Taqdir*

**Taqdir team:** Objectives for availability and first-token time: **met**. 95% under 2 s to first token.

**Reviewer:** Rasael's standard is 1.5 s. Partial.

#### [day4#ranked-findings] Risk = likelihood × impact × gap; the top three decide the review

*Lab 4.4 · ranked*

| Finding | Status | Risk |
| --- | --- | --- |
| Load test only at the average hour (2.1 a second; the busiest was 6.4) | missing | 16 |
| Weights from a third-party mirror, unsigned | missing | 15 |
| Quality objective on English samples only | partial | 10 |
| Runbook without roles or a decision log | missing | 9 |
| Quality alert on a daily average | partial | 8 |

#### [day4#launch-decision] Not yet: an unsigned model blocks the launch

*The decision*

- **Blocking.** Missing with impact 5: the model signature. Nobody can show the weights are the publisher's, and Lab 4.1 found a tampered mirror.
- **Conditions.** Busiest-hour load test and per-language quality within 14 days; runbook and quality alerts within 30, each with its proof.

#### [day4#capstone-kickoff] Your capstone is this review, on a real or supplied service, with measured evidence

*The capstone*

- A peer's service, or the supplied Athar v2.7 release pack (`labs/capstone/`)
- Objectives, capacity, degradation, an incident drill, release integrity, a decision
- A public GitHub repository; a 10-minute defence with 5 minutes of panel questions
- During the questions, the panel injects a fault and you diagnose it live

#### [day4#check-launch] Which launch decision?

*Checkpoint*

**Question:** A service has every item met except two partial ones: its canary gates on latency only, and its fallback was never tested under a provider failure. Both have likelihood 4 and impact 4, so each scores a risk of 8. What do you decide under Rasael's rule?

- A. Do not launch until both are fixed
- B. Launch with two dated conditions, each with the evidence that proves it
- C. Launch without conditions
- D. Ask the team to rerun their own checklist

#### [day4#lab-4-4] Readiness review of Taqdir

Lab 4.4 · 25 min

Apply the readiness checklist to Taqdir, the cross-border team's delivery-estimate assistant, and rank the findings by risk.

[D4_4_readiness_review.ipynb](https://sdaiaacademy.github.io/ae-403/labs/D4_4_readiness_review.ipynb)

- [ ] Read the checklist and the evidence pack (5 min)
- [ ] Score each item from the evidence (7 min)
- [ ] Rank the findings by risk (6 min)
- [ ] Launch decision and conditions (7 min)
- [ ] ✱ Stretch: Choose the capstone service and the first three items you will test

#### [day4#wrap-up] Three things to keep

*Day 4 · wrap-up*

- **Hash what you received.** Against a list you can trust.
- **Verify before admission.** Signature, bill of materials, licence, format: all logged.
- **Review by risk.** Evidence over claims; a decision with dated, provable conditions.

#### [day4#next] Capstone day: the readiness review before the panel

*Next*

- Bring your repository, its logs and a running service (or the simulator) for the live fault
- The supervised exit check, without AI, runs before the defences
