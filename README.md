# LLM-Project — From Natural Language to Linear Programs (NER → BART)

Turn plain natural-language optimization problems into structured linear‑program (LP) formulations with a two‑stage pipeline:

1. **Named Entity Recognition (XLM‑RoBERTa)** to tag key entities in the text (variables, numbers, limits, comparators, etc.)
2. **Sequence‑to‑Sequence generation (BART‑base)** to produce the objective and constraints of the LP from the tagged text

> Dataset: NL4Opt. NER uses **CoNLL** format; the generation stage trains on paired **JSONL** (tagged input → LP target).

---

## Overview

The repository bridges the gap from optimization statements in everyday English to standard LPs.

It uses a two-stage pipeline: an **XLM-RoBERTa NER model** first labels variables, quantities, bounds, and comparators; a **BART seq2seq model** then generates from the labeled text a standard LP (objective + constraints) format. Trained on **NL4Opt-style** data (CoNLL for NER, JSONL for gen), its goal is simple: accept as input a concise problem statement and return as output an LP that can be solved.

Preliminary results show decent recall on numeric values and inequality direction, with errors being predominantly in variable names and sometimes misplaced/swapped terms. This pointed out future directions, like standardised variable schemes, structure-aware losses, and a Lightweight LP validator.

The repository has clean data layout, reproducible notebooks for training, and end-to-end inference demo.

This repository demonstrates an end‑to‑end workflow that:

* Learns to recognize optimization entities from natural language (NER)
* Converts NER outputs into a simpler, **BART‑ready** representation (inline tags)
* Fine‑tunes **BART** to generate the final LP text with `max:` / `st:` sections and inequalities
* Evaluates both stages with appropriate metrics

**High‑level flow**

```
Natural‑language problem
       │
       ▼
NER (XLM‑RoBERTa) → CoNLL tags
       │
       ▼
Conversion to BART‑ready JSONL (inline tags)
       │
       ▼
BART‑base fine‑tune → LP text (objective + constraints)
```

---

## Repository Structure

```
LLM-Project/
├─ NER/                 # NER training/eval notebooks & helpers (XLM-RoBERTa)
├─ BART/                # BART training/eval/inference notebooks
├─ fine_tuned_bart/     # saved checkpoints / runs
├─ DATA/                # raw/processed data
├─ .gitignore
├─ .gitattributes
└─ README.md
```
---

## Quick Start

### 1) Environment

```bash
# Python 3.10+ recommended
python -m venv .venv
source .venv/bin/activate  # (Windows: .venv\Scripts\activate)
pip install -r requirements.txt
# or, if you don’t have one yet:
pip install torch transformers datasets sacrebleu rouge-score seqeval pandas numpy jupyter
```

### 2) Data Layout (suggested)

```
DATA/
├─ nl4opt/
│  ├─ ner_train.conll
│  ├─ ner_dev.conll
│  ├─ ner_test.conll
│  ├─ pairs_train.jsonl        # (NL ↔ LP targets)
│  ├─ pairs_dev.jsonl
│  └─ pairs_test.jsonl
└─ bart_ready/
   ├─ train.jsonl
   ├─ dev.jsonl
   └─ test.jsonl
```

**NER input**: CoNLL (one token per line with BIO tags; blank line separates sentences).
**BART input**: JSONL with fields such as:

```json
{
  "input": "A store sells <VAR>mango</VAR> and <VAR>peach</VAR> drinks ... at most <NUM>788</NUM> total ...",
  "target": "max: 3*mango + 1*peach\nst:\n  mango >= 53\n  peach >= 89\n  mango <= 560\n  peach <= 64\n  mango + peach <= 788"
}
```

Generate `bart_ready/*.jsonl` using the **conversion step** described below.

---

## Step 1 — NER (XLM‑RoBERTa)

Goal: tag entities like variables, numbers/limits, comparators, units, etc., using CoNLL‑formatted NL4Opt data.

**How to run**

* Open the NER notebook(s) under `NER/` and train XLM‑RoBERTa on the CoNLL files (train/dev)
* Save predictions on dev/test back in CoNLL format

**Evaluate**

* Report token‑level and entity‑level **precision/recall/F1** (CoNLL‑style)
* Save a small table to `results/ner_results.md`

---

## Bridge — Convert CoNLL → BART‑ready JSONL

Goal: reassemble tokens into sentences and **inline‑tag** the recognized entities (e.g., `<VAR>`, `<NUM>`, etc.), pairing each tagged NL input with its ground‑truth LP target to form **JSONL** records for BART.

**Deliverable**

* A notebook/script that:

  1. Reads predicted CoNLL
  2. Reconstructs sentences
  3. Injects inline tags
  4. Pairs with target LP strings
  5. Writes `DATA/bart_ready/{train,dev,test}.jsonl`

Why this helps:

* The original multi‑field format can be verbose; a **single input ↔ single output** per sample makes seq2seq training simpler and more robust.

---

## Step 2 — Sequence Generation (BART‑base)

Goal: generate the LP **objective** and **constraints** from the tagged NL inputs.

**How to run**

* Open the notebook(s) under `BART/`, point to `DATA/bart_ready/*.jsonl`, and fine‑tune **BART‑base**
* Useful knobs: `max_source_len`, `max_target_len`, `learning_rate`, `batch_size`, `num_train_epochs`, `label_smoothing_factor`, `warmup_steps`

**Evaluate**

* Text metrics: **ROUGE‑L**, **BLEU**
* Task metric: **LP correctness** (exact extraction of coefficients, variables, comparators, and bounds)
* Save to `results/bart_results.md`

---

## Inference Demo

Example NL prompt:

> “A bubble tea store sells peach and mango drinks… at most 788 total… at least 53 mango and 89 peach… at most 560 mango and 64 peach… profits \$3 and \$1… maximize profit.”

Expected output sketch:

```
max: 3*mango + 1*peach
st:
  mango >= 53
  peach >= 89
  mango <= 560
  peach <= 64
  mango + peach <= 788
```

---

## Current Status

* Trained on the provided dataset; also experimented with additional **synthetic samples** to increase diversity.
* In qualitative tests, **most numbers and inequality directions** are learned correctly; errors often involve variable names, occasional swaps, or missing terms.

---

## Known Limitations

* **Pretraining bias**: when uncertain, BART may drift to familiar but irrelevant words from general‑domain pretraining
* **Limited fine‑tuning data**: relatively small dataset constrains generalization
* **Unfamiliar output format**: LP syntax (e.g., `max:`, `st:`, inequalities) differs from natural language
* **Tagging/vocabulary inconsistency**: mismatches like `peach_drink` vs `peach` can confuse mapping

---

## Roadmap

* Standardize tags & variable naming between NER and BART
* Add **task‑aware losses** or structure constraints; encourage copying numbers/variables from input
* Expand data with templated/counterfactual examples to cover edge cases
* Post‑process with a grammar checker or LP validator to auto‑fix or reject malformed outputs
* Report **exact‑match of all constraints** and **feasibility checks** via a simple LP parser/solver

---

## Citations & Acknowledgments

* NL4Opt organizers and dataset
* Hugging Face Transformers & Datasets
* PyTorch community

 
