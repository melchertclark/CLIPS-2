# Getting Started with CLIPS

This guide will help you get CLIPS up and running on your system.

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.8+**: [Download Python](https://www.python.org/downloads/)
- **Node.js 14+**: [Download Node.js](https://nodejs.org/)
- **OpenAI API Key**: [Get API key](https://platform.openai.com/account/api-keys)

## Installation

### Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/CLIPS.git
cd CLIPS
```

### Step 2: Set Up the Environment

#### Install Python Dependencies

```bash
pip install -r requirements.txt
```

#### Install Node.js Dependencies

```bash
npm install
```

### Step 3: Configure the API Key

Create a `.env` file in the project root and add your OpenAI API key:

```
OPENAI_API_KEY=your_api_key_here
DEBUG=false
```

Alternatively, you can set the API key through the application UI after startup.

## Running the Application

Start the application with:

```bash
./run.sh
```

Or:

```bash
npm start
```

The application will open in an Electron window.

## Quick Start Guide

1. **Set your OpenAI API key** if prompted.

2. **Load a Variation Definition Document**:
   - Go to **Import > Load Variation Definition (PDF)**
   - Try using the sample in `/examples/sample_variation_definition.md` (you'll need to convert it to PDF first)

3. **Load Sample JSON Data** (Optional):
   - Go to **Import > Load Programs JSON**
   - Select `/examples/sample_programs.json`
   - Go to **Import > Load Clubs JSON**
   - Select `/examples/sample_clubs.json`

4. **Enter Original Copy Template**:
   - Copy the content from `/examples/sample_copy_template.md` into the Original Copy Template section
   - Or create your own with markers in the format `{{MARKER_NAME}}`

5. **Set Up Instructions**:
   - Enter a partner name
   - Add variation application instructions (see `/examples/sample_instructions.md` for examples)
   - Add marker instructions for each marker in your template
   - Add tone and style guidance

6. **Generate Initial Draft**:
   - Click the "Generate Initial Draft" button
   - Review the generated draft
   - Toggle between Default and Random Variation views

7. **Provide Feedback**:
   - Enter feedback in the text area below the draft
   - Click "Apply Feedback & Regenerate"
   - Repeat until satisfied

8. **Generate All Variations**:
   - When ready, click "Generate All Variations"
   - Review the variation count and confirm
   - Wait for generation to complete
   - Use "Open Output Folder" to see your generated files

## Development Mode

For development, run the application with debugging enabled:

```bash
npm run dev
```

This will:
- Start the application
- Open Chrome DevTools automatically
- Enable more verbose logging

## Building for Distribution

To create a distributable version of the application:

```bash
npm run build
```

This will create a packaged application in the `dist` directory.

## Next Steps

- Check out the [User Guide](user_guide.md) for more detailed instructions.
- Explore the examples directory for sample files.
- Join our GitHub discussions for support and feature requests.