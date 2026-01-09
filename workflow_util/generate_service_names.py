import sys
import os

# Add workspace root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from workflow_util.service_catalog import catalog

def generate_service_names_file():
    content = catalog.get_service_names_grouped()
    output_path = "/workspace/workflow_data/pricing_service_names.txt"
    
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Successfully generated {output_path}")
    except Exception as e:
        print(f"Error generating file: {e}")

if __name__ == "__main__":
    generate_service_names_file()
