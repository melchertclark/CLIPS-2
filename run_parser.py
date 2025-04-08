#!/usr/bin/env python3
import os
import sys
import json
import argparse
import logging

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import parser
from backend.parsing import PDFParser
from backend.api import run_api

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("PDFParser")
logger.setLevel(logging.DEBUG)

# Create console handler
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
logger.addHandler(ch)

def parse_pdf(pdf_path, output_path=None, format_type=None, edit_fields=None):
    """Parse a PDF file and output the result"""
    parser = PDFParser(logger)
    
    print(f"Parsing PDF: {pdf_path}")
    variation_set = parser.parse_variation_pdf(pdf_path, format_type)
    
    # Apply field edits if provided
    if edit_fields:
        for edit in edit_fields:
            parts = edit.split('=', 1)
            if len(parts) != 2:
                logger.warning(f"Invalid edit format: {edit}")
                continue
                
            # Parse variable, data, and value
            field_ref, new_value = parts
            field_parts = field_ref.split(':')
            
            if len(field_parts) != 2:
                logger.warning(f"Invalid field reference: {field_ref}")
                continue
                
            variable, data = field_parts
            
            # Update field
            update = {
                'variable': variable,
                'data': data,
                'value': new_value
            }
            
            variation_set = parser.update_field_values(variation_set, [update])
    
    print("\nVariation Set Results:")
    print(f"Variables: {variation_set['variables']}")
    
    for var in variation_set["variables"]:
        levels = variation_set["levels"].get(var, [])
        print(f"\n{var} - {len(levels)} levels:")
        
        if "Academic Field" in var:
            print("\nAcademic Field of Interest Levels:")
            for level in levels:
                print(f"  - {level['data']}: {level['value']}")
    
    # Save results to JSON
    if output_path:
        output_file = output_path
    else:
        output_file = 'parsed_variations.json'
        
    with open(output_file, 'w') as f:
        json.dump(variation_set, f, indent=2)
    print(f"\nResults saved to {output_file}")
    
    return variation_set

def main():
    """Main entry point with command line arguments"""
    parser = argparse.ArgumentParser(description='Variation Definition PDF Parser')
    
    # Mode selection
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument('--api', action='store_true', help='Run as API server')
    mode_group.add_argument('--pdf', type=str, help='Parse a specific PDF file')
    mode_group.add_argument('--url', type=str, help='Parse a PDF from a URL')
    
    # API options
    parser.add_argument('--host', type=str, default='0.0.0.0', help='API server host (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=5000, help='API server port (default: 5000)')
    
    # Parser options
    parser.add_argument('--output', type=str, help='Output JSON file path')
    parser.add_argument('--format', type=str, choices=['south_carolina', 'standard'], 
                      help='PDF format type hint')
    parser.add_argument('--edit', type=str, nargs='+', 
                      help='Edit fields in format "Variable:ID=New Value"')
    
    args = parser.parse_args()
    
    if args.api:
        # Run API server
        print(f"Starting API server on {args.host}:{args.port}")
        run_api(host=args.host, port=args.port)
    else:
        # Parse PDF
        pdf_path = args.pdf or args.url
        parse_pdf(pdf_path, args.output, args.format, args.edit)

if __name__ == "__main__":
    main()