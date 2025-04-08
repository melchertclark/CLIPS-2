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

## License

MIT