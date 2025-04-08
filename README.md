# CLIPS - Copywriter's Lightweight Iteration Pipeline System

A tool for streamlining the generation of multiple copy variations for college enrollment marketing materials by combining user-defined instructions, a base copy template, parsing structured variation definitions, importing relevant content data, and leveraging AI generation capabilities via the OpenAI API.

## Features

- Two-panel UI for instruction input and workflow management
- PDF parsing for variation definitions 
- JSON data import for dynamic content
- OpenAI API integration for AI-powered content generation
- Iterative feedback cycle for refinement
- Session persistence for saving and loading work
- Markdown export for final variations

## Installation

### Prerequisites

- Python 3.8+
- Node.js and npm

### Setup

1. Clone the repository
   ```
   git clone https://github.com/yourusername/CLIPS.git
   cd CLIPS
   ```

2. Install Python dependencies
   ```
   pip install -r requirements.txt
   ```

3. Install Node.js dependencies
   ```
   npm install
   ```

4. Create a `.env` file and add your OpenAI API key
   ```
   cp .env.example .env
   # Edit .env file and add your OpenAI API key
   ```

## Usage

1. Start the application
   ```
   ./run.sh
   ```
   
   or
   
   ```
   npm start
   ```

2. The application will open with two main panels:
   - **Left Panel**: Instruction Set - Controls how variations are generated
   - **Right Panel**: Workflow - Contains your original copy and generated drafts

3. **Basic workflow**:
   - Load a variation definition document (PDF)
   - Load relevant JSON data files (Programs/Clubs)
   - Enter your base copy template with markers in the format `{{MARKER_NAME}}`
   - Configure your instruction set
   - Generate an initial draft
   - Provide feedback and iterate
   - Generate all variations when satisfied

## Understanding the Interface

### Instruction Set Panel

- **Partner Name**: The institution or context for the copy
- **Variation List Data**: Displays the parsed variables and levels from your PDF
- **Imported Content Data**: Shows what JSON data files are loaded
- **Variation Application Instructions**: Your notes on how variations should be applied
- **Marker Instructions**: How to handle markers in your template
- **Tone & Style Prompts**: Final adjustments to the tone or style

### Workflow Panel

- **Original Copy Template**: Your base copy with markers
- **Generated Draft**: View drafts with default or random variation levels
- **Feedback**: Provide feedback to improve the draft
- **Final Generation**: Generate all variations as Markdown files

## Development

Run in development mode with debugging enabled:
```
npm run dev
```

## Build (for distribution)

Create a distributable version:
```
npm run build
```

## Troubleshooting

- **API Key Issues**: Ensure your OpenAI API key is correctly set in the `.env` file or through the application UI
- **PDF Parsing Problems**: Make sure your variation definition document has a clear structure (tables or structured text)
- **Missing JSON Data**: Check that your JSON files contain the necessary `eab_cip_code` fields

## Enhanced PDF Parser

The system includes an advanced PDF parser with additional capabilities:

### Features

- Extract variation variables and levels from PDF documents
- Support for South Carolina and standard variation list formats
- Parse PDFs from local files or URLs
- Edit and customize parsed data
- RESTful API for integration with other systems
- Web-based editor for manual review and editing
- Command-line interface for batch processing

### Usage

#### Command Line Interface

The PDF parser can be used directly from the command line:

```bash
# Parse a local PDF file
python run_parser.py --pdf /path/to/variation.pdf

# Parse a PDF from a URL
python run_parser.py --url https://example.com/variation.pdf

# Specify the PDF format
python run_parser.py --pdf /path/to/variation.pdf --format south_carolina

# Save output to a specific location
python run_parser.py --pdf /path/to/variation.pdf --output result.json

# Edit fields during parsing
python run_parser.py --pdf /path/to/variation.pdf --edit "Academic Field of Interest:1=Computer Science"
```

#### API Server

Start the API server:

```bash
python run_parser.py --api
```

The API server will be available at http://localhost:5000 with the following endpoints:

- `POST /api/parse` - Parse a PDF file or URL
- `POST /api/update` - Update fields in a variation set
- `POST /api/add_field` - Add a new field to a variation set

#### Web-based Editor

Access the web-based editor by opening `frontend/editor.html` in your browser. This interface allows you to:

1. Parse PDF files from local paths or URLs
2. View and edit all extracted fields
3. Add new fields or delete existing ones
4. Download the modified variation set as JSON

#### Python API

You can also use the parser directly in your Python code:

```python
from backend.parsing import PDFParser

# Initialize parser
parser = PDFParser()

# Parse PDF file
variation_set = parser.parse_variation_pdf('/path/to/variation.pdf')

# Parse PDF from URL
variation_set = parser.parse_variation_pdf('https://example.com/variation.pdf')

# Update field values
field_updates = [
    {
        'variable': 'Academic Field of Interest',
        'data': '1',
        'value': 'Computer Science'
    }
]
updated_set = parser.update_field_values(variation_set, field_updates)

# Add a new field
updated_set = parser.add_field_value(
    variation_set, 
    'Academic Field of Interest', 
    'Mathematics', 
    '20'  # Optional ID, auto-assigned if None
)
```

### PDF Format Support

The parser supports multiple PDF formats for variation definitions:

- **South Carolina Format**: Used for South Carolina University variation lists (use `--format south_carolina`)
- **Standard Format**: General format with variables and levels in tables (default)

The parser will attempt to auto-detect the format, but you can specify it explicitly for better results.

## License

MIT