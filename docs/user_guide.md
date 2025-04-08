# CLIPS User Guide

Welcome to the Copywriter's Lightweight Iteration Pipeline System (CLIPS)! This guide will help you get up and running with the application.

## Getting Started

1. **Launch the application** by running `./run.sh` or `npm start` from the project directory.

2. **Set your OpenAI API key** if you haven't already. You'll see a red alert at the top of the application if your API key is not configured. Click "Set API Key" to enter your key.

3. **Create a new session** or load an existing one from the File menu.

## Setting up Your Variation System

### Step 1: Load a Variation Definition Document

1. Go to **Import > Load Variation Definition (PDF)**.
2. Select a PDF file that contains your variation variables and levels.
   - The PDF should contain tables or structured text defining variables and their possible levels.
   - Example format: Variable names in the first column, with levels in subsequent columns.
   - You can view an example in `/examples/sample_variation_definition.md`.

3. The parsed variables and levels will be displayed in the **Variation List Data** section.

### Step 2: Load Content Data (Optional)

If your variations include dynamic content based on fields of interest:

1. Go to **Import > Load Programs JSON** and/or **Import > Load Clubs JSON**.
2. Select your JSON files containing program or club information.
   - Each item should have an `eab_cip_code` field that matches codes in your variation definition.
   - See examples in `/examples/sample_programs.json` and `/examples/sample_clubs.json`.

3. Loaded data will be displayed in the **Imported Content Data** section.

### Step 3: Configure Your Instruction Set

Fill in the following sections in the left panel:

1. **Partner Name**: Enter the institution or context for your copy.

2. **Variation Application Instructions**:
   - Enter detailed notes about how variations should be applied.
   - These notes will be automatically distilled into concise instructions.

3. **Marker Instructions**:
   - Define how the AI should handle {{MARKERS}} in your template.
   - Example: "When you see {{LOCATION_DETAIL}}, customize content based on the Distance variable."

4. **Tone & Style Prompts**:
   - Add guidance about voice, tone, and style.
   - This is applied as a final filter to all generated variations.

## Creating Variations

### Step 1: Enter Your Original Copy

1. In the right panel, enter your copy template in the **Original Copy Template** section.
   - Include markers in double curly braces: `{{MARKER_NAME}}`.
   - These markers will be replaced with dynamically generated content.
   - See an example in `/examples/sample_copy_template.md`.

2. The system will detect and display all markers you've used.

### Step 2: Generate and Refine Drafts

1. Click **Generate Initial Draft** to create your first draft.

2. Toggle between **Default** and **Random Variation** to preview different variation combinations.

3. Provide feedback in the text area below the draft.

4. Click **Apply Feedback & Regenerate** to have the AI interpret your feedback and update the instructions.

5. Continue this iterative process until you're satisfied with the results.

### Step 3: Generate All Variations

1. When you're happy with your draft and instructions, click **Generate All Variations**.

2. Confirm the generation after reviewing the number of variations to be created.

3. The system will generate all possible combinations of variation levels as separate Markdown files.

4. Review the results summary when complete and click **Open Output Folder** to see your files.

## Saving and Loading Your Work

- **Save Session**: Save your current work to continue later.
- **Save Session As...**: Save a copy with a new filename.
- **Open Session**: Load a previously saved session.

## Tips and Best Practices

1. **Start small**: Begin with 2-3 variables and a few levels each to avoid combinatorial explosion.

2. **Be specific in your instructions**:
   - Clearly define how each variable affects the content.
   - Provide concrete examples where possible.

3. **Iterative refinement**:
   - Use the feedback loop to refine your instructions.
   - Consider generating multiple drafts before finalizing your instructions.

4. **Marker Best Practices**:
   - Use descriptive names for markers (e.g., `{{PROGRAM_HIGHLIGHT}}` rather than `{{SECTION_1}}`).
   - Keep markers semantically meaningful.

5. **Check your results**:
   - Review a sample of generated variations to ensure quality and accuracy.
   - Look for any missing data or incomplete replacements.

## Troubleshooting

- **PDF parsing issues**: Ensure your variation definition document has clear, consistent formatting.
- **API errors**: Check your OpenAI API key and account status.
- **Missing JSON data**: Verify that your JSON files contain the correct structure and `eab_cip_code` values.
- **Marker replacements**: Ensure your marker instructions clearly explain how each marker should be handled.