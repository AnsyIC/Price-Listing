import json
import os
import sys
from langchain.tools import tool

# Ensure workflow_util is importable
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from workflow_util.service_catalog import catalog

@tool
def readPricingSheet1(query: str, sheetName: str = "", top_k: int = 5):
    """Searches the pricing catalog for a service and returns matching items with pricing details.
    
    Args:
        query: The service name to search for (e.g., "HE染色", "小鼠饲养").
        sheetName: Optional sheet name to filter by.
        top_k: Number of top matches to return (default 5).
        
    Returns:
        dict: A dictionary containing query, matches, bestMatch, and confidence.
    """
    return catalog.search(query, sheetName, top_k)
