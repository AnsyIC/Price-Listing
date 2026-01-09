import sys
import os
import base64
import argparse
from dotenv import load_dotenv
from .Production_Workflow_Configuration import Production_Workflow_Configuration
from .Agent_1_Plan_Dissector import run_agent as run_agent_1
from .Agent_2_Pricing_Calculator import run_agent as run_agent_2
from .Output_Parser_Plan_Sections import parse_output as parse_output_1
from .Output_Parser_Pricing_Report import parse_output as parse_output_2
from .Generate_Excel_Document import generate_excel
from .Generate_Word_Document import generate_word
from .Prepare_Final_Output import Prepare_Final_Output
from pathlib import Path

# Load environment variables
load_dotenv()

def main(model_name="gpt-5.2"):
    # 1. Trigger (Simulated)
    experimental_plan = Path("/workspace/workflow_data/Sample_Experiment_Plan.txt").read_text()
    
    print(f"Starting Production Workflow with model: {model_name}...")
    
    # 2. Workflow Configuration
    config_node = Production_Workflow_Configuration()
    config = config_node.run()
    print(f"Configuration loaded: {config}")
    
    # 3. Agent 1 - Plan Dissector
    print("Running Agent 1 - Plan Dissector...")
    try:
        agent_1_output_text = run_agent_1(experimental_plan, model_name=model_name)
        agent_1_output = parse_output_1(agent_1_output_text)
        print(f"Agent 1 Output: {agent_1_output}")
    except Exception as e:
        print(f"Agent 1 failed: {e}")
        return

    # 4. Agent 2 - Pricing Calculator
    print("Running Agent 2 - Pricing Calculator...")
    try:
        # Agent 2 takes the JSON output of Agent 1
        agent_2_output_text = run_agent_2(agent_1_output, model_name=model_name)
        agent_2_output = parse_output_2(agent_2_output_text)
        print(f"Agent 2 Output: {agent_2_output}")
    except Exception as e:
        print(f"Agent 2 failed: {e}")
        return

    # 5. Generate Documents
    print("Generating Documents...")
    try:
        excel_doc = generate_excel(agent_2_output)
        word_doc = generate_word(agent_1_output['sections'], agent_2_output, model_name=model_name)
        print("Documents generated.")
    except Exception as e:
        print(f"Document generation failed: {e}")
        return

    # 6. Prepare Final Output
    final_output_node = Prepare_Final_Output()
    final_output = final_output_node.run(word_doc, excel_doc)
    
    print("Workflow completed successfully.")
    print(f"Final Status: {final_output['status']}")
    
    # Save files to .workflow_dump
    output_dir = Path("/workspace/.workflow_dump")
    output_dir.mkdir(exist_ok=True)

    # Save Word Document
    word_path = output_dir / final_output['wordDocument']['filename']
    with open(word_path, 'wb') as f:
        f.write(final_output['wordDocument']['data'])
    print(f"Saved Word document to {word_path}")

    # Save Excel Document
    excel_path = output_dir / final_output['excelDocument']['filename']
    with open(excel_path, 'wb') as f:
        f.write(base64.b64decode(final_output['excelDocument']['data']))
    print(f"Saved Excel document to {excel_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Production Workflow")
    parser.add_argument("--model", type=str, default="gpt-5.2", help="LLM model name to use (e.g. gpt-5.2, qwen-plus)")
    args = parser.parse_args()
    main(model_name=args.model)
