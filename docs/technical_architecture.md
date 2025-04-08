# CLIPS-2 Technical Architecture

## System Overview

CLIPS-2 (Copywriter's Lightweight Iteration Pipeline System) is a desktop application designed to streamline the generation of personalized marketing copy for college enrollment campaigns. The system combines PDF parsing capabilities, structured data management, and AI-powered content generation to create variations of marketing copy tailored to specific student segments.

## Architecture Diagram

```
┌─────────────────────────┐                 ┌──────────────────────┐
│    Electron Frontend    │◄────────────────►│    Python Backend    │
│  (HTML/CSS/JavaScript)  │     JSON API     │    (Flask Server)    │
└───────────┬─────────────┘                 └──────────┬───────────┘
            │                                          │
            │                                          │
            ▼                                          ▼
┌─────────────────────────┐                 ┌──────────────────────┐
│    UI Components        │                 │   Service Modules     │
│  - Instruction Panel    │                 │  - PDF Parser         │
│  - Workflow Panel       │                 │  - JSON Parser        │
│  - Variable Editor      │                 │  - Session Manager    │
└───────────┬─────────────┘                 │  - Output Generator   │
            │                               └──────────┬───────────┘
            │                                          │
            ▼                                          ▼
┌─────────────────────────┐                 ┌──────────────────────┐
│   State Management      │                 │   External Services   │
│  - Session Data         │                 │  - OpenAI API         │
│  - Variation Data       │                 │  - File System        │
└─────────────────────────┘                 └──────────────────────┘
```

## Component Architecture

### 1. Frontend (Electron)

The frontend is built using Electron with HTML, CSS, and JavaScript, providing a native desktop experience.

#### Key Components:

- **Main Process**: Manages the application lifecycle and creates browser windows
- **Renderer Process**: Handles the UI and communicates with the backend
- **UI Components**:
  - **Instruction Panel**: Configuration inputs for content generation
  - **Workflow Panel**: Template editing and draft management
  - **Variable Editor**: Interface for modifying variation values
  - **Modals**: Configuration dialogs and confirmation screens

#### Frontend Technologies:
- HTML5/CSS3 for UI structure and styling
- Bootstrap 5 for responsive UI components
- JavaScript for client-side logic
- Axios for HTTP requests to the backend API

### 2. Backend (Python)

The backend is implemented in Python with a Flask-based API server.

#### Key Components:

- **API Server**: Flask application exposing RESTful endpoints
- **PDF Parser**: Extracts variation data from PDF documents
- **JSON Parser**: Processes and indexes content data
- **Session Manager**: Handles user session persistence
- **AI Integration**: Communicates with OpenAI's API
- **Output Generator**: Creates the final variation outputs

#### Backend Technologies:
- Python 3.8+ for server-side logic
- Flask for API server implementation
- pdfplumber for PDF parsing
- OpenAI API for content generation

## Module Descriptions

### 1. PDFParser Module

```python
class PDFParser:
    def parse_variation_pdf(self, pdf_path, format_type=None):
        # Extract variables and levels from PDF
        
    def _extract_from_unified_table(self, tables, variation_set):
        # Extract from tables with unified format
        
    def _extract_variables_individually(self, tables, text, variation_set):
        # Extract variables one by one
        
    def _extract_academic_field_variable(self, tables, text, variation_set):
        # Special handling for academic fields
        
    def _process_south_carolina_field_format(self, tables, variation_set):
        # Format-specific processing
        
    def update_field_values(self, variation_set, field_updates):
        # Update specific field values
        
    def add_field_value(self, variation_set, variable, value, data=None):
        # Add new field values
```

The PDFParser is responsible for:
- Extracting structured variation data from PDF documents
- Supporting multiple PDF formats, including the South Carolina format
- Implementing extraction strategies with fallback mechanisms
- Providing editing capabilities for extracted data

### 2. JSONParser Module

```python
class JSONParser:
    def parse_json_file(self, json_path):
        # Parse and index JSON content data
        
    def _detect_json_type(self, data, filename):
        # Determine if the JSON is for programs or clubs
```

The JSONParser is responsible for:
- Loading and parsing JSON files containing programs and clubs information
- Automatically detecting the JSON data type based on content and filename
- Indexing content by CIP codes for efficient lookup
- Creating a structured format for use in content generation

### 3. Session Manager Module

```python
class SessionManager:
    def create_session(self):
        # Create a new session
        
    def load_session(self, session_id):
        # Load existing session
        
    def save_session(self, session_data, session_id=None):
        # Save session data
        
    def get_current_session(self):
        # Retrieve current session
```

The SessionManager is responsible for:
- Creating, loading, and saving user sessions
- Maintaining session state across application restarts
- Managing temporary file storage
- Handling session configuration

### 4. AI Integration Module

```python
class AIIntegration:
    def generate_draft(self, original_copy, instructions, variation_levels):
        # Generate content draft
        
    def process_feedback(self, draft, feedback, instructions):
        # Process feedback and update
        
    def generate_variation(self, template, instructions, levels, content_data):
        # Generate specific variation
```

The AI Integration module is responsible for:
- Communicating with the OpenAI API
- Formatting prompts with instructions and context
- Processing and applying AI-generated content
- Handling feedback incorporation for iterative improvement

### 5. Output Generator Module

```python
class OutputGenerator:
    def generate_all_variations(self, template, instructions, variation_data, imported_data):
        # Generate all possible variations
        
    def save_variation_file(self, content, filename):
        # Save variation as markdown
        
    def replace_markers(self, content, variation_levels, imported_data):
        # Replace markers with content
```

The Output Generator is responsible for:
- Calculating all possible variation combinations
- Generating personalized content for each combination
- Replacing markers with appropriate content
- Creating and saving output files

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/status` | GET | Get application status and settings |
| `/api/session/current` | GET | Get current session data |
| `/api/session/update` | PUT | Update session data |
| `/api/session/new` | POST | Create new session |
| `/api/session/load` | POST | Load an existing session |
| `/api/session/save` | POST | Save current session |
| `/api/parse/pdf` | POST | Parse variation PDF |
| `/api/parse/json` | POST | Parse content JSON |
| `/api/parse/update` | PUT | Update parsed variation data |
| `/api/generate/draft` | POST | Generate initial draft |
| `/api/feedback/process` | POST | Process feedback on draft |
| `/api/variations/preview_samples` | POST | Preview sample variations |
| `/api/variations/generate_all` | POST | Generate all variations |

## Data Structures

### 1. Variation Set

```json
{
  "variables": ["GPA Range", "Distance", "Academic Field of Interest"],
  "levels": {
    "GPA Range": [
      {"value": "3.3+", "data": "1"},
      {"value": "2.7-3.3", "data": "2"},
      {"value": "Unknown/Null", "data": "Default"}
    ]
  }
}
```

### 2. Session Object

```json
{
  "id": "session-20250408-123456",
  "created_at": "2025-04-08T12:34:56",
  "updated_at": "2025-04-08T13:45:00",
  "instruction_set": {
    "partner_name": "University Name",
    "variation_application_instructions": "...",
    "marker_instructions": "...",
    "tone_other_prompts": "...",
    "variation_list_data": {},
    "distilled_variation_instructions": "..."
  },
  "imported_data": {
    "programs": {},
    "clubs": {}
  },
  "original_copy": "Template with {{MARKERS}}",
  "current_draft": "Generated content...",
  "current_variation_levels": {}
}
```

### 3. Field Update Schema

```json
[
  {
    "variable": "Academic Field of Interest",
    "data": "1",
    "value": "Computer Science"
  },
  {
    "variable": "GPA Range",
    "data": "2",
    "value": "3.0-3.49"
  }
]
```

## Security and Performance Considerations

### Security Measures

1. **API Key Handling**:
   - API keys are stored only in memory during the session
   - No persistent storage of API keys in plain text
   - API keys are transmitted securely to the backend

2. **File System Security**:
   - Limited access to specific application directories
   - No execution of arbitrary user code
   - Validation of file paths and content

### Performance Optimizations

1. **PDF Parsing**:
   - Specialized handling for different PDF formats
   - Fallback strategies for robustness
   - Caching of parsed results

2. **Content Generation**:
   - Asynchronous processing for UI responsiveness
   - Batch processing for bulk variations
   - Status updates during long-running operations

3. **Data Management**:
   - Efficient in-memory indexing of content
   - Lazy loading of JSON data
   - Throttling of API requests

## System Requirements

- **Operating System**: Windows 10+, macOS 10.14+, Ubuntu 18.04+
- **Memory**: 4GB RAM minimum, 8GB recommended
- **Storage**: 500MB free space for application, additional space for outputs
- **Network**: Internet connection for OpenAI API integration
- **Dependencies**:
  - Python 3.8+
  - Node.js 14+
  - OpenAI API key