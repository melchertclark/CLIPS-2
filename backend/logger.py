import os
import json
import logging
import datetime
from pathlib import Path
from .config import LOGS_DIR, DEBUG

class CLIPSLogger:
    """Custom logger for CLIPS application"""
    
    def __init__(self, session_id=None):
        self.session_id = session_id or datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.setup_loggers()
        
    def setup_loggers(self):
        """Set up different loggers for various types of logs"""
        # Ensure logs directory exists
        os.makedirs(LOGS_DIR, exist_ok=True)
        
        # Common formatter for console output
        console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # Setup basic logger
        self.logger = logging.getLogger(f"clips.{self.session_id}")
        self.logger.setLevel(logging.DEBUG if DEBUG else logging.INFO)
        
        # Console handler
        console = logging.StreamHandler()
        console.setLevel(logging.DEBUG if DEBUG else logging.INFO)
        console.setFormatter(console_formatter)
        self.logger.addHandler(console)
        
        # File handler for general logs
        general_log_file = os.path.join(LOGS_DIR, f"{self.session_id}_general.log")
        file_handler = logging.FileHandler(general_log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(console_formatter)
        self.logger.addHandler(file_handler)
        
        # Set up specialized loggers
        self._setup_specialized_logger("interaction", "interaction")
        self._setup_specialized_logger("ai", "ai")
        self._setup_specialized_logger("output", "output")
        
    def _setup_specialized_logger(self, logger_name, file_prefix):
        """Set up a specialized logger that writes to both console and a specific file"""
        specialized_logger = logging.getLogger(f"clips.{self.session_id}.{logger_name}")
        specialized_logger.setLevel(logging.DEBUG)
        
        # File handler
        log_file = os.path.join(LOGS_DIR, f"{self.session_id}_{file_prefix}.log")
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
        specialized_logger.addHandler(file_handler)
        
        # Set the attribute dynamically
        setattr(self, f"{logger_name}_logger", specialized_logger)
    
    def log_interaction(self, action, details=None):
        """Log user interactions"""
        log_entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "action": action,
            "details": details or {}
        }
        self.interaction_logger.info(json.dumps(log_entry))
        if DEBUG:
            self.logger.debug(f"Interaction: {action}")
        
    def log_ai_interaction(self, endpoint, prompt, response, model=None, error=None):
        """Log AI API interactions"""
        log_entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "endpoint": endpoint,
            "model": model,
            "prompt": prompt,
            "response": response,
            "error": error
        }
        self.ai_logger.info(json.dumps(log_entry))
        if DEBUG:
            self.logger.debug(f"AI Interaction: {endpoint} - {'Success' if not error else 'Error'}")
        
    def log_output(self, filename, content, variation_levels=None):
        """Log information about generated output files"""
        log_entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "filename": filename,
            "file_size": len(content) if content else 0,
            "variation_levels": variation_levels or {}
        }
        self.output_logger.info(json.dumps(log_entry))
        if DEBUG:
            self.logger.debug(f"Output: Generated {filename}")
    
    def log_missing_json_data(self, cip_code, variation_levels):
        """Log when JSON data is missing for a specific CIP code during variation generation"""
        log_entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "cip_code": cip_code,
            "variation_levels": variation_levels
        }
        self.logger.warning(f"Missing JSON data for CIP code {cip_code} in variation {json.dumps(variation_levels)}")
        self.ai_logger.warning(json.dumps({"type": "missing_json_data", **log_entry}))
    
    def log_instruction_update(self, category, old_value, new_value, source="user"):
        """Log updates to instruction set"""
        log_entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "category": category,
            "source": source,  # 'user' or 'ai_feedback'
            "old_value": old_value,
            "new_value": new_value
        }
        self.interaction_logger.info(json.dumps({"type": "instruction_update", **log_entry}))
        if DEBUG:
            self.logger.debug(f"Instruction update: {category} by {source}")
    
    def log_error(self, message, context=None, exception=None):
        """Log errors"""
        if exception:
            self.logger.exception(message)
        else:
            self.logger.error(message)
            
        # Also log to the AI logger if it's an API error
        if context and context.get("type") == "api_error":
            log_entry = {
                "timestamp": datetime.datetime.now().isoformat(),
                "message": message,
                "context": context,
                "exception": str(exception) if exception else None
            }
            self.ai_logger.error(json.dumps({"type": "error", **log_entry}))
    
    def get_logger(self):
        """Return the main logger"""
        return self.logger
