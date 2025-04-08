import os
import json
import pdfplumber
import re
from .logger import CLIPSLogger

class PDFParser:
    """Class for parsing Variation Definition Documents in PDF format"""
    
    def __init__(self, logger=None):
        self.logger = logger or CLIPSLogger().get_logger()
    
    def parse_variation_pdf(self, pdf_path):
        """Parse a PDF file to extract variation variables and levels"""
        self.logger.info(f"Parsing PDF: {pdf_path}")
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                # Structure to hold our parsed data
                variation_set = {
                    "variables": [],
                    "levels": {}
                }
                
                # Process each page
                for page in pdf.pages:
                    # Extract tables first
                    tables = page.extract_tables()
                    if tables:
                        self._process_tables(tables, variation_set)
                    
                    # Extract text if tables don't yield enough information
                    if not variation_set["variables"]:
                        text = page.extract_text()
                        self._process_text(text, variation_set)
                
                self.logger.info(f"Successfully parsed PDF with {len(variation_set['variables'])} variables")
                return variation_set
                
        except Exception as e:
            self.logger.error(f"Error parsing PDF: {str(e)}")
            raise Exception(f"Failed to parse PDF: {str(e)}")
    
    def _process_tables(self, tables, variation_set):
        """Process tables extracted from the PDF"""
        for table in tables:
            if not table or len(table) <= 1:
                continue
                
            # Attempt to identify header row
            header_row = table[0]
            
            # Skip if table doesn't seem to have headers
            if not header_row or all(cell is None or cell.strip() == "" for cell in header_row):
                continue
            
            # Determine if this is a variation definition table
            is_variation_table = any(header for header in header_row if header and 
                                    ("variable" in header.lower() or "level" in header.lower()))
            
            if is_variation_table:
                self._extract_variations_from_table(table, variation_set)
    
    def _extract_variations_from_table(self, table, variation_set):
        """Extract variation variables and levels from a table"""
        header_row = table[0]
        
        # Determine column indices for variable and levels
        variable_col = None
        level_cols = []
        
        for i, header in enumerate(header_row):
            if header and "variable" in header.lower():
                variable_col = i
            elif header and ("level" in header.lower() or "value" in header.lower()):
                level_cols.append(i)
        
        # If we couldn't identify the right columns, try a different approach
        if variable_col is None:
            # Assume first column is variable name
            variable_col = 0
            level_cols = list(range(1, len(header_row)))
        
        # Process each row (skipping header)
        for row in table[1:]:
            if all(cell is None or cell.strip() == "" for cell in row):
                continue
                
            variable_name = row[variable_col]
            if not variable_name or variable_name.strip() == "":
                continue
                
            variable_name = variable_name.strip()
            
            # Add to variables list if not already there
            if variable_name not in variation_set["variables"]:
                variation_set["variables"].append(variable_name)
                variation_set["levels"][variable_name] = []
            
            # Add levels
            for level_col in level_cols:
                if level_col < len(row) and row[level_col] and row[level_col].strip() != "":
                    level_value = row[level_col].strip()
                    
                    # Check if this level has additional data (in format "value [data]")
                    level_data = None
                    match = re.search(r"(.*?)\s*\[(.*)\]\s*$", level_value)
                    
                    if match:
                        level_value = match.group(1).strip()
                        level_data = match.group(2).strip()
                    
                    # Add level if not already present
                    level_entry = {"value": level_value}
                    if level_data:
                        level_entry["data"] = level_data
                        
                    if level_entry not in variation_set["levels"][variable_name]:
                        variation_set["levels"][variable_name].append(level_entry)
    
    def _process_text(self, text, variation_set):
        """Process extracted text to find variation variables and levels"""
        if not text:
            return
            
        # Look for patterns indicating variables and levels
        # Example patterns:
        # "Variable: GPA Range"  followed by "Levels: 3.88+, 3.5-3.87, 3.0-3.49, <3.0"
        # Or "GPA Range: 3.88+, 3.5-3.87, 3.0-3.49, <3.0"
        
        # First pattern: "Variable: NAME" followed by "Levels: A, B, C"
        variable_pattern = r"Variable[s]?:?\s+([^\n]+)"
        levels_pattern = r"Levels?:?\s+([^\n]+)"
        
        variable_matches = re.finditer(variable_pattern, text, re.IGNORECASE)
        levels_matches = re.finditer(levels_pattern, text, re.IGNORECASE)
        
        # Process matches
        for var_match in variable_matches:
            variable_name = var_match.group(1).strip()
            
            # Find the next levels declaration
            levels_text = ""
            for level_match in levels_matches:
                if level_match.start() > var_match.end():
                    levels_text = level_match.group(1).strip()
                    break
            
            if variable_name and levels_text:
                # Add variable
                if variable_name not in variation_set["variables"]:
                    variation_set["variables"].append(variable_name)
                    variation_set["levels"][variable_name] = []
                
                # Process levels
                levels = [level.strip() for level in levels_text.split(",")]
                for level in levels:
                    if level:
                        level_entry = {"value": level}
                        if level_entry not in variation_set["levels"][variable_name]:
                            variation_set["levels"][variable_name].append(level_entry)
        
        # Second pattern: "NAME: A, B, C"
        combined_pattern = r"([^\n:]+):\s+([^\n]+)"
        combined_matches = re.finditer(combined_pattern, text)
        
        for match in combined_matches:
            variable_name = match.group(1).strip()
            levels_text = match.group(2).strip()
            
            # Skip if this doesn't seem like a variable definition
            if variable_name.lower() in ["variable", "variables", "level", "levels"]:
                continue
                
            # Check if levels_text looks like a comma-separated list
            if "," in levels_text:
                # Add variable
                if variable_name not in variation_set["variables"]:
                    variation_set["variables"].append(variable_name)
                    variation_set["levels"][variable_name] = []
                
                # Process levels
                levels = [level.strip() for level in levels_text.split(",")]
                for level in levels:
                    if level:
                        level_entry = {"value": level}
                        if level_entry not in variation_set["levels"][variable_name]:
                            variation_set["levels"][variable_name].append(level_entry)


class JSONParser:
    """Class for parsing Programs and Clubs JSON data"""
    
    def __init__(self, logger=None):
        self.logger = logger or CLIPSLogger().get_logger()
    
    def parse_json_file(self, json_path):
        """Parse a JSON file and index by eab_cip_code"""
        self.logger.info(f"Parsing JSON: {json_path}")
        
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Determine if this is programs or clubs data
            file_type = self._detect_json_type(data, os.path.basename(json_path))
            
            # Create indexed structure
            indexed_data = {
                "type": file_type,
                "source_file": os.path.basename(json_path),
                "by_cip_code": {}
            }
            
            # Index by eab_cip_code
            if isinstance(data, list):
                for item in data:
                    cip_code = item.get("eab_cip_code")
                    if cip_code:
                        if cip_code not in indexed_data["by_cip_code"]:
                            indexed_data["by_cip_code"][cip_code] = []
                        indexed_data["by_cip_code"][cip_code].append(item)
            elif isinstance(data, dict):
                for key, item in data.items():
                    if isinstance(item, dict):
                        cip_code = item.get("eab_cip_code")
                        if cip_code:
                            if cip_code not in indexed_data["by_cip_code"]:
                                indexed_data["by_cip_code"][cip_code] = []
                            indexed_data["by_cip_code"][cip_code].append(item)
            
            self.logger.info(f"Successfully parsed JSON with {len(indexed_data['by_cip_code'])} CIP codes")
            return indexed_data
                
        except Exception as e:
            self.logger.error(f"Error parsing JSON: {str(e)}")
            raise Exception(f"Failed to parse JSON: {str(e)}")
    
    def _detect_json_type(self, data, filename):
        """Detect if the JSON data is for programs or clubs"""
        if "program" in filename.lower() or "major" in filename.lower():
            return "programs"
        elif "club" in filename.lower() or "org" in filename.lower():
            return "clubs"
        
        # Try to detect from content
        sample = None
        if isinstance(data, list) and data:
            sample = data[0]
        elif isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, dict):
                    sample = value
                    break
        
        if sample:
            if any(key.lower() in ["program_name", "major", "degree"] for key in sample.keys()):
                return "programs"
            elif any(key.lower() in ["club_name", "organization", "activity"] for key in sample.keys()):
                return "clubs"
        
        # Default
        return "unknown"
