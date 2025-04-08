#!/usr/bin/env python3
import sys
import os
import json
import pdfplumber

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def inspect_pdf_structure(pdf_path):
    """Extract and print the structure of a PDF file"""
    with pdfplumber.open(pdf_path) as pdf:
        structure = {
            "page_count": len(pdf.pages),
            "pages": []
        }
        
        for i, page in enumerate(pdf.pages):
            page_data = {
                "page_number": i + 1,
                "width": page.width,
                "height": page.height,
                "has_text": bool(page.extract_text()),
                "has_tables": bool(page.extract_tables()),
                "table_count": len(page.extract_tables())
            }
            
            # Extract text and first 200 chars as sample
            text = page.extract_text()
            if text:
                page_data["text_sample"] = text[:200] + "..." if len(text) > 200 else text
            
            # Extract tables
            tables = page.extract_tables()
            page_data["tables"] = []
            
            for j, table in enumerate(tables):
                if not table:
                    continue
                    
                table_data = {
                    "table_number": j + 1,
                    "rows": len(table),
                    "columns": len(table[0]) if table and table[0] else 0,
                    "header": table[0] if table and len(table) > 0 else None,
                    "first_row": table[1] if table and len(table) > 1 else None
                }
                page_data["tables"].append(table_data)
            
            structure["pages"].append(page_data)
        
        return structure

def main():
    pdf_path = "/Users/CMelchert/CLIPS-2/examples/South Carolina Variation List.pdf"
    structure = inspect_pdf_structure(pdf_path)
    
    # Print summary
    print(f"PDF Structure Summary for: {pdf_path}")
    print(f"Total Pages: {structure['page_count']}")
    
    # Print detailed page info
    for page in structure["pages"]:
        print(f"\nPage {page['page_number']}:")
        print(f"  Text available: {page['has_text']}")
        print(f"  Tables: {page['table_count']}")
        
        if page["text_sample"]:
            print(f"  Text sample: {page['text_sample']}")
        
        if page["tables"]:
            print(f"  Tables on this page:")
            for table in page["tables"]:
                print(f"    Table {table['table_number']}: {table['rows']} rows x {table['columns']} columns")
                if table["header"]:
                    print(f"    Header: {table['header']}")
                if table["first_row"]:
                    print(f"    First row: {table['first_row']}")
    
    # Save full structure to JSON for later inspection
    with open('pdf_structure.json', 'w') as f:
        json.dump(structure, f, indent=2)
    print("\nFull structure saved to pdf_structure.json")

if __name__ == "__main__":
    main()
