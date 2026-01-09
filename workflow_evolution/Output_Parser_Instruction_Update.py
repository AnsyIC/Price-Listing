import json
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field

class InstructionUpdateOutput(BaseModel):
    updatedDissectingInstructions: str = Field(description="true or false")
    updatedPricingInstructions: str = Field(description="true or false")
    error: str = Field(description="Error message if any")

def parse_output(output_text: str):
    parser = JsonOutputParser(pydantic_object=InstructionUpdateOutput)
    try:
        return parser.parse(output_text)
    except Exception as e:
        # Fallback if the output is not pure JSON or has extra text
        # In a real scenario, we might want to use an LLM to fix it or regex
        print(f"Error parsing output: {e}")
        return {"error": "Failed to parse output"}
