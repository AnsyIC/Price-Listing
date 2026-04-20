# Pricing System Workflows

This repository contains the Python implementation of the **Pricing System Production Workflow** used to generate a pricing report (Word + Excel) for a preclinical research service from an experimental plan based on a company pricing catalog.

Note: the previous **Evolution Workflow** has been **deprecated** and moved under `workflow_legacy/` for archival/reference.

## Project Architecture (Production Workflow)

The runnable pipeline lives in `workflow_production/main.py` and follows this sequence:

1) **Trigger / Input Loader**
   - Reads the experimental plan text (currently `workflow_data/Sample_Experiment_Plan.txt`).

2) **Workflow Configuration** (`Production_Workflow_Configuration`)
   - Provides runtime configuration (currently only `notificationEmail`).

3) **Agent 1 — Plan Dissector** (`Agent_1_Plan_Dissector.run_agent`)
   - Service provided: converts the raw experimental plan into structured sections.
   - Uses system prompt: `workflow_data/Agent_1_Plan_Dissector.txt`.
   - Tooling: calls `readPricingSheet1` (catalog search) when it needs to reference known services.
   - Output: JSON string that parses into `{ "sections": [{"header": ..., "content": ...}, ...] }`.

4) **Agent 2 — Pricing Calculator** (`Agent_2_Pricing_Calculator.run_agent`)
   - Service provided: turns dissected sections into a detailed pricing report.
   - Uses system prompt: `workflow_data/Agent_2_Pricing_Calculator.txt`.
   - Inputs:
     - Agent 1 JSON
     - a service-name index generated from the catalog (`workflow_util.service_catalog.catalog.get_service_names_grouped()`)
   - Validation + retries:
     - Each attempt is validated by `workflow_production/validate_pricing_report.py`.
     - If validation fails, Agent 2 is re-run (up to 3 attempts) with error deltas.

5) **Document Generation**
   - `Generate_Word_Document.generate_word`: builds a Word quotation (`quotation.docx`).
   - `Generate_Excel_Document.generate_excel`: builds an Excel breakdown (`pricing_breakdown.xlsx`).

6) **Final Output Packaging** (`Prepare_Final_Output`)
   - Produces a final payload and writes artifacts to `.workflow_dump/`.

### Pricing catalog lookup ("Pricing Sheet")

There is no live Google Sheets integration in the current production workflow. Instead, the “pricing sheet” is represented by a local catalog:

- Source Excel: `workflow_data/KWT报价单.xlsx`
- Generated catalog: `workflow_data/pricing_catalog.json` (+ `workflow_data/pricing_catalog.txt`)
- Runtime search: `workflow_util/service_catalog.py` (fuzzy match via `rapidfuzz` when available)
- Agent tool entrypoint: `workflow_production/readPricingSheetProd.py` (`readPricingSheet1`)

## Directory Tree

```text
.
├── Dockerfile
├── README.md
├── requirements.txt
├── n8nworkflows/
│   ├── Evolution Workflow.json
│   └── Production Workflow.json
├── workflow_data/            # internal company data (not uploaded)
│   ├── Agent_1_Plan_Dissector.txt
│   ├── Agent_2_Pricing_Calculator.txt
│   ├── Sample_Experiment_Plan.txt
│   ├── KWT报价单.xlsx
│   ├── pricing_catalog.json
│   ├── pricing_catalog.txt
│   └── pricing_service_names.txt
├── workflow_production/
│   ├── main.py
│   ├── Production_Workflow_Configuration.py
│   ├── Agent_1_Plan_Dissector.py
│   ├── Agent_2_Pricing_Calculator.py
│   ├── readPricingSheetProd.py
│   ├── validate_pricing_report.py
│   ├── Output_Parser_Plan_Sections.py
│   ├── Output_Parser_Pricing_Report.py
│   ├── Generate_Word_Document.py
│   ├── Generate_Excel_Document.py
│   └── Prepare_Final_Output.py
├── workflow_util/
│   ├── service_catalog.py
│   ├── Data2Catalog.py
│   └── generate_service_names.py
├── workflow_legacy/
│   ├── workflow_evolution/
│   ├── old_Plan_Dissector*.txt
│   └── old_Pricing_Calculator*.txt
├── tests/
│   └── test_pricing_workflow.py
└── .workflow_dump/            # output artifacts (generated)
```

## Setup

1) Install dependencies

```bash
pip install -r requirements.txt
```

2) Configure environment variables

This project uses `python-dotenv`; you can put variables in `.env` or export them in your shell.

- For OpenAI-compatible GPT models:
  - `OPENAI_API_KEY`
- For non-`gpt*` models via DashScope (Aliyun compatible-mode):
  - `DASHSCOPE_API_KEY`

## Usage

### Run the production workflow

Basic:

```bash
python -m workflow_production.main
```

Choose a model:

```bash
python -m workflow_production.main --model gpt-5.2
```

To use a DashScope-hosted model (any model name that does **not** start with `gpt`):

```bash
python -m workflow_production.main --model qwen-plus
```

Outputs:

- Word + Excel files are written to `.workflow_dump/`.

Inputs:

- The default input is `workflow_data/Sample_Experiment_Plan.txt` (edit `workflow_production/main.py` to point to a different plan source).

### Rebuild the pricing catalog from the Excel source

If `workflow_data/KWT报价单.xlsx` changes, regenerate the catalog files:

```bash
python workflow_util/Data2Catalog.py
```

Then regenerate the grouped service-name index:

```bash
python workflow_util/generate_service_names.py
```

## Validation behavior (Agent 2)

`workflow_production/validate_pricing_report.py` enforces a strict policy:

- `isOutsourced = false`: must be computable, math-correct, and (when matched) consistent with the catalog.
- `isOutsourced = true`: subtotal must be `0` (math is not enforced), but if the catalog has a priced match the report should still carry the correct `unitPrice` + `unit`.

Agent 2 will retry up to 3 times if validation fails.

## Case memory (human-verified report retrieval)

To improve "industrial" consistency and reduce reruns, the production workflow can inject a small number of **human-verified reference cases** into Agent 1 and Agent 2 at runtime.

- Source examples: `workflow_data/pricing_reports/*.docx`
- Built casebank: `workflow_data/casebank.jsonl` (JSONL of compact "case cards")

Build / rebuild the casebank:

```bash
python -m workflow_util.case_memory.build_casebank
```

Runtime controls (optional):

- `CASE_MEMORY_ENABLED=1` (default) enables reference-case injection when a casebank exists.
- `CASE_MEMORY_PATH=/workspace/workflow_data/casebank.jsonl` selects a casebank file.
- `CASE_MEMORY_TOP_K=2` controls how many cases are injected per run.
- `CASE_MEMORY_AUTO_BUILD=1` (default off) auto-builds the casebank if missing.

Safety rules: reference cases are used only to copy **structure/sectioning/formula style/uncertainty phrasing** — prices and numeric totals must always come from the current catalog via the pricing tool.

## Legacy

`workflow_legacy/` contains archived prompts and the deprecated evolution workflow implementation. It is not wired into the current production run.
