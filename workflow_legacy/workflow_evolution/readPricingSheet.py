from langchain.tools import tool

@tool
def readPricingSheet(sheetName: str, documentId: str = ""):
    """访问现有价格表"""
    # Placeholder
    return f"Placeholder content for Pricing Sheet: {sheetName}"
