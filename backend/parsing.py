import os
import json
import pdfplumber
import re
import requests
from io import BytesIO
from .logger import CLIPSLogger

class PDFParser:
    """Class for parsing Variation Definition Documents in PDF format"""
    
    def __init__(self, logger=None):
        self.logger = logger or CLIPSLogger()
        # Add direct logging methods if using the standard logger
        if hasattr(self.logger, 'get_logger'):
            self.logger = self.logger.get_logger()
    
    def parse_variation_pdf(self, pdf_path, format_type=None):
        """Parse a PDF file to extract variation variables and levels
        
        Args:
            pdf_path (str): Path to PDF file or URL for remote PDF
            format_type (str, optional): Format type hint ('south_carolina', 'standard', etc.)
            
        Returns:
            dict: Extracted variation data structure
        """
        self.logger.info(f"Parsing PDF: {pdf_path}")
        
        try:
            # Handle URL or file path
            if pdf_path.startswith(('http://', 'https://')):
                # Download from URL
                self.logger.info(f"Downloading PDF from URL: {pdf_path}")
                response = requests.get(pdf_path, stream=True)
                response.raise_for_status()  # Raise exception for HTTP errors
                pdf_data = BytesIO(response.content)
                pdf = pdfplumber.open(pdf_data)
            else:
                # Local file
                pdf = pdfplumber.open(pdf_path)
            
            # Continue with PDF processing
            with pdf:
                # Structure to hold our parsed data
                variation_set = {
                    "variables": [],
                    "levels": {}
                }
                
                # Process all pages to get all tables and text
                all_tables = []
                all_text = ""
                
                for page in pdf.pages:
                    # Extract tables
                    tables = page.extract_tables()
                    if tables:
                        self.logger.info(f"Found {len(tables)} tables on page {page.page_number}")
                        all_tables.extend(tables)
                    
                    # Extract text
                    page_text = page.extract_text()
                    if page_text:
                        all_text += page_text + "\n\n"
                
                # Apply specific format handler if provided
                if format_type == 'south_carolina':
                    # Use South Carolina format directly
                    self._extract_variables_individually(all_tables, all_text, variation_set)
                else:
                    # First try to extract variables from a unified table format
                    if not self._extract_from_unified_table(all_tables, variation_set):
                        # If unified table approach doesn't work, try individual variable extraction
                        self._extract_variables_individually(all_tables, all_text, variation_set)
                
                # Calculate total variations
                total_variations = self._calculate_total_variations(variation_set)
                
                # Log results
                self.logger.info(f"Successfully parsed PDF with {len(variation_set['variables'])} variables")
                self.logger.info(f"Variables found: {', '.join(variation_set['variables'])}")
                self.logger.info(f"Total possible variations: {total_variations}")
                
                # Print the number of levels for each variable
                for var in variation_set["variables"]:
                    level_count = len(variation_set["levels"].get(var, []))
                    self.logger.info(f"Variable '{var}' has {level_count} levels")
                    
                    # Debug: Print actual level values
                    if "Academic Field of Interest" in var:
                        self.logger.info("Academic Field of Interest levels:")
                        for level in variation_set["levels"][var]:
                            self.logger.info(f"  - {level['data']}: {level['value']}")
                
                # Verify we have the right structure for all variables
                self._verify_and_fix_structure(variation_set)
                
                return variation_set
                
        except Exception as e:
            self.logger.error(f"Error parsing PDF: {str(e)}")
            raise Exception(f"Failed to parse PDF: {str(e)}")
    
    def update_field_values(self, variation_set, field_updates):
        """Update specific field values in a variation set
        
        Args:
            variation_set (dict): The current variation set
            field_updates (list): List of update dicts with:
                - variable: Variable name to update
                - data: Level ID/data value to match
                - value: New value to use
                
        Returns:
            dict: Updated variation set
        """
        for update in field_updates:
            var_name = update.get('variable')
            data_id = update.get('data')
            new_value = update.get('value')
            
            # Skip if missing required fields
            if not var_name or not data_id or not new_value:
                self.logger.warning(f"Skipping invalid field update: {update}")
                continue
                
            # Skip if variable doesn't exist
            if var_name not in variation_set["levels"]:
                self.logger.warning(f"Variable not found: {var_name}")
                continue
                
            # Find and update the matching level
            found = False
            for level in variation_set["levels"][var_name]:
                if str(level.get("data")) == str(data_id):
                    self.logger.info(f"Updating {var_name}[{data_id}] from '{level['value']}' to '{new_value}'")
                    level["value"] = new_value
                    found = True
                    break
            
            if not found:
                self.logger.warning(f"Level ID {data_id} not found for variable {var_name}")
        
        return variation_set
    
    def add_field_value(self, variation_set, variable, value, data=None):
        """Add a new field value to a variable
        
        Args:
            variation_set (dict): The current variation set
            variable (str): Variable name to add to
            value (str): Value to add
            data (str, optional): Data ID to use, auto-assigned if None
            
        Returns:
            dict: Updated variation set
        """
        # Skip if variable doesn't exist
        if variable not in variation_set["variables"]:
            self.logger.warning(f"Variable not found: {variable}")
            return variation_set
            
        # Auto-assign data ID if not provided
        if data is None:
            # Find next available number
            existing_ids = [level.get("data") for level in variation_set["levels"][variable] 
                         if level.get("data") != "Default" and level.get("data", "").isdigit()]
            next_id = str(max([int(id) for id in existing_ids if id.isdigit()] + [0]) + 1)
            data = next_id
        
        # Check if entry with this data ID already exists
        for level in variation_set["levels"][variable]:
            if level.get("data") == data:
                self.logger.warning(f"Entry with data ID {data} already exists for {variable}")
                return variation_set
        
        # Add new entry
        variation_set["levels"][variable].append({
            "value": value,
            "data": data
        })
        
        self.logger.info(f"Added new {variable} value: {value} with ID {data}")
        return variation_set
    
    def _extract_from_unified_table(self, tables, variation_set):
        """Extract variables from a unified table format (like a table with multiple columns for each variable)"""
        # Look for tables that might have a row/column format with all variables
        for table in tables:
            if not table or len(table) < 3:  # Need at least header + 2 rows
                continue
            
            # Check if this looks like a variation definition table
            header_row = table[0]
            if not header_row:
                continue
            
            # Clean and convert header to lowercase for easier matching
            header = [str(cell).lower().strip() if cell else "" for cell in header_row]
            
            # Check if the first cell contains "variable" or similar
            if header and any(term in header[0] for term in ["variable", "var", "type"]):
                # This looks like a variation definition table
                self.logger.info("Found unified variation definition table")
                
                # Process the table as a definition of variables and levels
                return self._process_unified_table(table, variation_set)
        
        return False
    
    def _process_unified_table(self, table, variation_set):
        """Process a unified table that defines variables in rows and levels in columns"""
        if len(table) < 2:
            return False
        
        header_row = table[0]
        # Determine if this is a row-based or column-based table
        # Row-based: Variables in rows, levels in columns (more common)
        # Column-based: Variables in columns, levels in rows

        # Try row-based first (variables in rows)
        valid_variables = 0
        
        for row_idx in range(1, len(table)):
            row = table[row_idx]
            if not row or len(row) < 2:
                continue
            
            variable_name = str(row[0]).strip() if row[0] else ""
            if not variable_name or variable_name.lower() == "variable":
                continue
            
            # Check if this is a recognized variable name
            if any(term in variable_name.lower() for term in ["gpa", "grade", "academic", "field", "distance", "miles"]):
                # Standardize some common variable names
                if "gpa" in variable_name.lower() or "grade" in variable_name.lower():
                    variable_name = "GPA Range"
                elif "distance" in variable_name.lower() or "miles" in variable_name.lower():
                    variable_name = "Distance"
                elif "field" in variable_name.lower() or "academic" in variable_name.lower() or "interest" in variable_name.lower():
                    variable_name = "Academic Field of Interest"
                
                # Extract levels from the row
                levels = []
                for col_idx in range(1, len(row)):
                    if row[col_idx]:
                        level_value = str(row[col_idx]).strip()
                        
                        # Look for [CODE] pattern in the level
                        cip_match = re.search(r'\[([A-Z0-9]+)\]', level_value)
                        if cip_match:
                            # Extract code and clean level value
                            code = cip_match.group(1)
                            clean_value = level_value.replace(cip_match.group(0), '').strip()
                            
                            levels.append({
                                "value": clean_value,
                                "data": code
                            })
                        else:
                            # No code, use column index as the ID
                            levels.append({
                                "value": level_value,
                                "data": str(col_idx)
                            })
                
                if levels:
                    variation_set["variables"].append(variable_name)
                    variation_set["levels"][variable_name] = levels
                    valid_variables += 1
        
        return valid_variables > 0
    
    def _extract_variables_individually(self, tables, text, variation_set):
        """Extract variables individually from tables or text"""
        # Try to extract GPA, Distance, and Academic Field variables
        gpa_extracted = self._extract_gpa_variable(tables, text, variation_set)
        distance_extracted = self._extract_distance_variable(tables, text, variation_set)
        field_extracted = self._extract_academic_field_variable(tables, text, variation_set)
        
        # If any variable wasn't found, try harder with text extraction
        if not gpa_extracted or not distance_extracted or not field_extracted:
            self.logger.info("Not all variables found in tables, attempting text extraction")
            self._extract_from_text(text, variation_set)
    
    def _extract_gpa_variable(self, tables, text, variation_set):
        """Extract GPA variable from tables or text"""
        variable_name = "GPA Range"
        
        # Add to variables if not already there
        if variable_name not in variation_set["variables"]:
            variation_set["variables"].append(variable_name)
            variation_set["levels"][variable_name] = []
        
        # Look for GPA specific tables first
        for table in tables:
            if not table or len(table) <= 1:
                continue
            
            # Check if this looks like a GPA table
            has_gpa_keywords = False
            for row in table[:2]:  # Check header and first row
                if row and any(cell and "gpa" in str(cell).lower() for cell in row):
                    has_gpa_keywords = True
                    break
            
            if has_gpa_keywords:
                self.logger.info("Found GPA-specific table")
                self._process_gpa_table(table, variation_set)
                if variation_set["levels"][variable_name]:
                    return True
        
        # If no GPA levels found, try extracting from text
        if not variation_set["levels"][variable_name]:
            gpa_segment = self._extract_segment(text, ["gpa", "grade point", "academic performance"])
            if gpa_segment:
                self._process_text_segment(gpa_segment, variable_name, variation_set)
        
        # Default GPA levels if none found
        if not variation_set["levels"][variable_name]:
            self.logger.info("Using default GPA levels")
            variation_set["levels"][variable_name] = [
                {"value": "3.5+", "data": "1"},
                {"value": "3.0-3.49", "data": "2"},
                {"value": "2.5-2.99", "data": "3"},
                {"value": "Below 2.5", "data": "4"},
                {"value": "Unknown/Null", "data": "Default"}
            ]
        
        return len(variation_set["levels"][variable_name]) > 0
    
    def _process_gpa_table(self, table, variation_set):
        """Process a table that contains GPA information"""
        variable_name = "GPA Range"
        
        # Try to identify columns for variation number and GPA range
        var_col = None
        level_col = None
        
        # Check the header row
        header_row = table[0]
        for i, cell in enumerate(header_row):
            if not cell:
                continue
            cell_lower = str(cell).lower()
            
            if any(term in cell_lower for term in ["variation", "var", "number", "#", "id"]):
                var_col = i
            elif any(term in cell_lower for term in ["gpa", "range", "value"]):
                level_col = i
        
        # If columns not identified, make assumptions
        if var_col is None or level_col is None:
            # Assume first column is variation number, second is GPA range
            var_col = 0
            level_col = 1
        
        # Process each row (skip header)
        for row in table[1:]:
            if len(row) <= max(var_col, level_col) or all(cell is None or str(cell).strip() == "" for cell in row):
                continue
            
            var_num = row[var_col]
            gpa_range = row[level_col]
            
            if var_num is not None and gpa_range is not None:
                var_num = str(var_num).strip()
                gpa_range = str(gpa_range).strip()
                
                # Handle "Default" case
                if var_num.lower() == "default" or gpa_range.lower() == "default":
                    var_num = "Default"
                    if gpa_range.lower() == "default":
                        gpa_range = "Unknown/Null"
                
                # Add level with variation number as data
                level_entry = {
                    "value": gpa_range,
                    "data": var_num
                }
                
                # Check if we already have this level
                if not any(level.get("value") == gpa_range for level in variation_set["levels"][variable_name]):
                    variation_set["levels"][variable_name].append(level_entry)
    
    def _extract_distance_variable(self, tables, text, variation_set):
        """Extract Distance variable from tables or text"""
        variable_name = "Distance"
        
        # Add to variables if not already there
        if variable_name not in variation_set["variables"]:
            variation_set["variables"].append(variable_name)
            variation_set["levels"][variable_name] = []
        
        # Look for Distance specific tables first
        for table in tables:
            if not table or len(table) <= 1:
                continue
            
            # Check if this looks like a Distance table
            has_distance_keywords = False
            for row in table[:2]:  # Check header and first row
                if row and any(cell and any(term in str(cell).lower() for term in ["distance", "miles"]) for cell in row):
                    has_distance_keywords = True
                    break
            
            if has_distance_keywords:
                self.logger.info("Found Distance-specific table")
                self._process_distance_table(table, variation_set)
                if variation_set["levels"][variable_name]:
                    return True
        
        # If no Distance levels found, try extracting from text
        if not variation_set["levels"][variable_name]:
            distance_segment = self._extract_segment(text, ["distance", "miles", "proximity"])
            if distance_segment:
                self._process_text_segment(distance_segment, variable_name, variation_set)
        
        # Default Distance levels if none found
        if not variation_set["levels"][variable_name]:
            self.logger.info("Using default Distance levels")
            variation_set["levels"][variable_name] = [
                {"value": "0-50 miles", "data": "1"},
                {"value": "51-200 miles", "data": "2"},
                {"value": "201-500 miles", "data": "3"},
                {"value": "500+ miles", "data": "4"},
                {"value": "Unknown/Null", "data": "Default"}
            ]
        
        return len(variation_set["levels"][variable_name]) > 0
    
    def _process_distance_table(self, table, variation_set):
        """Process a table that contains Distance information"""
        variable_name = "Distance"
        
        # Try to identify columns for variation number and distance range
        var_col = None
        level_col = None
        
        # Check the header row
        header_row = table[0]
        for i, cell in enumerate(header_row):
            if not cell:
                continue
            cell_lower = str(cell).lower()
            
            if any(term in cell_lower for term in ["variation", "var", "number", "#", "id"]):
                var_col = i
            elif any(term in cell_lower for term in ["distance", "miles", "range", "value"]):
                level_col = i
        
        # If columns not identified, make assumptions
        if var_col is None or level_col is None:
            # Assume first column is variation number, second is distance range
            var_col = 0
            level_col = 1
        
        # Process each row (skip header)
        for row in table[1:]:
            if len(row) <= max(var_col, level_col) or all(cell is None or str(cell).strip() == "" for cell in row):
                continue
            
            var_num = row[var_col]
            distance_range = row[level_col]
            
            if var_num is not None and distance_range is not None:
                var_num = str(var_num).strip()
                distance_range = str(distance_range).strip()
                
                # Handle "Default" case
                if var_num.lower() == "default" or distance_range.lower() == "default":
                    var_num = "Default"
                    if distance_range.lower() == "default":
                        distance_range = "Unknown/Null"
                
                # Add level with variation number as data
                level_entry = {
                    "value": distance_range,
                    "data": var_num
                }
                
                # Check if we already have this level
                if not any(level.get("value") == distance_range for level in variation_set["levels"][variable_name]):
                    variation_set["levels"][variable_name].append(level_entry)
    
    def _extract_academic_field_variable(self, tables, text, variation_set):
        """Extract Academic Field of Interest variable from tables or text"""
        variable_name = "Academic Field of Interest"
        
        # Add to variables if not already there
        if variable_name not in variation_set["variables"]:
            variation_set["variables"].append(variable_name)
            variation_set["levels"][variable_name] = []

        # Handle South Carolina variation list format with the field table on page 2
        field_table_found = self._process_south_carolina_field_format(tables, variation_set)
        if field_table_found and len(variation_set["levels"][variable_name]) > 5:
            self.logger.info(f"Successfully processed South Carolina format, found {len(variation_set['levels'][variable_name])} academic fields")
            return True
        
        # First check if the academic fields are in a unified table
        field_row_found = False
        for table in tables:
            if not table or len(table) < 2:
                continue
            
            # Try to find academic field row in the table
            for row_idx, row in enumerate(table):
                if not row or len(row) < 2:
                    continue
                
                first_cell = str(row[0]).lower() if row[0] else ""
                if "field" in first_cell or "academic" in first_cell or "interest" in first_cell:
                    self.logger.info(f"Found Academic Field row in table: {row}")
                    self._process_academic_field_row(row, variation_set)
                    field_row_found = True
                    break
        
        # Look for Academic Field specific tables if not found in unified table
        if not field_row_found:
            self.logger.info("Looking for dedicated Academic Field tables")
            for table in tables:
                if not table or len(table) <= 1:
                    continue
                
                # Check if this looks like an Academic Field table
                has_field_keywords = False
                for row in table[:2]:  # Check header and first row
                    if row and any(cell and any(term in str(cell).lower() for term in ["field", "academic", "interest"]) for cell in row):
                        has_field_keywords = True
                        break
                
                if has_field_keywords:
                    self.logger.info("Found Academic Field-specific table")
                    self._process_academic_field_table(table, variation_set)
                    if len(variation_set["levels"][variable_name]) > 3:  # If we found several fields
                        return True
        
        # Try text extraction if table approach didn't find enough fields
        if len(variation_set["levels"][variable_name]) < 4:
            self.logger.info("Not enough Academic Fields found in tables, attempting text extraction")
            academic_segment = self._extract_segment(text, ["academic field", "field of interest", "major", "program"])
            if academic_segment:
                self._process_text_segment(academic_segment, variable_name, variation_set)
            
            # Also try to find field definitions with codes in brackets
            self._extract_fields_with_codes(text, variation_set)
        
        # Use default Academic Field levels if we still don't have enough
        if len(variation_set["levels"][variable_name]) < 4:
            self.logger.info("Using default Academic Field levels")
            # For sample_variation_definition.md which has [BUS001] format
            variation_set["levels"][variable_name] = [
                {"value": "Business", "data": "BUS001"},
                {"value": "Engineering", "data": "ENG002"},
                {"value": "Arts", "data": "ART003"},
                {"value": "Science", "data": "SCI004"},
                {"value": "Default", "data": "Default"}
            ]
        
        return len(variation_set["levels"][variable_name]) > 0
        
    def _process_south_carolina_field_format(self, tables, variation_set):
        """Special processing for South Carolina Variation List PDF format"""
        variable_name = "Academic Field of Interest"
        field_table_found = False
        
        # Look for the academic field table on page 2-3
        field_interest_table = None
        
        for table in tables:
            if not table or len(table) < 3:  # Need at least header + 2 rows
                continue
                
            # Check if this is the Field of Interest table (look for characteristic header)
            for row_idx, row in enumerate(table[:3]):  # Check first few rows
                if not row:
                    continue
                
                # Check for the "Field of Interest" column header
                cells_text = " ".join(str(cell) for cell in row if cell)
                if "Field of Interest" in cells_text and "Variation" in cells_text:
                    field_table_found = True
                    field_interest_table = table
                    self.logger.info(f"Found Field of Interest table with {len(table)} rows")
                    break
        
        if field_interest_table:
            # Find column indices for variation number and field of interest
            var_col = None
            field_col = None
            
            # Check the header row
            for row_idx, row in enumerate(field_interest_table[:3]):  # Check first few rows for headers
                for col_idx, cell in enumerate(row):
                    if not cell:
                        continue
                    cell_str = str(cell).strip()
                    
                    if "Variation" in cell_str:
                        var_col = col_idx
                    elif "Field of Interest" in cell_str:
                        field_col = col_idx
            
            if var_col is not None and field_col is not None:
                self.logger.info(f"Found variation column at index {var_col} and field column at index {field_col}")
                
                # Process rows (skip header rows)
                # First find the header row index
                header_row_idx = 0
                for idx, row in enumerate(field_interest_table):
                    if row and any(cell and "Field of Interest" in str(cell) for cell in row):
                        header_row_idx = idx
                        break
                
                # Process all rows after the header
                fields_processed = 0
                for row in field_interest_table[header_row_idx + 1:]:
                    if not row or len(row) <= max(var_col, field_col):
                        continue
                    
                    var_num = row[var_col]
                    field_name = row[field_col]
                    
                    # Skip rows without both variation number and field name
                    if not var_num or not field_name:
                        continue
                    
                    var_num = str(var_num).strip()
                    field_name = str(field_name).strip()
                    
                    # Skip empty fields or headers
                    if not var_num or not field_name or field_name.lower() == "unknown/null" or var_num.lower() in ["variation", "field", "programs"]:
                        continue
                        
                    # Skip rows with likely non-field content
                    invalid_content = ["©", "eab.com", "all rights", "reserved", "university"]
                    if any(invalid in field_name.lower() for invalid in invalid_content):
                        continue
                    
                    # Filter valid field entries
                    if var_num.isdigit() or var_num.lower() == "default":
                        if var_num.lower() == "default":
                            var_num = "Default"
                        
                        # Add field if not already there
                        level_entry = {
                            "value": field_name,
                            "data": var_num
                        }
                        
                        # Check if we already have this field
                        if not any(level.get("data") == var_num for level in variation_set["levels"][variable_name]):
                            variation_set["levels"][variable_name].append(level_entry)
                            fields_processed += 1
                            self.logger.info(f"Added field: {field_name} with variation {var_num}")
            
                # Make sure we have the Default level
                has_default = any(level.get("data") == "Default" for level in variation_set["levels"][variable_name])
                if not has_default:
                    variation_set["levels"][variable_name].append({
                        "value": "Default",
                        "data": "Default"
                    })
                
                self.logger.info(f"Processed {fields_processed} fields from South Carolina format table")
                
                # Process additional fields from small tables throughout the PDF
                self._extract_additional_south_carolina_fields(tables, variation_set)
        else:
            # If no main field table found, try harder with other small tables
            self._extract_additional_south_carolina_fields(tables, variation_set)
        
        return field_table_found
        
    def _extract_additional_south_carolina_fields(self, tables, variation_set):
        """Extract additional academic fields from small tables in the South Carolina PDF"""
        variable_name = "Academic Field of Interest"
        fields_added = 0
        
        # Standard field categories from CIP codes
        standard_field_categories = [
            "Agriculture",
            "Natural Resources",
            "Architecture",
            "Area, Ethnic, Cultural, Gender, and Group Studies",
            "Communication, Journalism",
            "Communications Technologies",
            "Computer and Information Sciences",
            "Education",
            "Engineering",
            "Engineering Technologies",
            "Foreign Languages, Literatures, and Linguistics",
            "Family and Consumer Sciences",
            "Legal Professions and Studies",
            "English Language and Literature",
            "Liberal Arts and Sciences, General Studies",
            "Library Science",
            "Biological and Biomedical Sciences",
            "Mathematics and Statistics",
            "Military Science",
            "Multi/Interdisciplinary Studies",
            "Parks, Recreation, Leisure, and Fitness",
            "Philosophy and Religious Studies",
            "Physical Sciences",
            "Psychology",
            "Security and Protective Services",
            "Public Administration and Social Service",
            "Social Sciences",
            "Visual and Performing Arts",
            "Health Professions",
            "Business, Management, Marketing",
            "History"
        ]
        
        # Look for field names in small tables
        for table in tables:
            if not table or len(table) < 1 or len(table) > 5:  # Only check small tables (1-4 rows)
                continue
            
            # Check if this is a standalone field name table
            field_name = ""
            
            # Join all non-empty cells in the first column
            for row in table:
                if row and len(row) > 0 and row[0]:
                    cell_text = str(row[0]).strip()
                    if cell_text and len(cell_text) > 2:  # Skip very short cells
                        field_name += cell_text + " "
            
            field_name = field_name.strip()
            
            # Check if this resembles a field category
            if field_name and len(field_name) > 5:
                # Check if it matches any known field category patterns
                is_field_category = False
                
                # Check against known field categories
                for category in standard_field_categories:
                    # Full match or partial match of beginning with at least 5 chars
                    if category.lower() in field_name.lower() or (len(category) > 5 and category.lower()[:5] in field_name.lower()):
                        is_field_category = True
                        break
                
                # Check for other common patterns
                common_field_words = ["studies", "science", "arts", "education", "engineering", 
                                     "health", "business", "technology", "management", "communication"]
                
                if not is_field_category:
                    for word in common_field_words:
                        if word in field_name.lower():
                            is_field_category = True
                            break
                
                if is_field_category:
                    # This looks like a valid field category
                    # Clean up field name - remove common artifacts
                    field_name = re.sub(r'\brelated\b|\bprograms\b|\bfield\b|\bvariable\b', '', field_name, flags=re.IGNORECASE).strip()
                    
                    # Further clean up and normalize field name
                    field_name = re.sub(r'\s+', ' ', field_name).strip()
                    if field_name.endswith(','):
                        field_name = field_name[:-1]
                    
                    # Only process if field name is substantial
                    if len(field_name) > 5:
                        # Assign a new variation number 
                        existing_nums = [int(level.get("data")) for level in variation_set["levels"][variable_name] 
                                      if level.get("data") != "Default" and level.get("data").isdigit()]
                        next_num = max(existing_nums) + 1 if existing_nums else 1
                        
                        # Add field if not already there (check by name similarity)
                        if not any(self._is_similar_field(level.get("value"), field_name) for level in variation_set["levels"][variable_name]):
                            level_entry = {
                                "value": field_name,
                                "data": str(next_num)
                            }
                            variation_set["levels"][variable_name].append(level_entry)
                            fields_added += 1
                            self.logger.info(f"Added supplementary field: {field_name}")
        
        # Also scan for Business, Marketing and other common fields in the text of tables
        for table in tables:
            if not table or len(table) < 2:  # Skip very small tables
                continue
            
            # Check for field names in other columns
            for row in table:
                for cell in row:
                    if not cell:
                        continue
                    
                    cell_text = str(cell).strip()
                    # Skip very short or empty cells
                    if not cell_text or len(cell_text) < 10:
                        continue
                    
                    # Look for business and marketing field patterns
                    if ("business" in cell_text.lower() or "marketing" in cell_text.lower()) and "," in cell_text:
                        # This might be a business field - extract it
                        field_name = "Business, Management, Marketing, and Related Support Services"
                        
                        # Check if we already have a business field
                        if not any("business" in level.get("value", "").lower() for level in variation_set["levels"][variable_name]):
                            # Assign a new variation number
                            existing_nums = [int(level.get("data")) for level in variation_set["levels"][variable_name] 
                                          if level.get("data") != "Default" and level.get("data").isdigit()]
                            next_num = max(existing_nums) + 1 if existing_nums else 1
                            
                            level_entry = {
                                "value": field_name,
                                "data": str(next_num)
                            }
                            variation_set["levels"][variable_name].append(level_entry)
                            fields_added += 1
                            self.logger.info(f"Added business field: {field_name}")
                            break  # Only add business field once
        
        # If applicable, add other common field categories not yet included
        existing_fields = [level.get("value", "").lower() for level in variation_set["levels"][variable_name]]
        
        for category in standard_field_categories:
            category_lower = category.lower()
            # Check if we already have this field category or similar
            if not any(cat_word in field.lower() for cat_word in category_lower.split() for field in existing_fields if len(cat_word) > 4):
                # Check if this is a common major field category
                common_categories = ["Business", "Engineering", "Computer", "Health", "Education", 
                                   "Science", "Psychology", "Communication", "Arts"]
                
                if any(common in category for common in common_categories):
                    # Add this common category
                    existing_nums = [int(level.get("data")) for level in variation_set["levels"][variable_name] 
                                  if level.get("data") != "Default" and level.get("data").isdigit()]
                    next_num = max(existing_nums) + 1 if existing_nums else 1
                    
                    level_entry = {
                        "value": category,
                        "data": str(next_num)
                    }
                    variation_set["levels"][variable_name].append(level_entry)
                    fields_added += 1
                    self.logger.info(f"Added standard field category: {category}")
                    
                    # Limit how many we add automatically
                    if fields_added > 10:
                        break
        
        self.logger.info(f"Added {fields_added} supplementary fields from tables")
        
        # Clean up field names - fix incomplete field names
        for level in variation_set["levels"][variable_name]:
            value = level.get("value", "")
            
            # Complete incomplete field names with standard naming
            if value == "Communication, Journalism, and":
                level["value"] = "Communication, Journalism, and Related Programs"
            
            # Clean up any non-field values (like raw degrees/majors)
            if "B.A." in value or "B.S." in value:
                # Check if this is a field with degree names - shorten if too long
                if len(value.split(',')) > 3 and len(value) > 70:
                    # Extract the first part before listing degrees
                    parts = value.split(',')
                    # Look for a pattern like "Social Sciences" in the value
                    for category in standard_field_categories:
                        if category.lower() in value.lower():
                            level["value"] = category
                            break
                    # If not found, use the first segment as the field name
                    if level["value"] == value:
                        level["value"] = parts[0]
        
    def _is_similar_field(self, field1, field2):
        """Check if two field names are similar (to avoid duplicates)"""
        if not field1 or not field2:
            return False
            
        field1 = str(field1).lower()
        field2 = str(field2).lower()
        
        # Direct match
        if field1 == field2:
            return True
            
        # Check if one is a substring of the other
        if field1 in field2 or field2 in field1:
            return True
            
        # Check for common significant words (at least 4 chars)
        words1 = [w for w in field1.split() if len(w) > 3]
        words2 = [w for w in field2.split() if len(w) > 3]
        
        common_words = set(words1).intersection(set(words2))
        
        # If they share at least 2 significant words, consider them similar
        return len(common_words) >= 2
    
    def _process_academic_field_row(self, row, variation_set):
        """Process a row that contains Academic Field information in a unified table"""
        variable_name = "Academic Field of Interest"
        
        # Skip the first cell (variable name)
        for col_idx in range(1, len(row)):
            if not row[col_idx]:
                continue
                
            cell_value = str(row[col_idx]).strip()
            if not cell_value:
                continue
            
            # Look for [CODE] pattern
            cip_match = re.search(r'\[([A-Z0-9]+)\]', cell_value)
            if cip_match:
                # Extract code and clean field name
                code = cip_match.group(1)
                field_name = cell_value.replace(cip_match.group(0), '').strip()
                
                level_entry = {
                    "value": field_name,
                    "data": code
                }
                
                # Add if not already there
                if not any(level.get("data") == code for level in variation_set["levels"][variable_name]):
                    variation_set["levels"][variable_name].append(level_entry)
            else:
                # No code found, use column index as data
                level_entry = {
                    "value": cell_value,
                    "data": str(col_idx)
                }
                
                # Add if not already there
                if not any(level.get("value") == cell_value for level in variation_set["levels"][variable_name]):
                    variation_set["levels"][variable_name].append(level_entry)
    
    def _process_academic_field_table(self, table, variation_set):
        """Process a table that contains Academic Field information"""
        variable_name = "Academic Field of Interest"
        
        # Try to identify columns for variation/CIP number and field name
        var_col = None
        field_col = None
        cip_col = None  # Optional column for explicit CIP code
        
        # Check the header row
        header_row = table[0]
        for i, cell in enumerate(header_row):
            if not cell:
                continue
            cell_lower = str(cell).lower()
            
            if any(term in cell_lower for term in ["variation", "var", "number", "#", "id", "cip"]):
                var_col = i
            elif any(term in cell_lower for term in ["field", "program", "major", "academic", "discipline"]):
                field_col = i
            elif "cip" in cell_lower or "code" in cell_lower:
                cip_col = i
        
        # If columns not identified, make assumptions
        if var_col is None or field_col is None:
            # Log the header for debugging
            self.logger.info(f"Academic field table header not clearly identified: {header_row}")
            
            # Assume first column is variation number, second is field name
            var_col = 0
            field_col = 1
        
        # Process each row (skip header)
        for row in table[1:]:
            if len(row) <= max(var_col, field_col) or all(cell is None or str(cell).strip() == "" for cell in row):
                continue
            
            var_num = row[var_col] if var_col < len(row) else None
            field_name = row[field_col] if field_col < len(row) else None
            cip_code = row[cip_col] if cip_col is not None and cip_col < len(row) else None
            
            if var_num is not None and field_name is not None:
                var_num = str(var_num).strip()
                field_name = str(field_name).strip()
                
                # Skip rows that look like headers or are empty
                if not var_num or not field_name or any(keyword in field_name.lower() for keyword in ["field", "academic", "variation", "var"]):
                    continue
                
                # Handle "Default" case
                if var_num.lower() == "default" or field_name.lower() == "default":
                    var_num = "Default"
                    if field_name.lower() == "default":
                        field_name = "Default"
                
                # Use the CIP code if provided, otherwise use the variation number
                data_value = str(cip_code).strip() if cip_code else var_num
                
                # Add level with data
                level_entry = {
                    "value": field_name,
                    "data": data_value
                }
                
                # Check if we already have this level by data (CIP code)
                if not any(level.get("data") == data_value for level in variation_set["levels"][variable_name]):
                    variation_set["levels"][variable_name].append(level_entry)
        
        # Log how many fields we found
        self.logger.info(f"Found {len(variation_set['levels'][variable_name])} academic fields from table")
    
    def _extract_fields_with_codes(self, text, variation_set):
        """Extract academic fields with codes in brackets from text"""
        variable_name = "Academic Field of Interest"
        
        # Look for field names with [CODE] pattern
        # Pattern: Word or phrase followed by code in brackets
        field_matches = re.finditer(r'([A-Za-z][\w\s,&\'"\(\)-]+)\s*\[([A-Z0-9]+)\]', text)
        
        for match in field_matches:
            field_name = match.group(1).strip()
            code = match.group(2).strip()
            
            # Skip if field name too short
            if len(field_name) < 3:
                continue
                
            # Add level with data
            level_entry = {
                "value": field_name,
                "data": code
            }
            
            # Check if we already have this level by data (CIP code)
            if not any(level.get("data") == code for level in variation_set["levels"][variable_name]):
                self.logger.info(f"Found academic field with code in text: {field_name} [{code}]")
                variation_set["levels"][variable_name].append(level_entry)
    
    def _extract_from_text(self, text, variation_set):
        """Extract variation information from text when tables don't provide enough"""
        if not text:
            return
        
        # Extract segments for each variable type
        gpa_segment = self._extract_segment(text, ["gpa", "grade point", "academic performance"])
        distance_segment = self._extract_segment(text, ["distance", "miles", "proximity"])
        academic_segment = self._extract_segment(text, ["academic field", "field of interest", "major", "program"])
        
        # Process each segment if found
        if gpa_segment and "GPA Range" not in variation_set["variables"]:
            self._process_text_segment(gpa_segment, "GPA Range", variation_set)
        elif gpa_segment and len(variation_set["levels"]["GPA Range"]) < 3:
            self._process_text_segment(gpa_segment, "GPA Range", variation_set)
        
        if distance_segment and "Distance" not in variation_set["variables"]:
            self._process_text_segment(distance_segment, "Distance", variation_set)
        elif distance_segment and len(variation_set["levels"]["Distance"]) < 3:
            self._process_text_segment(distance_segment, "Distance", variation_set)
        
        if academic_segment and "Academic Field of Interest" not in variation_set["variables"]:
            self._process_text_segment(academic_segment, "Academic Field of Interest", variation_set)
        elif academic_segment and len(variation_set["levels"]["Academic Field of Interest"]) < 4:
            self._process_text_segment(academic_segment, "Academic Field of Interest", variation_set)
    
    def _extract_segment(self, text, keywords):
        """Extract a segment of text containing keywords"""
        lines = text.split('\n')
        segment_lines = []
        in_segment = False
        
        for line in lines:
            line_lower = line.lower()
            
            # Check if this line indicates the start of a segment
            if any(keyword in line_lower for keyword in keywords):
                in_segment = True
                segment_lines = [line]
            # If we're in a segment, keep adding lines until we hit an empty line
            elif in_segment:
                if line.strip():
                    segment_lines.append(line)
                else:
                    # If we have 2+ lines and hit empty, end segment
                    if len(segment_lines) > 1:
                        break
        
        # Return the segment if found
        return '\n'.join(segment_lines) if segment_lines else ""
    
    def _process_text_segment(self, segment, variable_name, variation_set):
        """Process a text segment to extract variation information"""
        # Add variable if not already there
        if variable_name not in variation_set["variables"]:
            variation_set["variables"].append(variable_name)
            variation_set["levels"][variable_name] = []
        
        # Look for number-value pairs (e.g., "1. 3.3+" or "Variation 2: 26-100 Miles")
        pairs = re.findall(r"(?:var(?:iation)?|level)?\s*(\d+|[Dd]efault)[\s:.-]*([^\n\r]+?)(?=\s*(?:var(?:iation)?|level)?\s*(?:\d+|[Dd]efault)|$)", segment)
        
        for var_num, value in pairs:
            var_num = var_num.strip()
            value = value.strip()
            
            # Skip empty values
            if not value:
                continue
                
            # Standardize "Default"
            if var_num.lower() == "default":
                var_num = "Default"
                if not value or value.lower() == "default":
                    value = "Unknown/Null" if variable_name != "Academic Field of Interest" else "Default"
            
            # Add level with data
            level_entry = {
                "value": value,
                "data": var_num
            }
            
            # Add if not already there
            if not any(level.get("data") == var_num for level in variation_set["levels"][variable_name]):
                variation_set["levels"][variable_name].append(level_entry)
    
    def _verify_and_fix_structure(self, variation_set):
        """Verify the structure of the variation set and fix if needed"""
        # Make sure all required variables are present
        required_variables = ["GPA Range", "Distance", "Academic Field of Interest"]
        for var in required_variables:
            if var not in variation_set["variables"]:
                self.logger.warning(f"Required variable {var} not found, adding default")
                variation_set["variables"].append(var)
                
                if var == "GPA Range":
                    variation_set["levels"][var] = [
                        {"value": "3.5+", "data": "1"},
                        {"value": "3.0-3.49", "data": "2"},
                        {"value": "2.5-2.99", "data": "3"},
                        {"value": "Below 2.5", "data": "4"},
                        {"value": "Unknown/Null", "data": "Default"}
                    ]
                elif var == "Distance":
                    variation_set["levels"][var] = [
                        {"value": "0-50 miles", "data": "1"},
                        {"value": "51-200 miles", "data": "2"},
                        {"value": "201-500 miles", "data": "3"},
                        {"value": "500+ miles", "data": "4"},
                        {"value": "Unknown/Null", "data": "Default"}
                    ]
                elif var == "Academic Field of Interest":
                    variation_set["levels"][var] = [
                        {"value": "Business", "data": "BUS001"},
                        {"value": "Engineering", "data": "ENG002"},
                        {"value": "Arts", "data": "ART003"},
                        {"value": "Science", "data": "SCI004"},
                        {"value": "Default", "data": "Default"}
                    ]
        
        # Ensure each variable has a Default level
        for var in variation_set["variables"]:
            if var not in variation_set["levels"] or not variation_set["levels"][var]:
                continue
                
            has_default = False
            for level in variation_set["levels"][var]:
                if level.get("data") == "Default":
                    has_default = True
                    break
            
            if not has_default:
                default_value = "Unknown/Null" if var != "Academic Field of Interest" else "Default"
                variation_set["levels"][var].append({
                    "value": default_value,
                    "data": "Default"
                })
    
    def _calculate_total_variations(self, variation_set):
        """Calculate the total number of possible variations"""
        total = 1
        for var in variation_set["variables"]:
            if var in variation_set["levels"] and variation_set["levels"][var]:
                total *= len(variation_set["levels"][var])
        return total


class JSONParser:
    """Class for parsing Programs and Clubs JSON data"""
    
    def __init__(self, logger=None):
        self.logger = logger or CLIPSLogger()
        # Add direct logging methods if using the standard logger
        if hasattr(self.logger, 'get_logger'):
            self.logger = self.logger.get_logger()
    
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
            
            # Log stats
            self.logger.info(f"Successfully parsed JSON with {len(indexed_data['by_cip_code'])} CIP codes")
            self.logger.info(f"JSON type: {file_type}")
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