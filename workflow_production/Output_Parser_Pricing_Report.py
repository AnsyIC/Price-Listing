import json
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field
from typing import List, Dict, Any

class PricingReportOutput(BaseModel):
    notes: List[str]
    sections: List[Dict[str, Any]]
    totalCost: float

def parse_output(output_text: str):
    parser = JsonOutputParser(pydantic_object=PricingReportOutput)
    try:
        return parser.parse(output_text)
    except Exception as e:
        print(f"Error parsing output: {e}")
        return {"error": "Failed to parse output"}
