from langchain.agents import create_openai_functions_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
# from langchain_core.tools import StructuredTool
from langchain_openai import ChatOpenAI
from pathlib import Path
from .readPricingSheetProd import readPricingSheet1
from workflow_util.case_memory.runtime import get_reference_cases_block

def run_agent(experimentalPlan, model_name="gpt-5.2"):
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
    # tools = [StructuredTool.from_function(tool) for tool in tools]
    
    system_message = Path("/workspace/workflow_data/Agent_1_Plan_Dissector.txt").read_text().replace("{", "{{").replace("}", "}}")

    referenceCases = get_reference_cases_block(experimentalPlan)

    print("\nReference Cases Block for Agent 1:", referenceCases, "\n")
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_message),
        ("user", "{experimentalPlan}\n\n{referenceCases}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    
    agent = create_openai_functions_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
    
    result = agent_executor.invoke({
        "experimentalPlan": experimentalPlan,
        "referenceCases": referenceCases,
    })
    return result["output"]
