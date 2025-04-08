import os
import sys
import json
import random
import datetime
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import re

# Add parent directory to path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.config import ensure_directories, get_app_settings, save_openai_api_key
from backend.logger import CLIPSLogger
from backend.parsing import PDFParser, JSONParser
from backend.ai_integration import AIIntegration
from backend.session_manager import SessionManager
from backend.output_generator import OutputGenerator

# Initialize Flask app
app = Flask(__name__)

# Enable CORS for all routes with explicit settings
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

# Add CORS headers to all responses
@app.after_request
def add_cors_headers(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,X-Requested-With')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS,PATCH')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    # Handle preflight requests
    if request.method == 'OPTIONS':
        response.status_code = 200
    return response

# Add OPTIONS handler for all routes
@app.route('/', defaults={'path': ''}, methods=['OPTIONS'])
@app.route('/<path:path>', methods=['OPTIONS'])
def options_handler(path):
    return Response('', 200)

# Initialize components
ensure_directories()
logger = CLIPSLogger()
app_logger = logger.get_logger()
app_logger.info("Starting CLIPS backend")

session_manager = SessionManager(logger)
pdf_parser = PDFParser(logger)
json_parser = JSONParser(logger)
ai_integration = AIIntegration(logger)
output_generator = OutputGenerator(ai_integration, logger)

# Current session state
current_session = session_manager.create_empty_session()

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get the application status and settings"""
    return jsonify({
        "status": "ok",
        "settings": get_app_settings()
    })

@app.route('/api/openai/setup', methods=['POST'])
def setup_openai():
    """Set up OpenAI API key"""
    data = request.json
    api_key = data.get('api_key')
    
    if not api_key:
        return jsonify({"error": "API key is required"}), 400
    
    # Save the API key
    if save_openai_api_key(api_key):
        # Initialize AI integration with new key
        if ai_integration.initialize_client(api_key):
            logger.log_interaction("setup_openai_api", {"success": True})
            return jsonify({"success": True})
        else:
            return jsonify({"error": "Failed to initialize OpenAI client with provided key"}), 400
    else:
        return jsonify({"error": "Failed to save API key"}), 500

@app.route('/api/session/new', methods=['POST'])
def new_session():
    """Create a new session"""
    global current_session
    current_session = session_manager.create_empty_session()
    logger.log_interaction("new_session")
    return jsonify({"success": True, "session": current_session})

@app.route('/api/session/save', methods=['POST'])
def save_session():
    """Save the current session"""
    global current_session
    
    try:
        filepath = session_manager.save_session(current_session)
        return jsonify({"success": True, "filepath": filepath})
    except Exception as e:
        app_logger.exception("Failed to save session")
        return jsonify({"error": str(e)}), 500

@app.route('/api/session/save_as', methods=['POST'])
def save_session_as():
    """Save the current session to a new file"""
    global current_session
    data = request.json
    filepath = data.get('filepath')
    
    if not filepath:
        return jsonify({"error": "Filepath is required"}), 400
    
    try:
        filepath = session_manager.save_session_as(current_session, filepath)
        return jsonify({"success": True, "filepath": filepath})
    except Exception as e:
        app_logger.exception("Failed to save session as new file")
        return jsonify({"error": str(e)}), 500

@app.route('/api/session/load', methods=['POST'])
def load_session():
    """Load a session from a file"""
    global current_session
    data = request.json
    filepath = data.get('filepath')
    
    if not filepath:
        return jsonify({"error": "Filepath is required"}), 400
    
    try:
        current_session = session_manager.load_session(filepath)
        return jsonify({"success": True, "session": current_session})
    except Exception as e:
        app_logger.exception("Failed to load session")
        return jsonify({"error": str(e)}), 500

@app.route('/api/session/recent', methods=['GET'])
def get_recent_sessions():
    """Get a list of recent sessions"""
    try:
        recent_sessions = session_manager.get_recent_sessions()
        return jsonify({"success": True, "sessions": recent_sessions})
    except Exception as e:
        app_logger.exception("Failed to get recent sessions")
        return jsonify({"error": str(e)}), 500

@app.route('/api/session/current', methods=['GET'])
def get_current_session():
    """Get the current session state"""
    global current_session
    return jsonify({"success": True, "session": current_session})

@app.route('/api/parse/pdf', methods=['POST'])
def parse_pdf():
    """Parse a PDF file to extract variation variables and levels"""
    global current_session
    
    app_logger.info(f"PDF parse request received: {request.method} {request.path}")
    app_logger.info(f"Request headers: {request.headers}")
    app_logger.info(f"Request files: {request.files}")
    
    if 'file' not in request.files:
        app_logger.warning("No file found in request.files")
        return jsonify({"error": "No file provided"}), 400
    
    pdf_file = request.files['file']
    if pdf_file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    # Log file details
    app_logger.info(f"Received file: {pdf_file.filename}, size: {pdf_file.content_length}")
    
    # Save the uploaded file temporarily
    temp_filepath = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                              "temp_uploads", pdf_file.filename)
    os.makedirs(os.path.dirname(temp_filepath), exist_ok=True)
    
    try:
        pdf_file.save(temp_filepath)
        file_size = os.path.getsize(temp_filepath)
        app_logger.info(f"File saved to {temp_filepath}, size: {file_size} bytes")
        logger.log_interaction("upload_pdf", {"filename": pdf_file.filename, "size": file_size})
        
        # Parse the PDF
        variation_set = pdf_parser.parse_variation_pdf(temp_filepath)
        
        # Update session state
        current_session["instruction_set"]["variation_list_data"] = variation_set
        
        # Save the session
        session_manager.save_session(current_session)
        
        # Return the parsed data
        return jsonify({"success": True, "variation_set": variation_set})
    except Exception as e:
        app_logger.exception(f"Failed to parse PDF: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_filepath):
            app_logger.info(f"Removing temporary file: {temp_filepath}")
            os.remove(temp_filepath)

@app.route('/api/parse/json', methods=['POST'])
def parse_json():
    """Parse a JSON file to extract program or club data"""
    global current_session
    
    app_logger.info(f"JSON parse request received: {request.method} {request.path}")
    app_logger.info(f"Request headers: {request.headers}")
    app_logger.info(f"Request files: {request.files}")
    
    if 'file' not in request.files:
        app_logger.warning("No file found in request.files")
        return jsonify({"error": "No file provided"}), 400
    
    json_file = request.files['file']
    if json_file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    # Log file details
    app_logger.info(f"Received JSON file: {json_file.filename}, size: {json_file.content_length}")
    
    # Save the uploaded file temporarily
    temp_filepath = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                              "temp_uploads", json_file.filename)
    os.makedirs(os.path.dirname(temp_filepath), exist_ok=True)
    
    try:
        json_file.save(temp_filepath)
        file_size = os.path.getsize(temp_filepath)
        app_logger.info(f"JSON file saved to {temp_filepath}, size: {file_size} bytes")
        logger.log_interaction("upload_json", {"filename": json_file.filename, "size": file_size})
        
        # Parse the JSON
        indexed_data = json_parser.parse_json_file(temp_filepath)
        app_logger.info(f"JSON parsed successfully: {len(indexed_data.get('by_cip_code', {}))} CIP codes found")
        
        # Update session state based on data type
        data_type = indexed_data.get("type", "unknown")
        if data_type == "programs" or "program" in json_file.filename.lower():
            # Clear any existing programs data first
            current_session["imported_data"]["programs"] = indexed_data
            # Make sure clubs data is not falsely shown if not loaded
            if not current_session["imported_data"]["clubs"]:
                current_session["imported_data"]["clubs"] = None
            app_logger.info(f"Identified as programs data")
        elif data_type == "clubs" or "club" in json_file.filename.lower():
            # Clear any existing clubs data first
            current_session["imported_data"]["clubs"] = indexed_data
            # Make sure programs data is not falsely shown if not loaded
            if not current_session["imported_data"]["programs"]:
                current_session["imported_data"]["programs"] = None
            app_logger.info(f"Identified as clubs data")
        else:
            # Ask user which type this is?
            app_logger.info(f"Unable to determine data type, requesting user selection")
            return jsonify({
                "success": True, 
                "indexed_data": indexed_data,
                "requires_type_selection": True
            })
        
        # Save the session
        session_manager.save_session(current_session)
        
        # Return the parsed data
        return jsonify({"success": True, "indexed_data": indexed_data})
    except Exception as e:
        app_logger.exception(f"Failed to parse JSON: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_filepath):
            app_logger.info(f"Removing temporary JSON file: {temp_filepath}")
            os.remove(temp_filepath)

@app.route('/api/json/set_type', methods=['POST'])
def set_json_type():
    """Set the type of a previously uploaded JSON file"""
    global current_session
    data = request.json
    indexed_data = data.get('indexed_data')
    data_type = data.get('data_type')
    
    if not indexed_data or not data_type:
        return jsonify({"error": "Both indexed_data and data_type are required"}), 400
    
    try:
        # Update the data type
        indexed_data["type"] = data_type
        
        # Update session state
        if data_type == "programs":
            current_session["imported_data"]["programs"] = indexed_data
            # Ensure clubs data is null if not present to prevent display issues
            if not current_session["imported_data"].get("clubs"):
                current_session["imported_data"]["clubs"] = None
        elif data_type == "clubs":
            current_session["imported_data"]["clubs"] = indexed_data
            # Ensure programs data is null if not present to prevent display issues
            if not current_session["imported_data"].get("programs"):
                current_session["imported_data"]["programs"] = None
        
        # Save the session
        session_manager.save_session(current_session)
        
        return jsonify({"success": True})
    except Exception as e:
        app_logger.exception("Failed to set JSON type")
        return jsonify({"error": str(e)}), 500

@app.route('/api/instructions/update', methods=['POST'])
def update_instructions():
    """Update an instruction category"""
    global current_session
    data = request.json
    category = data.get('category')
    value = data.get('value')
    
    if not category:
        return jsonify({"error": "Category is required"}), 400
    
    try:
        # Get old value for logging
        old_value = current_session["instruction_set"].get(category, "")
        
        # Update the instruction
        current_session["instruction_set"][category] = value
        
        # If updating variation_application_instructions, distill them
        if category == "variation_application_instructions" and value:
            distilled = ai_integration.distill_variation_instructions(value)
            current_session["instruction_set"]["distilled_variation_instructions"] = distilled
        
        # Log the change
        logger.log_instruction_update(category, old_value, value)
        
        # Save the session
        session_manager.save_session(current_session)
        
        return jsonify({
            "success": True, 
            "distilled": current_session["instruction_set"].get("distilled_variation_instructions", "") \
                if category == "variation_application_instructions" else None
        })
    except Exception as e:
        app_logger.exception("Failed to update instructions")
        return jsonify({"error": str(e)}), 500

@app.route('/api/copy/update', methods=['POST'])
def update_original_copy():
    """Update the original copy template"""
    global current_session
    data = request.json
    copy_text = data.get('copy_text')
    
    if copy_text is None:  # Allow empty string as valid input
        return jsonify({"error": "copy_text is required"}), 400
    
    try:
        # Update the original copy
        current_session["original_copy"] = copy_text
        
        # Log the change
        logger.log_interaction("update_original_copy")
        
        # Analyze for markers if text is not empty
        markers = []
        if copy_text:
            # Find all markers in the format {{MARKER_NAME}}
            marker_pattern = r'\{\{([^\}]+)\}\}'
            matches = re.finditer(marker_pattern, copy_text)
            markers = [match.group(1) for match in matches]
        
        # Save the session
        session_manager.save_session(current_session)
        
        return jsonify({"success": True, "markers": markers})
    except Exception as e:
        app_logger.exception("Failed to update original copy")
        return jsonify({"error": str(e)}), 500

@app.route('/api/draft/generate', methods=['POST'])
def generate_draft():
    """Generate a draft using the current instructions and variation levels"""
    global current_session
    data = request.json
    variation_type = data.get('variation_type', 'default')  # 'default' or 'random'
    
    try:
        # Check if we have necessary components
        if not current_session["original_copy"]:
            return jsonify({"error": "Original copy is required"}), 400
        
        # Determine variation levels to use
        variation_levels = {}
        variation_set = current_session["instruction_set"].get("variation_list_data", {})
        
        if variation_type == 'random' and variation_set and variation_set.get("variables") and variation_set.get("levels"):
            # Select random levels for each variable
            for var in variation_set["variables"]:
                if var in variation_set["levels"] and variation_set["levels"][var]:
                    # Choose a random level for this variable
                    random_level = random.choice(variation_set["levels"][var])
                    level_value = random_level.get("value")
                    
                    variation_levels[var] = level_value
                    
                    # If this level has associated data (like CIP code), include it
                    if "data" in random_level:
                        variation_levels[var] = {
                            "value": level_value,
                            "data": random_level["data"]
                        }
        
        # Store current variation levels
        current_session["current_variation_levels"] = variation_levels
        
        # Prepare imported data
        json_data = {
            "programs": current_session["imported_data"].get("programs"),
            "clubs": current_session["imported_data"].get("clubs")
        }
        
        # Generate the draft
        draft = ai_integration.generate_draft(
            current_session["original_copy"],
            current_session["instruction_set"],
            variation_levels,
            json_data
        )
        
        # Update the current draft
        current_session["current_draft"] = draft
        
        # Save the session
        session_manager.save_session(current_session)
        
        return jsonify({
            "success": True, 
            "draft": draft,
            "variation_levels": variation_levels
        })
    except Exception as e:
        app_logger.exception("Failed to generate draft")
        return jsonify({"error": str(e)}), 500

@app.route('/api/feedback/process', methods=['POST'])
def process_feedback():
    """Process feedback and update instructions accordingly"""
    global current_session
    data = request.json
    feedback = data.get('feedback')
    
    if not feedback:
        return jsonify({"error": "Feedback is required"}), 400
    
    try:
        # Check if we have necessary components
        if not current_session["original_copy"] or not current_session["current_draft"]:
            return jsonify({"error": "Both original copy and a current draft are required"}), 400
        
        # Log the feedback
        logger.log_interaction("submit_feedback", {"feedback": feedback})
        
        # Interpret the feedback
        instruction_updates = ai_integration.interpret_feedback(
            current_session["original_copy"],
            current_session["current_draft"],
            feedback,
            current_session["instruction_set"]
        )
        
        # If no updates were identified, return error
        if not instruction_updates:
            return jsonify({"error": "Could not interpret feedback into specific instruction updates"}), 400
        
        # Apply the updates
        for category, new_value in instruction_updates.items():
            if category in current_session["instruction_set"]:
                old_value = current_session["instruction_set"][category]
                current_session["instruction_set"][category] = new_value
                logger.log_instruction_update(category, old_value, new_value, "ai_feedback")
        
        # Save the session
        session_manager.save_session(current_session)
        
        # Generate a new draft with the updated instructions
        # Re-use the current variation levels
        variation_levels = current_session["current_variation_levels"]
        
        # Prepare imported data
        json_data = {
            "programs": current_session["imported_data"].get("programs"),
            "clubs": current_session["imported_data"].get("clubs")
        }
        
        # Generate the draft
        draft = ai_integration.generate_draft(
            current_session["original_copy"],
            current_session["instruction_set"],
            variation_levels,
            json_data
        )
        
        # Update the current draft
        current_session["current_draft"] = draft
        
        # Save the session again
        session_manager.save_session(current_session)
        
        return jsonify({
            "success": True, 
            "draft": draft,
            "instruction_updates": instruction_updates
        })
    except Exception as e:
        app_logger.exception("Failed to process feedback")
        return jsonify({"error": str(e)}), 500

@app.route('/api/variations/preview_samples', methods=['POST'])
def preview_sample_variations():
    """Generate a few sample variations to preview"""
    global current_session
    
    try:
        # Check if we have necessary components
        if not current_session["original_copy"]:
            return jsonify({"error": "Original copy is required"}), 400
            
        if not current_session["instruction_set"].get("variation_list_data") or \
           not current_session["instruction_set"]["variation_list_data"].get("variables"):
            return jsonify({"error": "Variation definition data is required"}), 400
        
        # Log the action
        logger.log_interaction("preview_sample_variations")
        
        # Prepare imported data
        json_data = {
            "programs": current_session["imported_data"].get("programs"),
            "clubs": current_session["imported_data"].get("clubs")
        }
        
        # Get variation data
        variation_set = current_session["instruction_set"]["variation_list_data"]
        variables = variation_set.get("variables", [])
        levels = variation_set.get("levels", {})
        
        # Generate a few diverse sample variations
        samples = []
        max_samples = 3  # Number of samples to generate
        
        # Create different combinations of levels
        # We'll use a few strategies to get diverse samples:
        # 1. Default values for all variables
        # 2. Random representative values
        # 3. Edge case values (high/low)
        
        # Sample 1: Default values where possible
        default_levels = {}
        for var in variables:
            if var in levels and levels[var]:
                # Look for a level with 'Default' value
                default_level = next((level for level in levels[var] if level.get("value", "").lower() == "default"), None)
                if not default_level:
                    # If no "Default" level, use the first one
                    default_level = levels[var][0]
                
                # Format the level properly
                level_value = default_level.get("value")
                level_data = {
                    "value": level_value
                }
                
                # Add data field if present (like CIP code)
                if "data" in default_level:
                    level_data["data"] = default_level["data"]
                    
                default_levels[var] = level_data
                
        # Sample 2: Mid-range values
        mid_levels = {}
        for var in variables:
            if var in levels and levels[var]:
                # Get middle level
                mid_idx = len(levels[var]) // 2
                mid_level = levels[var][mid_idx]
                
                # Format the level properly
                level_value = mid_level.get("value")
                level_data = {
                    "value": level_value
                }
                
                # Add data field if present
                if "data" in mid_level:
                    level_data["data"] = mid_level["data"]
                    
                mid_levels[var] = level_data
                
        # Sample 3: High values or distinct values
        high_levels = {}
        for var in variables:
            if var in levels and levels[var]:
                # For GPA, use highest value
                if "gpa" in var.lower():
                    high_level = levels[var][-1]  # Highest GPA
                # For distance, use furthest or closest depending on what's available
                elif "distance" in var.lower():
                    # Check if we have "out of state" or high distance values
                    out_state = next((level for level in levels[var] if "out" in level.get("value", "").lower()), None)
                    if out_state:
                        high_level = out_state
                    else:
                        high_level = levels[var][-1]  # Furthest distance
                # For academic field, use something different from the default
                elif "academic" in var.lower() or "field" in var.lower():
                    # Try to find a STEM field if possible
                    stem_field = next((level for level in levels[var] if any(stem in level.get("value", "").lower() 
                                                                     for stem in ["science", "engineering", "math", "computer", "technology"])), None)
                    if stem_field:
                        high_level = stem_field
                    else:
                        # Just pick one different from default
                        high_level = levels[var][min(2, len(levels[var])-1)]
                else:
                    # For other variables, use last value
                    high_level = levels[var][-1]
                
                # Format the level properly
                level_value = high_level.get("value")
                level_data = {
                    "value": level_value
                }
                
                # Add data field if present
                if "data" in high_level:
                    level_data["data"] = high_level["data"]
                    
                high_levels[var] = level_data
        
        # Generate the samples
        sample_variations = [default_levels, mid_levels, high_levels]
        
        for i, variation_levels in enumerate(sample_variations):
            try:
                # Generate the content
                content = ai_integration.generate_draft(
                    current_session["original_copy"],
                    current_session["instruction_set"],
                    variation_levels,
                    json_data
                )
                
                samples.append({
                    "id": i + 1,
                    "levels": variation_levels,
                    "content": content
                })
                
                # If we have enough samples, stop
                if len(samples) >= max_samples:
                    break
                    
            except Exception as e:
                app_logger.warning(f"Failed to generate sample {i+1}: {str(e)}")
                continue
        
        return jsonify({
            "success": True,
            "samples": samples
        })
    except Exception as e:
        app_logger.exception("Failed to preview sample variations")
        return jsonify({"error": str(e)}), 500

@app.route('/api/variations/generate_all', methods=['POST'])
def generate_all_variations():
    """Generate all possible variations"""
    global current_session
    
    try:
        # Check if we have necessary components
        if not current_session["original_copy"]:
            return jsonify({"error": "Original copy is required"}), 400
            
        if not current_session["instruction_set"].get("variation_list_data") or \
           not current_session["instruction_set"]["variation_list_data"].get("variables"):
            return jsonify({"error": "Variation definition data is required"}), 400
        
        # Log the action
        logger.log_interaction("generate_all_variations")
        
        # Prepare imported data
        json_data = {
            "programs": current_session["imported_data"].get("programs"),
            "clubs": current_session["imported_data"].get("clubs")
        }
        
        # Generate all variations
        results = output_generator.generate_all_variations(
            current_session["original_copy"],
            current_session["instruction_set"],
            current_session["instruction_set"]["variation_list_data"],
            json_data
        )
        
        # Save the session
        session_manager.save_session(current_session)
        
        return jsonify({
            "success": True, 
            "results": results
        })
    except Exception as e:
        app_logger.exception("Failed to generate all variations")
        return jsonify({"error": str(e)}), 500

def find_available_port(start_port=3000, max_attempts=100):
    """Find an available port to use for the server"""
    import socket
    
    for port in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            in_use = s.connect_ex(('localhost', port)) == 0
            if not in_use:
                return port
    
    # If we get here, we couldn't find a free port
    raise RuntimeError(f"Could not find an available port after {max_attempts} attempts")

if __name__ == '__main__':
    # Determine port from command line or use default
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    else:
        # Find an available port starting from 3000
        port = find_available_port(3000)
    
    # Create temp directory if it doesn't exist
    os.makedirs(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "temp_uploads"), exist_ok=True)
    
    # Print startup message
    print(f"Starting CLIPS backend server...")
    print(f"Creating required directories...")
    
    # Start the server
    print(f"Running on http://0.0.0.0:{port} (accessible via 127.0.0.1)")
    
    # Open status file with port information
    status_file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend_port.txt")
    with open(status_file_path, 'w') as f:
        f.write(str(port))
    print(f"Port information saved to {status_file_path}")
    
    # Run without debug mode to prevent automatic reloading
    # Use 0.0.0.0 to bind to all available interfaces
    app.run(host='0.0.0.0', port=port, debug=False)