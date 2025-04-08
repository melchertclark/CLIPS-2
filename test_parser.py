#\!/usr/bin/env python3
import sys
import os
import json
import logging

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import parser
from backend.parsing import PDFParser

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("PDFParser")
logger.setLevel(logging.DEBUG)

# Create console handler
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
logger.addHandler(ch)

def main():
    pdf_path = "/Users/CMelchert/CLIPS-2/examples/South Carolina Variation List.pdf"
    parser = PDFParser(logger)
    
    print(f"Parsing PDF: {pdf_path}")
    variation_set = parser.parse_variation_pdf(pdf_path)
    
    print("\nVariation Set Results:")
    print(f"Variables: {variation_set['variables']}")
    
    for var in variation_set["variables"]:
        levels = variation_set["levels"].get(var, [])
        print(f"\n{var} - {len(levels)} levels:")
        
        if "Academic Field" in var:
            print("\nAcademic Field of Interest Levels:")
            for level in levels:
                print(f"  - {level['data']}: {level['value']}")
    
    # Save results to JSON for inspection
    with open('parsed_variations.json', 'w') as f:
        json.dump(variation_set, f, indent=2)
    print("\nResults saved to parsed_variations.json")

if __name__ == "__main__":
    main()
