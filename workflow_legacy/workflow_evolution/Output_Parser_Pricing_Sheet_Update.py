import json
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field

class PricingSheetUpdateOutput(BaseModel):
    updatedPricingSheet: str = Field(description="true or false")
    error: str = Field(description="Error message if any")

def parse_output(output_text: str):
    parser = JsonOutputParser(pydantic_object=PricingSheetUpdateOutput)
    try:
        return parser.parse(output_text)
    except Exception as e:
        print(f"Error parsing output: {e}")
        return {"error": "Failed to parse output"}
