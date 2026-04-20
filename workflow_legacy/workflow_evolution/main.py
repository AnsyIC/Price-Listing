import sys
import os
from dotenv import load_dotenv
from .Workflow_Configuration import Workflow_Configuration
from .Agent_1_Instruction_Optimizer import run_agent as run_agent_1
from .Agent_2_Pricing_Sheet_Optimizer import run_agent as run_agent_2
from .Output_Parser_Instruction_Update import parse_output as parse_output_1
from .Output_Parser_Pricing_Sheet_Update import parse_output as parse_output_2
from .sendNotification import sendNotification

# Load environment variables
load_dotenv()

def main():
    # 1. Trigger (Simulated)
    # In a real scenario, this would come from a webhook or form submission
    # For now, we can read from files or args
    experiment_doc = "Placeholder Experiment Doc Content"
    report_doc = "Placeholder Report Doc Content"
    
    print("Starting Evolution Workflow...")
    
    # 2. Workflow Configuration
    config_node = Workflow_Configuration()
    config = config_node.run()
    print(f"Configuration loaded: {config}")
    
    # 3. Run Agents in Parallel (Sequentially here for simplicity)
    print("Running Agent 1 - Instruction Optimizer...")
    try:
        agent_1_output_text = run_agent_1(experiment_doc, report_doc)
        agent_1_output = parse_output_1(agent_1_output_text)
        print(f"Agent 1 Output: {agent_1_output}")
    except Exception as e:
        print(f"Agent 1 failed: {e}")
        agent_1_output = {}
    
    print("Running Agent 2 - Pricing Sheet Optimizer...")
    try:
        agent_2_output_text = run_agent_2(experiment_doc, report_doc)
        agent_2_output = parse_output_2(agent_2_output_text)
        print(f"Agent 2 Output: {agent_2_output}")
    except Exception as e:
        print(f"Agent 2 failed: {e}")
        agent_2_output = {}
    
    # 4. Send Notification
    # Construct message
    updated_dissect = "Updated" if agent_1_output.get("updatedDissectingInstructions") == "true" else "No changes"
    updated_pricing_instru = "Updated" if agent_1_output.get("updatedPricingInstructions") == "true" else "No changes"
    updated_pricing_sheet = "Updated" if agent_2_output.get("updatedPricingSheet") == "true" else "No changes"
    
    import datetime
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    message = f"""Updates completed:

Dissecting Instruction Document: {updated_dissect}
Pricing Instruction Document: {updated_pricing_instru}
Pricing Sheet: {updated_pricing_sheet}

Timestamp: {timestamp}"""

    sendNotification(config["notificationEmail"], "Workflow Update Notification - Pricing System", message)
    print("Workflow completed.")

if __name__ == "__main__":
    main()
