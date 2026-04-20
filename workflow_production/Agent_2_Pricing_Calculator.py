import sys
import os
import json
from pathlib import Path
from langchain.agents import create_openai_tools_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI

# Ensure imports work
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from workflow_production.readPricingSheetProd import readPricingSheet1
from workflow_production.validate_pricing_report import validate_pricing_report
from workflow_util.service_catalog import catalog
from workflow_util.case_memory.runtime import get_reference_cases_block

def run_agent(dissectedPlanJson: str, model_name="gpt-5.2"):
    if model_name.startswith("gpt"):
        llm = ChatOpenAI(model=model_name, temperature=0)
    else:
        # Use DashScope for other models as requested
        import os
        api_key = os.environ.get("DASHSCOPE_API_KEY")
        llm = ChatOpenAI(
            model=model_name, 
            temperature=0,
            api_key=api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
    tools = [readPricingSheet1]

    system_message_content = Path("/workspace/workflow_data/Agent_2_Pricing_Calculator.txt").read_text()
    pricingServiceNames = catalog.get_service_names_grouped()

    referenceCases = get_reference_cases_block(
        dissectedPlanJson if isinstance(dissectedPlanJson, str) else json.dumps(dissectedPlanJson, ensure_ascii=False)
    )
    
    print("\nReference Cases Block for Agent 2:", referenceCases, "\n")

    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content=system_message_content),
        ("user",
         "实验文本拆解JSON: {dissectedPlanJson}\n\n"
         "报价单服务索引:\n{pricingServiceNames}\n\n"
         "{referenceCases}\n\n"
         "{delta_instructions}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    agent = create_openai_tools_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

    max_attempts = 3
    delta_instructions = ""
    last_output = ""

    for attempt in range(max_attempts):
        result = agent_executor.invoke({
            "dissectedPlanJson": dissectedPlanJson,
            "pricingServiceNames": pricingServiceNames,
            "referenceCases": referenceCases,
            "delta_instructions": delta_instructions,
        })

        output = result["output"]
        last_output = output

        # Validate
        # Ensure dissectedPlanJson is passed in a format validate_pricing_report accepts (it now accepts dict or str)
        # output from agent is likely a string (JSON), but if parsed it might be a dict.
        
        errors, retry_delta, hints = validate_pricing_report(
            dissectedPlanJson, 
            output, 
            lambda q, k=1: catalog.search(q, top_k=k)
        )

        if not errors:
            return output

        delta_instructions = (
            "\n\nPrevious attempt had errors. Please fix:\n"
            f"{retry_delta}\n\nPrevious Output JSON:\n{last_output}"
        )

        print("Agent 2 errors detected, retrying with error:", errors)

    raise Exception(f"Failed after {max_attempts} attempts. Last errors:\n{errors}")
