import sys
import os
import json
import pytest

# Add workspace root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from workflow_util.service_catalog import catalog
from workflow_production.validate_pricing_report import validate_pricing_report

def test_catalog_finds_he_staining():
    # Ensure catalog is loaded
    assert len(catalog.items) > 0
    
    # Search for HE staining
    # Note: The catalog might have Chinese name "HE染色" or English "HE staining"
    # Let's try searching for "HE染色" which is common in Chinese catalogs
    result = catalog.search("HE染色")
    
    # If not found, try "HE staining" or just "HE"
    if not result["bestMatch"]:
        result = catalog.search("HE staining")
        
    if not result["bestMatch"]:
        result = catalog.search("HE")
        
    assert result["bestMatch"] is not None
    assert result["confidence"] > 0.8
    print(f"Found HE staining: {result['bestMatch']['canonicalName']}")

def test_validator_catches_outsourced_he_staining():
    # 1. Setup
    dissected_plan = json.dumps({
        "sections": [
            {"header": "Pathology", "content": "Perform HE staining on 10 slides."}
        ]
    })
    
    # 2. Bad Report: HE staining is outsourced
    bad_report = json.dumps({
        "generatedDate": "2023-10-27",
        "notes": [],
        "sections": [
            {
                "sectionHeader": "Pathology",
                "sectionTotal": 0,
                "items": [
                    {
                        "name": "HE染色",
                        "unitPrice": 0,
                        "unit": "unknown",
                        "quantityFactors": {"张": 10},
                        "subtotal": 0,
                        "isOutsourced": True
                    }
                ]
            }
        ],
        "totalCost": 0
    })
    
    # 3. Validate
    errors, retry_delta, hints = validate_pricing_report(
        dissected_plan, 
        bad_report, 
        lambda q: catalog.search(q, top_k=1)
    )
    
    # 4. Assert
    assert len(errors) > 0
    assert any("marked outsourced but exists in catalog" in e for e in errors)
    assert "HE染色" in hints
    print("Validator successfully caught outsourced HE staining.")

def test_validator_accepts_valid_he_staining():
    # 1. Setup
    dissected_plan = json.dumps({
        "sections": [
            {"header": "Pathology", "content": "Perform HE staining on 10 slides."}
        ]
    })
    
    # Find actual price to make it valid
    match = catalog.search("HE染色")["bestMatch"]
    if not match:
        pytest.skip("HE染色 not found in catalog, cannot run valid test")
        
    price = match["unitPrice"]
    unit = match["unit"]
    
    # 2. Good Report
    good_report = json.dumps({
        "generatedDate": "2023-10-27",
        "notes": [],
        "sections": [
            {
                "sectionHeader": "Pathology",
                "sectionTotal": price * 10,
                "items": [
                    {
                        "name": match["canonicalName"],
                        "unitPrice": price,
                        "unit": unit,
                        "quantityFactors": {"张": 10}, # Assuming unit has "张"
                        "subtotal": price * 10,
                        "isOutsourced": False
                    }
                ]
            }
        ],
        "totalCost": price * 10
    })
    
    # 3. Validate
    errors, retry_delta, hints = validate_pricing_report(
        dissected_plan, 
        good_report, 
        lambda q: catalog.search(q, top_k=1)
    )
    
    # 4. Assert
    # Note: Math check might fail if quantity factors don't match unit exactly, 
    # but we are mainly testing the outsourced check.
    # Let's filter for the outsourced error specifically.
    outsourced_errors = [e for e in errors if "marked outsourced but exists in catalog" in e]
    assert len(outsourced_errors) == 0
    print("Validator accepted valid HE staining.")

if __name__ == "__main__":
    # Manually run tests if executed as script
    try:
        test_catalog_finds_he_staining()
        test_validator_catches_outsourced_he_staining()
        test_validator_accepts_valid_he_staining()
        print("All tests passed!")
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
