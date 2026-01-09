import json
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field
from typing import List

class Section(BaseModel):
    header: str = Field(description="Section title")
    content: str = Field(description="Section body text")

class PlanSectionsOutput(BaseModel):
    sections: List[Section] = Field(description="Ordered list of dissected sections")

def parse_output(output_text: str):
    parser = JsonOutputParser(pydantic_object=PlanSectionsOutput)
    try:
        return parser.parse(output_text)
    except Exception as e:
        print(f"Error parsing output: {e}")
        return {"error": "Failed to parse output"}
