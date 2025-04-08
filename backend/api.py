import os
import json
from flask import Flask, request, jsonify
from .parsing import PDFParser
from .logger import CLIPSLogger

app = Flask(__name__)
logger = CLIPSLogger().get_logger()
parser = PDFParser(logger)

@app.route('/api/parse', methods=['POST'])
def parse_variation_pdf():
    """API endpoint to parse PDF from URL or base64 data"""
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Get PDF source (URL or file path)
        pdf_source = data.get('pdf_url') or data.get('pdf_path')
        if not pdf_source:
            return jsonify({"error": "No PDF source provided"}), 400
            
        # Get optional format type hint
        format_type = data.get('format_type')
        
        # Process PDF
        variation_set = parser.parse_variation_pdf(pdf_source, format_type)
        
        # Apply field updates if provided
        field_updates = data.get('field_updates', [])
        if field_updates:
            variation_set = parser.update_field_values(variation_set, field_updates)
        
        # Add fields if provided
        new_fields = data.get('new_fields', [])
        for field in new_fields:
            var_name = field.get('variable')
            value = field.get('value')
            data_id = field.get('data')
            
            if var_name and value:
                variation_set = parser.add_field_value(variation_set, var_name, value, data_id)
        
        return jsonify(variation_set)
    
    except Exception as e:
        logger.error(f"API error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/update', methods=['POST'])
def update_variation_set():
    """API endpoint to update fields in an existing variation set"""
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Get variation set and updates
        variation_set = data.get('variation_set')
        field_updates = data.get('field_updates', [])
        
        if not variation_set:
            return jsonify({"error": "No variation set provided"}), 400
        if not field_updates:
            return jsonify({"error": "No field updates provided"}), 400
            
        # Apply updates
        updated_set = parser.update_field_values(variation_set, field_updates)
        
        return jsonify(updated_set)
    
    except Exception as e:
        logger.error(f"API error: {str(e)}")
        return jsonify({"error": str(e)}), 500
        
@app.route('/api/add_field', methods=['POST'])
def add_field():
    """API endpoint to add a new field to a variable"""
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Get required data
        variation_set = data.get('variation_set')
        variable = data.get('variable')
        value = data.get('value')
        data_id = data.get('data')
        
        if not variation_set or not variable or not value:
            return jsonify({"error": "Missing required fields"}), 400
            
        # Add new field
        updated_set = parser.add_field_value(variation_set, variable, value, data_id)
        
        return jsonify(updated_set)
    
    except Exception as e:
        logger.error(f"API error: {str(e)}")
        return jsonify({"error": str(e)}), 500

def run_api(host='0.0.0.0', port=5000, debug=False):
    """Run the API server"""
    app.run(host=host, port=port, debug=debug)

if __name__ == '__main__':
    run_api(debug=True)