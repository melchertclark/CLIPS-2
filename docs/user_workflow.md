# CLIPS-2 User Workflow & Data Flow

## User Workflow Narrative

### 1. Setup Phase

As a marketing copywriter for a college enrollment campaign, you begin by launching the CLIPS-2 application. The interface displays two main panels:

- **Left Panel (Instruction Set)**: Where you'll configure your content generation parameters
- **Right Panel (Workflow)**: Where you'll interact with your source copy and generated variations

The first time you use the application, you'll need to set your OpenAI API key by clicking the alert banner or navigating to File → Set OpenAI API Key. This API key is stored in memory for the current session and will be used for all AI-powered operations.

### 2. Content Import Phase

#### Importing the Variation Definition

You start by importing a variation definition that specifies how your content will be personalized. Navigate to Import → Load Variation Definition (PDF). You select a structured PDF document (such as "South Carolina Variation List.pdf") that contains:

- Variables (e.g., "GPA Range", "Distance", "Academic Field of Interest")
- Levels for each variable (e.g., GPA ranges like "3.3+", "2.7-3.3")
- Variation IDs (unique identifiers that match with JSON data)

The system processes the PDF and displays the extracted variables and levels in the Variation Definition section. If you notice any parsing issues or missing fields, you can click the "Edit Variable Values" button to:
- Correct any incorrectly parsed values
- Add new levels that may have been missed
- Remove unnecessary levels
- View and maintain the mapping between fields and their IDs

#### Importing Content Data

Next, you import the content data that will populate the dynamic sections of your copy:

1. Navigate to Import → Load Programs JSON to import academic program details
2. Navigate to Import → Load Clubs JSON to import student organization details

These JSON files contain structured information about programs and clubs, indexed by `eab_cip_code` which corresponds to the Academic Field of Interest variable levels.

### 3. Content Creation Phase

#### Setting Up Your Template

In the right panel, you enter your base copy template in the "Original Copy Template" section. This template includes placeholders (markers) in double curly braces, such as `{{PROGRAM_DETAILS}}` or `{{CLUB_HIGHLIGHTS}}`, which will be replaced with relevant content for each variation.

As you type, the system automatically detects and displays the markers you've used below the Marker Instructions field.

#### Configuring Instructions

You complete the instruction set in the left panel:

1. **Partner Name**: Enter the institution name
2. **Variation Application Instructions**: Provide detailed notes on how to apply the variations
3. **Marker Instructions**: Specific guidance on how to handle and replace the markers
4. **Tone & Style Prompts**: Additional stylistic guidance for the generated content

### 4. Content Generation & Refinement

#### Initial Draft Generation

With your template and instructions in place, click the "Generate Initial Draft" button. The system creates a draft using default variation levels.

You can toggle between viewing the draft with default levels or a random variation using the radio buttons at the top of the Generated Draft section.

#### Feedback Loop

Review the generated draft and provide feedback in the "Provide Feedback for Improvement" field. This feedback can address tone, content, or any other aspects needing refinement.

Click "Apply Feedback & Regenerate" to have the system incorporate your feedback. The AI updates the draft and may also refine the instructions based on your feedback.

You can repeat this feedback process until you're satisfied with the results.

### 5. Final Generation

When you're satisfied with the draft and how the variations are being applied, click "Generate All Variations". The system will:

1. Calculate the total number of variations based on all possible combinations
2. Confirm your intention to generate all variations
3. Process each variation, applying specific content for each combination of variables
4. Save the results as Markdown files in the output folder

A results summary will display when the process is complete, showing how many variations were created and any issues encountered.

### 6. Result Management

Review the generated variations by clicking "Open Output Folder". Each file represents a unique combination of variation levels, with all markers replaced with relevant, personalized content.

You can edit these files manually if needed or use them directly in your marketing campaigns.

## Data Flow Explanation

### 1. Application Initialization

```
User Launches App → Backend Server Starts → Frontend UI Loads → Session Status Check
```

- The application initializes with an empty or previous session
- The backend Python server handles API requests, file processing, and AI integration
- The frontend Electron-based UI provides the interactive interface

### 2. PDF Parsing Process

```
PDF Upload → PDFParser Class → Extraction Strategies → Variation Set Construction → UI Display
```

When a PDF is uploaded:
1. The `PDFParser` class receives the file path or URL
2. Multiple extraction strategies are attempted:
   - Unified table extraction
   - Individual variable extraction
   - Text-based extraction as fallback
3. For each variable (GPA, Distance, Academic Field), specialized processing logic is applied
4. South Carolina format detection for special handling of complex PDFs
5. The parser constructs a structured "variation set" with variables and levels
6. The UI displays the extracted data in the Variation Definition section

### 3. JSON Data Processing

```
JSON Upload → JSONParser Class → CIP Code Indexing → Content Mapping → Memory Storage
```

When JSON files are uploaded:
1. The `JSONParser` class detects whether it's program or club data
2. Content is indexed by `eab_cip_code` to allow fast lookup
3. The data is stored in the current session for later use in content generation
4. The UI displays the available CIP codes and validation status

### 4. Session Management

```
UI Changes → Event Handlers → Session Updates → Server Storage → Persistence
```

As users interact with the UI:
1. Change events trigger `handleContentChange()` functions
2. Data is collected and sent to the backend via API calls
3. The session is updated and stored
4. Content and settings persist across application restarts

### 5. Draft Generation Process

```
Template + Instructions → AI Request → Content Generation → Marker Replacement → Display
```

When generating a draft:
1. Original copy, instructions, and selected variation levels are sent to the backend
2. The backend formats an API request to OpenAI
3. The generated content is received and processed
4. Markers are replaced with relevant content based on the selected variation levels
5. The resulting draft is displayed in the UI

### 6. Variation Generation Pipeline

```
Final Template → Level Combinations → Batch Processing → Content Filling → Markdown Files
```

For final variation generation:
1. All possible combinations of variation levels are calculated
2. For each combination:
   - Specific variation levels are selected
   - Relevant content for that combination is retrieved from the JSON data
   - OpenAI generates content tailored to those specific levels
   - Markers are replaced with personalized content
   - A Markdown file is created and saved with the completed copy
3. Progress is tracked and reported back to the UI

### 7. Field Editing Flow

```
Edit Button → Variable Modal → UI Manipulation → Data Model Updates → Session Persistence
```

When editing variable fields:
1. The edit interface loads current variation data into an editable modal
2. User changes are collected through form inputs
3. Upon saving, the data model is updated with the new values
4. Changes are persisted in the session
5. The UI is refreshed to reflect the updates

### Key Data Structures

1. **Variation Set**: The core data structure representing variables and their levels
   ```json
   {
     "variables": ["GPA Range", "Distance", "Academic Field of Interest"],
     "levels": {
       "GPA Range": [
         {"value": "3.3+", "data": "1"},
         {"value": "2.7-3.3", "data": "2"},
         {"value": "2.7 or lower", "data": "3"},
         {"value": "Unknown/Null", "data": "Default"}
       ],
       "Distance": [...],
       "Academic Field of Interest": [...]
     }
   }
   ```

2. **Session Object**: Contains all current working data
   ```json
   {
     "instruction_set": {
       "partner_name": "University Name",
       "variation_application_instructions": "...",
       "marker_instructions": "...",
       "tone_other_prompts": "...",
       "variation_list_data": {VARIATION_SET},
       "distilled_variation_instructions": "..."
     },
     "imported_data": {
       "programs": {INDEXED_PROGRAMS},
       "clubs": {INDEXED_CLUBS}
     },
     "original_copy": "Template with {{MARKERS}}",
     "current_draft": "Generated content...",
     "current_variation_levels": {...}
   }
   ```

3. **Indexed Content**: JSON data organized by CIP code
   ```json
   {
     "type": "programs",
     "source_file": "sample_programs.json",
     "by_cip_code": {
       "BUS001": [
         {
           "program_name": "Business Administration",
           "eab_cip_code": "BUS001",
           "...": "..."
         }
       ]
     }
   }
   ```

This data flow architecture enables efficient processing of complex variations and ensures that the user interface remains responsive while handling large datasets and multiple API calls.