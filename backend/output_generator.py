import os
import json
import datetime
from pathlib import Path
import itertools
from .config import OUTPUT_DIR
from .logger import CLIPSLogger

class OutputGenerator:
    """Class to handle generation of final variations and formatting output"""
    
    def __init__(self, ai_integration, logger=None):
        self.logger = logger or CLIPSLogger()
        self.ai_integration = ai_integration
        
        # Ensure output directory exists
        os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    def generate_all_variations(self, original_copy, instruction_set, variation_set, json_data):
        """Generate all possible variations based on the Cartesian product of variation levels"""
        # Initialize counters
        results = {
            "total": 0,
            "success": 0,
            "failure": 0,
            "missing_data": 0,
            "variations": []
        }
        
        # Get all variables and their levels
        variables = variation_set.get("variables", [])
        levels = variation_set.get("levels", {})
        
        if not variables or not levels:
            self.logger.log_error("Cannot generate variations: No variation variables or levels defined")
            return results
        
        # Generate all possible combinations of levels
        level_values = []
        level_names = []
        
        for var in variables:
            if var in levels and levels[var]:
                level_values.append(levels[var])
                level_names.append(var)
        
        # Get all combinations (Cartesian product)
        combinations = list(itertools.product(*level_values))
        results["total"] = len(combinations)
        
        # Generate each variation
        for i, combo in enumerate(combinations):
            # Create the specific variation levels for this combination
            variation_levels = {}
            for j, level_obj in enumerate(combo):
                var_name = level_names[j]
                variation_levels[var_name] = level_obj
            
            # Check for missing JSON data if needed
            missing_data = False
            field_of_interest_var = next((var for var in level_names if var.lower() in ['field of interest', 'program', 'major']), None)
            
            if field_of_interest_var and variation_levels.get(field_of_interest_var, {}).get("data"):
                cip_code = variation_levels[field_of_interest_var]["data"]
                program_data = json_data.get('programs', {}).get('by_cip_code', {}).get(cip_code, [])
                club_data = json_data.get('clubs', {}).get('by_cip_code', {}).get(cip_code, [])
                
                if not program_data and not club_data:
                    missing_data = True
                    results["missing_data"] += 1
                    self.logger.log_missing_json_data(cip_code, variation_levels)
            
            # Generate the variation
            try:
                # Prepare a simplified version of variation_levels for the AI prompt
                simple_variation_levels = {}
                for var_name, level_obj in variation_levels.items():
                    simple_variation_levels[var_name] = level_obj.get("value")
                    if level_obj.get("data"):
                        simple_variation_levels[var_name] = {
                            "value": level_obj.get("value"),
                            "data": level_obj.get("data")
                        }
                
                # Generate draft
                variation_content = self.ai_integration.generate_draft(
                    original_copy, 
                    instruction_set, 
                    simple_variation_levels, 
                    json_data
                )
                
                # Format as Markdown
                markdown_content = self._format_as_markdown(variation_content, simple_variation_levels)
                
                # Create filename
                filename = self._create_variation_filename(instruction_set.get("partner_name", ""), simple_variation_levels)
                
                # Save the file
                filepath = os.path.join(OUTPUT_DIR, filename)
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(markdown_content)
                
                # Log the output
                self.logger.log_output(filename, markdown_content, simple_variation_levels)
                
                # Update counters
                results["success"] += 1
                results["variations"].append({
                    "filename": filename,
                    "filepath": filepath,
                    "levels": simple_variation_levels,
                    "missing_data": missing_data
                })
                
            except Exception as e:
                results["failure"] += 1
                self.logger.log_error(f"Failed to generate variation {i+1}/{len(combinations)}", 
                                    {"variation_levels": simple_variation_levels}, e)
        
        return results
    
    def _format_as_markdown(self, content, variation_levels):
        """Format the generated content as Markdown with metadata"""
        # Create the frontmatter
        frontmatter = [
            "---",
            "title: Generated Copy Variation",
            f"date: {datetime.datetime.now().isoformat()}",
            "variations:"  
        ]
        
        # Add variation levels to frontmatter
        for var, level in variation_levels.items():
            if isinstance(level, dict):
                frontmatter.append(f"  {var}: {level['value']}")
            else:
                frontmatter.append(f"  {var}: {level}")
        
        frontmatter.append("---\n")
        
        # Combine frontmatter and content
        markdown = "\n".join(frontmatter) + content
        
        return markdown
    
    def _create_variation_filename(self, partner_name, variation_levels):
        """Create a filename for the variation based on its levels"""
        # Clean the partner name for use in filename
        if partner_name:
            clean_partner = partner_name.replace(" ", "_").replace("/", "-").replace("\\", "-")
            base_name = f"{clean_partner}_"
        else:
            base_name = "Variation_"
        
        # Add variation levels
        level_parts = []
        for var, level in variation_levels.items():
            level_value = level['value'] if isinstance(level, dict) else level
            # Clean level value for filename
            clean_level = level_value.replace(" ", "_").replace("/", "-").replace("\\", "-").\
                          replace(".", "p").replace("+", "plus").replace("<", "lt").replace(">", "gt")
            level_parts.append(f"{var[:3]}_{clean_level[:10]}")
        
        # Add timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Combine all parts
        filename = f"{base_name}{'_'.join(level_parts)}_{timestamp}.md"
        
        return filename
