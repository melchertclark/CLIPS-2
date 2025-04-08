import os
import json
import datetime
from pathlib import Path
from .config import SESSIONS_DIR
from .logger import CLIPSLogger

class SessionManager:
    """Class to handle saving and loading session state"""
    
    def __init__(self, logger=None):
        self.logger = logger or CLIPSLogger()
        self.session_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_file = None
        
        # Ensure sessions directory exists
        os.makedirs(SESSIONS_DIR, exist_ok=True)
    
    def create_empty_session(self):
        """Create an empty session with default values"""
        return {
            "session_id": self.session_id,
            "created_at": datetime.datetime.now().isoformat(),
            "updated_at": datetime.datetime.now().isoformat(),
            "original_copy": "",
            "instruction_set": {
                "partner_name": "",
                "variation_list_data": {},
                "variation_application_instructions": "",
                "distilled_variation_instructions": "",
                "marker_instructions": "",
                "tone_other_prompts": ""
            },
            "imported_data": {
                "programs": None,
                "clubs": None
            },
            "current_draft": "",
            "current_variation_levels": {}
        }
    
    def save_session(self, session_data, filepath=None):
        """Save the current session state to a file"""
        try:
            # Update timestamp
            session_data["updated_at"] = datetime.datetime.now().isoformat()
            
            # Use provided filepath or generate one
            if not filepath:
                if self.session_file:
                    filepath = self.session_file
                else:
                    filename = f"clips_session_{self.session_id}.json"
                    filepath = os.path.join(SESSIONS_DIR, filename)
            
            # Save file
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2)
            
            self.session_file = filepath
            self.logger.log_interaction("save_session", {"filepath": filepath})
            return filepath
            
        except Exception as e:
            self.logger.log_error(f"Failed to save session: {str(e)}", 
                                {"filepath": filepath})
            raise
    
    def save_session_as(self, session_data, filepath):
        """Save the current session state to a new file"""
        # Update session ID based on new filename
        filename = os.path.basename(filepath)
        if filename.startswith("clips_session_") and filename.endswith(".json"):
            new_session_id = filename[14:-5]  # Extract ID from filename
            session_data["session_id"] = new_session_id
            self.session_id = new_session_id
        
        return self.save_session(session_data, filepath)
    
    def load_session(self, filepath):
        """Load a session state from a file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            # Update session ID and file
            self.session_id = session_data.get("session_id", self.session_id)
            self.session_file = filepath
            
            self.logger.log_interaction("load_session", {"filepath": filepath})
            return session_data
            
        except Exception as e:
            self.logger.log_error(f"Failed to load session: {str(e)}", 
                                {"filepath": filepath})
            raise
    
    def get_recent_sessions(self, limit=5):
        """Get a list of recent session files"""
        try:
            sessions = []
            
            # List all session files
            for filename in os.listdir(SESSIONS_DIR):
                if filename.startswith("clips_session_") and filename.endswith(".json"):
                    filepath = os.path.join(SESSIONS_DIR, filename)
                    modified_time = os.path.getmtime(filepath)
                    
                    # Try to extract session name/title
                    session_name = filename[14:-5]  # Default to ID in filename
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            partner_name = data.get("instruction_set", {}).get("partner_name", "")
                            if partner_name:
                                session_name = f"{partner_name} ({session_name})"
                    except:
                        pass
                    
                    sessions.append({
                        "filepath": filepath,
                        "filename": filename,
                        "session_name": session_name,
                        "modified": datetime.datetime.fromtimestamp(modified_time).isoformat()
                    })
            
            # Sort by modified time (newest first) and limit
            sessions.sort(key=lambda x: x["modified"], reverse=True)
            return sessions[:limit]
            
        except Exception as e:
            self.logger.log_error(f"Failed to get recent sessions: {str(e)}")
            return []
