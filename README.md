# Pricing System Workflows

This repository contains the Python implementation of the Evolution and Production workflows for the Pricing System. It is designed to automate the generation of pricing reports from experimental plans and continuously improve the process based on feedback.

## Project Architecture

The system is divided into two main workflows:

### 1. Evolution Workflow (`workflow_evolution/`)
This workflow is responsible for "learning" and "optimizing" the system. It takes a completed experiment plan and its corresponding manually verified pricing report as input to refine the instructions and data used by the Production Workflow.

*   **Goal:** Optimize instructions and pricing sheets based on feedback.
*   **Trigger:** Receipt of a finalized Experiment Doc and a verified Pricing Report.
*   **Key Components:**
    *   **Agent 1 - Instruction Optimizer:** Analyzes the input documents to update the *Plan Dissector Instructions* and *Pricing Calculator Instructions*. It ensures that the production agents have the most up-to-date logic.
    *   **Agent 2 - Pricing Sheet Optimizer:** Checks the *Pricing Report* against the current *Pricing Sheet*. If new services or price changes are detected, it updates the Pricing Sheet (simulated as Google Sheets updates).
    *   **Notification:** Sends a summary of the changes made to the instructions and pricing sheets.

### 2. Production Workflow (`workflow_production/`)
This is the operational workflow that generates pricing reports for new experimental plans.

*   **Goal:** Generate accurate pricing reports from raw experimental plans.
*   **Trigger:** Receipt of a new Experimental Plan.
*   **Key Components:**
    *   **Agent 1 - Plan Dissector:** Reads the raw *Experimental Plan* and breaks it down into structured sections (e.g., sample preparation, sequencing, analysis) based on the *Plan Dissector Instructions*.
    *   **Agent 2 - Pricing Calculator:** Takes the dissected sections and calculates the cost for each part using the *Pricing Calculator Instructions* and the *Pricing Sheet*.
    *   **Document Generators:**
        *   `Generate_Excel_Document`: Creates a detailed Excel spreadsheet with the pricing breakdown.
        *   `Generate_Word_Document`: Creates a formal Word document for the pricing report.
    *   **Final Output:** Packages the generated documents for delivery.

## Directory Structure

*   `workflow_evolution/`: Contains the Evolution Workflow logic.
    *   `Agent_1_Instruction_Optimizer.py`: Logic for updating instructions.
    *   `Agent_2_Pricing_Sheet_Optimizer.py`: Logic for updating pricing data.
    *   `main.py`: Entry point for the Evolution Workflow.
*   `workflow_production/`: Contains the Production Workflow logic.
    *   `Agent_1_Plan_Dissector.py`: Logic for parsing experimental plans.
    *   `Agent_2_Pricing_Calculator.py`: Logic for calculating prices.
    *   `Generate_*.py`: Modules for creating output files.
    *   `main.py`: Entry point for the Production Workflow.
*   `workflow_data/`: Contains the "brain" of the system - the instructions, prompts, and pricing catalogs used by the agents.
    *   `Agent_1_Plan_Dissector.txt`: System prompt/instructions for the Plan Dissector.
    *   `Agent_2_Pricing_Calculator.txt`: System prompt/instructions for the Pricing Calculator.
    *   `pricing_catalog.json/txt`: The source of truth for pricing.
*   `n8nworkflows/`: Contains JSON exports of n8n workflows, likely used for orchestration or integration.

## Setup

1.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Configure environment variables:**
    Copy `.env.example` to `.env` and fill in your API keys (e.g., OpenAI API Key).
    ```bash
    cp .env.example .env
    ```

## Usage

### Running the Evolution Workflow
Run this when you have a "ground truth" example (Experiment Plan + Verified Report) to improve the system.
```bash
python -m workflow_evolution.main
```
*   **Input:** Configured in `main.py` (currently placeholders).
*   **Output:** Updates to files in `workflow_data/` and a notification.

### Running the Production Workflow
Run this to generate a price quote for a new experiment.
```bash
python -m workflow_production.main
```
*   **Input:** `workflow_data/Sample_Experiment_Plan.txt` (configurable in `main.py`).
*   **Output:** Generated Excel and Word documents in `.workflow_dump/`.

## Notes
*   **LLM Configuration:** The system is configured to use OpenAI models (e.g., `gpt-4o`, `gpt-5.2` in some placeholders). Ensure your API key has access to the required models.
*   **Google Sheets Integration:** The pricing sheet updates in the Evolution Workflow are designed to interact with Google Sheets, but may be using local file simulations or placeholders depending on the specific implementation details in `workflow_util`.
