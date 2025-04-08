// Import required modules
const { ipcRenderer } = require('electron');
const axios = require('axios');

// Backend API URL
const API_BASE_URL = 'http://localhost:5000/api';

// Global state
let currentSession = null;
let pendingJsonData = null;
let appSettings = null;

// DOM Elements - Instruction Panel
const partnerNameInput = document.getElementById('partner-name-input');
const variationListEmpty = document.getElementById('variation-list-empty');
const variationListContent = document.getElementById('variation-list-content');
const jsonDataEmpty = document.getElementById('json-data-empty');
const jsonDataContent = document.getElementById('json-data-content');
const programsJsonItem = document.getElementById('programs-json-item');
const clubsJsonItem = document.getElementById('clubs-json-item');
const variationOriginalNotes = document.getElementById('variation-original-notes');
const variationDistilledInstructions = document.getElementById('variation-distilled-instructions');
const markerInstructionsInput = document.getElementById('marker-instructions-input');
const markersDetected = document.getElementById('markers-detected');
const markersList = document.getElementById('markers-list');
const tonePromptsInput = document.getElementById('tone-prompts-input');

// DOM Elements - Workflow Panel
const originalCopyInput = document.getElementById('original-copy-input');
const generateDraftBtn = document.getElementById('generate-draft-btn');
const generatedDraftCard = document.getElementById('generated-draft-card');
const generatedDraftOutput = document.getElementById('generated-draft-output');
const defaultDraftOption = document.getElementById('default-draft-option');
const randomDraftOption = document.getElementById('random-draft-option');
const draftVariationLevels = document.getElementById('draft-variation-levels');
const variationLevelsDisplay = document.getElementById('variation-levels-display');
const feedbackInput = document.getElementById('feedback-input');
const regenerateDraftBtn = document.getElementById('regenerate-draft-btn');
const applyFeedbackBtn = document.getElementById('apply-feedback-btn');
const finalGenerationCard = document.getElementById('final-generation-card');
const generateAllVariationsBtn = document.getElementById('generate-all-variations-btn');
const resultsSummaryCard = document.getElementById('results-summary-card');
const resultsContent = document.getElementById('results-content');

// DOM Elements - Modals
const apiKeyModal = new bootstrap.Modal(document.getElementById('apiKeyModal'));
const aboutModal = new bootstrap.Modal(document.getElementById('aboutModal'));
const jsonTypeModal = new bootstrap.Modal(document.getElementById('jsonTypeModal'));
const confirmGenerateAllModal = new bootstrap.Modal(document.getElementById('confirmGenerateAllModal'));
const apiKeyInput = document.getElementById('api-key-input');
const saveApiKeyBtn = document.getElementById('save-api-key-btn');
const apiKeyAlert = document.getElementById('api-key-alert');
const apiKeyAlertBtn = document.getElementById('api-key-alert-btn');
const appVersion = document.getElementById('app-version');
const programsRadio = document.getElementById('programsRadio');
const clubsRadio = document.getElementById('clubsRadio');
const confirmJsonTypeBtn = document.getElementById('confirm-json-type-btn');
const variationCount = document.getElementById('variation-count');
const confirmGenerateAllBtn = document.getElementById('confirm-generate-all-btn');

// DOM Elements - Status and Toolbar
const statusSpinner = document.getElementById('status-spinner');
const statusMessage = document.getElementById('status-message');

// Initialize the application
async function init() {
    // Get app settings
    try {
        const response = await axios.get(`${API_BASE_URL}/status`);
        appSettings = response.data.settings;
        
        // Update version in About modal
        if (appVersion) {
            appVersion.textContent = appSettings.version;
        }
        
        // Check if API key is set
        if (!appSettings.hasApiKey) {
            apiKeyAlert.style.display = 'block';
        } else {
            apiKeyAlert.style.display = 'none';
        }
        
        // Get current session
        await loadCurrentSession();
        
        // Debug mode
        if (appSettings.debugMode) {
            console.log('Running in debug mode');
            console.log('App settings:', appSettings);
        }
        
        setStatusMessage('Ready');
    } catch (error) {
        console.error('Failed to initialize app:', error);
        setStatusMessage('Error: Failed to connect to backend');
    }
}

// Set status message and show/hide spinner
function setStatusMessage(message, loading = false) {
    statusMessage.textContent = message;
    statusSpinner.style.display = loading ? 'inline-block' : 'none';
}

// Load current session from the server
async function loadCurrentSession() {
    try {
        setStatusMessage('Loading session...', true);
        
        const response = await axios.get(`${API_BASE_URL}/session/current`);
        currentSession = response.data.session;
        
        // Populate the UI with session data
        populateUIFromSession(currentSession);
        
        setStatusMessage('Session loaded');
    } catch (error) {
        console.error('Failed to load current session:', error);
        setStatusMessage('Error: Failed to load session');
    }
}

// Populate the UI from a session object
function populateUIFromSession(session) {
    if (!session) return;
    
    // Fill instruction fields
    partnerNameInput.value = session.instruction_set.partner_name || '';
    variationOriginalNotes.value = session.instruction_set.variation_application_instructions || '';
    variationDistilledInstructions.value = session.instruction_set.distilled_variation_instructions || '';
    markerInstructionsInput.value = session.instruction_set.marker_instructions || '';
    tonePromptsInput.value = session.instruction_set.tone_other_prompts || '';
    
    // Fill original copy
    originalCopyInput.value = session.original_copy || '';
    
    // Display variation list data if available
    if (session.instruction_set.variation_list_data && 
        session.instruction_set.variation_list_data.variables && 
        session.instruction_set.variation_list_data.variables.length > 0) {
        displayVariationListData(session.instruction_set.variation_list_data);
    } else {
        variationListEmpty.style.display = 'block';
        variationListContent.style.display = 'none';
    }
    
    // Display imported JSON data status
    updateJsonDataDisplay(session.imported_data);
    
    // Check for markers in original copy
    if (session.original_copy) {
        detectAndDisplayMarkers(session.original_copy);
    }
    
    // Show draft if available
    if (session.current_draft) {
        generatedDraftOutput.textContent = session.current_draft;
        generatedDraftCard.style.display = 'block';
        finalGenerationCard.style.display = 'block';
        
        if (Object.keys(session.current_variation_levels).length > 0) {
            displayVariationLevels(session.current_variation_levels);
        }
    }
}

// Display variation list data
function displayVariationListData(variationData) {
    if (!variationData || !variationData.variables || variationData.variables.length === 0) {
        variationListEmpty.style.display = 'block';
        variationListContent.style.display = 'none';
        return;
    }
    
    const variables = variationData.variables;
    const levels = variationData.levels || {};
    
    // Create HTML for the variation table
    let html = '<div class="table-responsive"><table class="variation-table">';
    html += '<thead><tr><th>Variable</th><th>Levels</th></tr></thead><tbody>';
    
    variables.forEach(variable => {
        const variableLevels = levels[variable] || [];
        const levelsText = variableLevels.map(level => {
            let text = level.value;
            if (level.data) {
                text += ` [${level.data}]`;
            }
            return text;
        }).join(', ');
        
        html += `<tr><td>${variable}</td><td>${levelsText}</td></tr>`;
    });
    
    html += '</tbody></table></div>';
    
    // Update the UI
    variationListContent.innerHTML = html;
    variationListEmpty.style.display = 'none';
    variationListContent.style.display = 'block';
}

// Update JSON data display
function updateJsonDataDisplay(importedData) {
    if (!importedData || (!importedData.programs && !importedData.clubs)) {
        jsonDataEmpty.style.display = 'block';
        jsonDataContent.style.display = 'none';
        return;
    }
    
    jsonDataEmpty.style.display = 'none';
    jsonDataContent.style.display = 'block';
    
    // Display programs data status
    if (importedData.programs) {
        programsJsonItem.style.display = 'flex';
    } else {
        programsJsonItem.style.display = 'none';
    }
    
    // Display clubs data status
    if (importedData.clubs) {
        clubsJsonItem.style.display = 'flex';
    } else {
        clubsJsonItem.style.display = 'none';
    }
}

// Detect markers in original copy and display them
function detectAndDisplayMarkers(copyText) {
    if (!copyText) {
        markersDetected.style.display = 'none';
        return;
    }
    
    const markerPattern = /\{\{([^\}]+)\}\}/g;
    const matches = [...copyText.matchAll(markerPattern)];
    
    if (matches.length > 0) {
        const uniqueMarkers = [...new Set(matches.map(match => match[1]))];
        markersList.textContent = uniqueMarkers.join(', ');
        markersDetected.style.display = 'block';
    } else {
        markersDetected.style.display = 'none';
    }
}

// Display variation levels for current draft
function displayVariationLevels(levels) {
    if (!levels || Object.keys(levels).length === 0) {
        draftVariationLevels.style.display = 'none';
        return;
    }
    
    let levelText = '';
    
    Object.entries(levels).forEach(([variable, level], index) => {
        if (index > 0) levelText += ', ';
        
        if (typeof level === 'object') {
            levelText += `${variable}: ${level.value}`;
        } else {
            levelText += `${variable}: ${level}`;
        }
    });
    
    variationLevelsDisplay.textContent = levelText;
    draftVariationLevels.style.display = 'block';
}

// Create a new session
async function createNewSession() {
    try {
        setStatusMessage('Creating new session...', true);
        
        const response = await axios.post(`${API_BASE_URL}/session/new`);
        currentSession = response.data.session;
        
        // Clear the UI
        clearUI();
        
        setStatusMessage('New session created');
    } catch (error) {
        console.error('Failed to create new session:', error);
        setStatusMessage('Error: Failed to create new session');
    }
}

// Clear the UI
function clearUI() {
    // Clear instruction fields
    partnerNameInput.value = '';
    variationOriginalNotes.value = '';
    variationDistilledInstructions.value = '';
    markerInstructionsInput.value = '';
    tonePromptsInput.value = '';
    
    // Clear original copy
    originalCopyInput.value = '';
    
    // Hide variation list data
    variationListEmpty.style.display = 'block';
    variationListContent.style.display = 'none';
    
    // Hide JSON data status
    jsonDataEmpty.style.display = 'block';
    jsonDataContent.style.display = 'none';
    programsJsonItem.style.display = 'none';
    clubsJsonItem.style.display = 'none';
    
    // Hide markers
    markersDetected.style.display = 'none';
    
    // Hide draft
    generatedDraftCard.style.display = 'none';
    generatedDraftOutput.textContent = 'No draft generated yet.';
    feedbackInput.value = '';
    
    // Hide final generation
    finalGenerationCard.style.display = 'none';
    
    // Hide results
    resultsSummaryCard.style.display = 'none';
}

// Save current session
async function saveSession(saveAs = false) {
    try {
        setStatusMessage('Saving session...', true);
        
        let filepath = null;
        let response;
        
        if (saveAs) {
            // Show save dialog
            filepath = await ipcRenderer.invoke('save-file-dialog', {
                filters: [{ name: 'CLIPS Session', extensions: ['json'] }],
                defaultPath: 'clips_session.json'
            });
            
            if (!filepath) {
                setStatusMessage('Save cancelled');
                return;
            }
            
            // Save session to new file
            response = await axios.post(`${API_BASE_URL}/session/save_as`, { filepath });
        } else {
            // Save session
            response = await axios.post(`${API_BASE_URL}/session/save`);
        }
        
        if (response.data.success) {
            setStatusMessage(`Session saved to ${response.data.filepath}`);
        } else {
            throw new Error(response.data.error || 'Unknown error');
        }
    } catch (error) {
        console.error('Failed to save session:', error);
        setStatusMessage('Error: Failed to save session');
        await ipcRenderer.invoke('show-error-dialog', {
            title: 'Save Error',
            message: `Failed to save session: ${error.message}`
        });
    }
}

// Load a session from file
async function loadSession() {
    try {
        // Show open dialog
        const filePaths = await ipcRenderer.invoke('open-file-dialog', {
            filters: [{ name: 'CLIPS Session', extensions: ['json'] }],
            properties: ['openFile']
        });
        
        if (!filePaths || filePaths.length === 0) {
            setStatusMessage('Open cancelled');
            return;
        }
        
        setStatusMessage('Loading session...', true);
        
        // Load session from file
        const response = await axios.post(`${API_BASE_URL}/session/load`, {
            filepath: filePaths[0]
        });
        
        if (response.data.success) {
            currentSession = response.data.session;
            populateUIFromSession(currentSession);
            setStatusMessage(`Session loaded from ${filePaths[0]}`);
        } else {
            throw new Error(response.data.error || 'Unknown error');
        }
    } catch (error) {
        console.error('Failed to load session:', error);
        setStatusMessage('Error: Failed to load session');
        await ipcRenderer.invoke('show-error-dialog', {
            title: 'Load Error',
            message: `Failed to load session: ${error.message}`
        });
    }
}

// Setup OpenAI API Key
async function setupApiKey() {
    const apiKey = apiKeyInput.value.trim();
    
    if (!apiKey) {
        await ipcRenderer.invoke('show-error-dialog', {
            title: 'API Key Required',
            message: 'Please enter your OpenAI API key.'
        });
        return;
    }
    
    try {
        setStatusMessage('Setting up API key...', true);
        
        const response = await axios.post(`${API_BASE_URL}/openai/setup`, { api_key: apiKey });
        
        if (response.data.success) {
            // Close modal
            apiKeyModal.hide();
            
            // Hide alert
            apiKeyAlert.style.display = 'none';
            
            // Update settings
            appSettings.hasApiKey = true;
            
            setStatusMessage('API key saved successfully');
        } else {
            throw new Error(response.data.error || 'Unknown error');
        }
    } catch (error) {
        console.error('Failed to setup API key:', error);
        setStatusMessage('Error: Failed to setup API key');
        await ipcRenderer.invoke('show-error-dialog', {
            title: 'API Key Error',
            message: `Failed to setup API key: ${error.response?.data?.error || error.message}`
        });
    }
}

// Load Variation Definition PDF
async function loadVariationPDF() {
    try {
        // Show open dialog
        const filePaths = await ipcRenderer.invoke('open-file-dialog', {
            filters: [{ name: 'PDF Files', extensions: ['pdf'] }],
            properties: ['openFile']
        });
        
        if (!filePaths || filePaths.length === 0) {
            setStatusMessage('Open cancelled');
            return;
        }
        
        setStatusMessage('Parsing PDF...', true);
        
        // Create FormData for file upload
        const formData = new FormData();
        const filePath = filePaths[0];
        
        // Read file as blob and append to form data
        const fileBlob = await fetch(`file://${filePath}`).then(r => r.blob());
        const file = new File([fileBlob], filePath.split(/[\\/]/).pop());
        formData.append('file', file);
        
        // Upload and parse PDF
        const response = await axios.post(`${API_BASE_URL}/parse/pdf`, formData, {
            headers: {
                'Content-Type': 'multipart/form-data'
            }
        });
        
        if (response.data.success) {
            // Display variation data
            displayVariationListData(response.data.variation_set);
            setStatusMessage('Variation definition loaded');
            
            // Update current session
            await loadCurrentSession();
        } else {
            throw new Error(response.data.error || 'Unknown error');
        }
    } catch (error) {
        console.error('Failed to load PDF:', error);
        setStatusMessage('Error: Failed to load PDF');
        await ipcRenderer.invoke('show-error-dialog', {
            title: 'PDF Load Error',
            message: `Failed to load PDF: ${error.response?.data?.error || error.message}`
        });
    }
}

// Load JSON file (Programs or Clubs)
async function loadJsonFile(type) {
    try {
        // Show open dialog
        const filePaths = await ipcRenderer.invoke('open-file-dialog', {
            filters: [{ name: 'JSON Files', extensions: ['json'] }],
            properties: ['openFile']
        });
        
        if (!filePaths || filePaths.length === 0) {
            setStatusMessage('Open cancelled');
            return;
        }
        
        setStatusMessage(`Parsing ${type} JSON...`, true);
        
        // Create FormData for file upload
        const formData = new FormData();
        const filePath = filePaths[0];
        
        // Read file as blob and append to form data
        const fileBlob = await fetch(`file://${filePath}`).then(r => r.blob());
        const file = new File([fileBlob], filePath.split(/[\\/]/).pop());
        formData.append('file', file);
        
        // Upload and parse JSON
        const response = await axios.post(`${API_BASE_URL}/parse/json`, formData, {
            headers: {
                'Content-Type': 'multipart/form-data'
            }
        });
        
        if (response.data.success) {
            if (response.data.requires_type_selection) {
                // Store the data for confirmation
                pendingJsonData = response.data.indexed_data;
                
                // Show type selection modal
                if (type === 'programs') {
                    programsRadio.checked = true;
                } else if (type === 'clubs') {
                    clubsRadio.checked = true;
                }
                
                jsonTypeModal.show();
            } else {
                // Update UI with JSON data status
                await loadCurrentSession();
                setStatusMessage(`${type} JSON loaded`);
            }
        } else {
            throw new Error(response.data.error || 'Unknown error');
        }
    } catch (error) {
        console.error(`Failed to load ${type} JSON:`, error);
        setStatusMessage(`Error: Failed to load ${type} JSON`);
        await ipcRenderer.invoke('show-error-dialog', {
            title: 'JSON Load Error',
            message: `Failed to load ${type} JSON: ${error.response?.data?.error || error.message}`
        });
    }
}

// Confirm JSON type
async function confirmJsonType() {
    if (!pendingJsonData) {
        jsonTypeModal.hide();
        return;
    }
    
    const dataType = document.querySelector('input[name="jsonTypeRadio"]:checked').value;
    
    try {
        setStatusMessage(`Setting JSON type to ${dataType}...`, true);
        
        const response = await axios.post(`${API_BASE_URL}/json/set_type`, {
            indexed_data: pendingJsonData,
            data_type: dataType
        });
        
        if (response.data.success) {
            jsonTypeModal.hide();
            pendingJsonData = null;
            
            // Update UI with JSON data status
            await loadCurrentSession();
            setStatusMessage(`${dataType} JSON loaded`);
        } else {
            throw new Error(response.data.error || 'Unknown error');
        }
    } catch (error) {
        console.error('Failed to set JSON type:', error);
        setStatusMessage('Error: Failed to set JSON type');
        await ipcRenderer.invoke('show-error-dialog', {
            title: 'JSON Type Error',
            message: `Failed to set JSON type: ${error.response?.data?.error || error.message}`
        });
    }
}

// Update instruction category
async function updateInstructions(category, value) {
    try {
        setStatusMessage(`Updating ${category}...`, true);
        
        const response = await axios.post(`${API_BASE_URL}/instructions/update`, { category, value });
        
        if (response.data.success) {
            // If this was variation_application_instructions, update the distilled instructions
            if (category === 'variation_application_instructions' && response.data.distilled) {
                variationDistilledInstructions.value = response.data.distilled;
            }
            
            setStatusMessage(`${category} updated`);
        } else {
            throw new Error(response.data.error || 'Unknown error');
        }
    } catch (error) {
        console.error(`Failed to update ${category}:`, error);
        setStatusMessage(`Error: Failed to update ${category}`);
    }
}

// Update original copy
async function updateOriginalCopy(copyText) {
    try {
        setStatusMessage('Updating original copy...', true);
        
        const response = await axios.post(`${API_BASE_URL}/copy/update`, { copy_text: copyText });
        
        if (response.data.success) {
            // Update markers
            if (response.data.markers.length > 0) {
                markersList.textContent = response.data.markers.join(', ');
                markersDetected.style.display = 'block';
            } else {
                markersDetected.style.display = 'none';
            }
            
            setStatusMessage('Original copy updated');
        } else {
            throw new Error(response.data.error || 'Unknown error');
        }
    } catch (error) {
        console.error('Failed to update original copy:', error);
        setStatusMessage('Error: Failed to update original copy');
    }
}

// Generate draft
async function generateDraft(variationType = 'default') {
    try {
        // Validate
        if (!originalCopyInput.value.trim()) {
            await ipcRenderer.invoke('show-error-dialog', {
                title: 'Original Copy Required',
                message: 'Please enter the original copy template before generating a draft.'
            });
            return;
        }
        
        setStatusMessage(`Generating ${variationType} draft...`, true);
        
        const response = await axios.post(`${API_BASE_URL}/draft/generate`, { variation_type: variationType });
        
        if (response.data.success) {
            // Display draft
            generatedDraftOutput.textContent = response.data.draft;
            generatedDraftCard.style.display = 'block';
            finalGenerationCard.style.display = 'block';
            
            // Display variation levels if any
            displayVariationLevels(response.data.variation_levels);
            
            setStatusMessage('Draft generated');
        } else {
            throw new Error(response.data.error || 'Unknown error');
        }
    } catch (error) {
        console.error('Failed to generate draft:', error);
        setStatusMessage('Error: Failed to generate draft');
        await ipcRenderer.invoke('show-error-dialog', {
            title: 'Draft Generation Error',
            message: `Failed to generate draft: ${error.response?.data?.error || error.message}`
        });
    }
}

// Process feedback and regenerate draft
async function processFeedback() {
    try {
        // Validate
        if (!feedbackInput.value.trim()) {
            await ipcRenderer.invoke('show-error-dialog', {
                title: 'Feedback Required',
                message: 'Please enter feedback before applying.'
            });
            return;
        }
        
        setStatusMessage('Processing feedback...', true);
        
        const response = await axios.post(`${API_BASE_URL}/feedback/process`, {
            feedback: feedbackInput.value.trim()
        });
        
        if (response.data.success) {
            // Show instruction updates
            if (response.data.instruction_updates) {
                // Update the UI with the changes
                if (response.data.instruction_updates.distilled_variation_instructions) {
                    variationDistilledInstructions.value = response.data.instruction_updates.distilled_variation_instructions;
                }
                if (response.data.instruction_updates.marker_instructions) {
                    markerInstructionsInput.value = response.data.instruction_updates.marker_instructions;
                }
                if (response.data.instruction_updates.tone_other_prompts) {
                    tonePromptsInput.value = response.data.instruction_updates.tone_other_prompts;
                }
            }
            
            // Display new draft
            generatedDraftOutput.textContent = response.data.draft;
            
            // Clear feedback field
            feedbackInput.value = '';
            
            setStatusMessage('Feedback applied and draft regenerated');
        } else {
            throw new Error(response.data.error || 'Unknown error');
        }
    } catch (error) {
        console.error('Failed to process feedback:', error);
        setStatusMessage('Error: Failed to process feedback');
        await ipcRenderer.invoke('show-error-dialog', {
            title: 'Feedback Processing Error',
            message: `Failed to process feedback: ${error.response?.data?.error || error.message}`
        });
    }
}

// Calculate and display total possible variations
async function calculateVariations() {
    try {
        if (!currentSession || 
            !currentSession.instruction_set || 
            !currentSession.instruction_set.variation_list_data || 
            !currentSession.instruction_set.variation_list_data.variables) {
            variationCount.textContent = 'Number of variations to generate: No variation data loaded';
            return 0;
        }
        
        const variables = currentSession.instruction_set.variation_list_data.variables;
        const levels = currentSession.instruction_set.variation_list_data.levels;
        
        let totalVariations = 1;
        variables.forEach(variable => {
            if (levels[variable]) {
                totalVariations *= levels[variable].length;
            }
        });
        
        variationCount.textContent = `Number of variations to generate: ${totalVariations}`;
        return totalVariations;
    } catch (error) {
        console.error('Error calculating variations:', error);
        variationCount.textContent = 'Error calculating variations';
        return 0;
    }
}

// Generate all variations
async function generateAllVariations() {
    try {
        setStatusMessage('Generating all variations...', true);
        
        const response = await axios.post(`${API_BASE_URL}/variations/generate_all`);
        
        if (response.data.success) {
            // Hide the confirmation modal
            confirmGenerateAllModal.hide();
            
            // Display results summary
            displayResultsSummary(response.data.results);
            
            setStatusMessage('All variations generated');
        } else {
            throw new Error(response.data.error || 'Unknown error');
        }
    } catch (error) {
        console.error('Failed to generate all variations:', error);
        setStatusMessage('Error: Failed to generate all variations');
        await ipcRenderer.invoke('show-error-dialog', {
            title: 'Variation Generation Error',
            message: `Failed to generate all variations: ${error.response?.data?.error || error.message}`
        });
    }
}

// Display results summary
function displayResultsSummary(results) {
    if (!results) return;
    
    let html = '<div class="results-summary">';
    
    // Show statistics
    html += '<div class="results-stats mb-3">';
    html += `<div class="results-stat">Total Variations: <span class="stat-number">${results.total}</span></div>`;
    html += `<div class="results-stat">Successfully Generated: <span class="stat-number text-success">${results.success}</span></div>`;
    
    if (results.failure > 0) {
        html += `<div class="results-stat">Failed Generations: <span class="stat-number text-danger">${results.failure}</span></div>`;
    }
    
    if (results.missing_data > 0) {
        html += `<div class="results-stat">Generated with Missing Data: <span class="stat-number text-warning">${results.missing_data}</span></div>`;
        html += '<div class="missing-data-warning"><i class="bi bi-exclamation-triangle-fill"></i> Some variations were generated with missing JSON data for specific CIP codes. These variations may have placeholder content.</div>';
    }
    
    html += '</div>'; // End results-stats
    
    html += '</div>'; // End results-summary
    
    // Update the UI
    resultsContent.innerHTML = html;
    resultsSummaryCard.style.display = 'block';
}

// Event listeners
document.addEventListener('DOMContentLoaded', () => {
    // Initialize app
    init();
    
    // Navbar menu items
    document.getElementById('new-session-btn').addEventListener('click', () => createNewSession());
    document.getElementById('open-session-btn').addEventListener('click', () => loadSession());
    document.getElementById('save-session-btn').addEventListener('click', () => saveSession());
    document.getElementById('save-as-session-btn').addEventListener('click', () => saveSession(true));
    document.getElementById('setup-api-key-btn').addEventListener('click', () => apiKeyModal.show());
    document.getElementById('load-pdf-btn').addEventListener('click', () => loadVariationPDF());
    document.getElementById('load-programs-json-btn').addEventListener('click', () => loadJsonFile('programs'));
    document.getElementById('load-clubs-json-btn').addEventListener('click', () => loadJsonFile('clubs'));
    document.getElementById('show-output-folder-btn').addEventListener('click', () => ipcRenderer.invoke('show-output-folder'));
    document.getElementById('about-btn').addEventListener('click', () => aboutModal.show());
    
    // API key modal
    saveApiKeyBtn.addEventListener('click', () => setupApiKey());
    document.getElementById('openai-link').addEventListener('click', (e) => {
        e.preventDefault();
        ipcRenderer.invoke('open-external-link', 'https://platform.openai.com/account/api-keys');
    });
    apiKeyAlertBtn.addEventListener('click', () => apiKeyModal.show());
    
    // JSON type modal
    confirmJsonTypeBtn.addEventListener('click', () => confirmJsonType());
    
    // Confirm generate all modal
    document.getElementById('generate-all-variations-btn').addEventListener('click', async () => {
        await calculateVariations();
        confirmGenerateAllModal.show();
    });
    confirmGenerateAllBtn.addEventListener('click', () => generateAllVariations());
    
    // Instructions panel event listeners
    partnerNameInput.addEventListener('change', (e) => updateInstructions('partner_name', e.target.value));
    variationOriginalNotes.addEventListener('change', (e) => updateInstructions('variation_application_instructions', e.target.value));
    markerInstructionsInput.addEventListener('change', (e) => updateInstructions('marker_instructions', e.target.value));
    tonePromptsInput.addEventListener('change', (e) => updateInstructions('tone_other_prompts', e.target.value));
    
    // Workflow panel event listeners
    originalCopyInput.addEventListener('change', (e) => updateOriginalCopy(e.target.value));
    generateDraftBtn.addEventListener('click', () => generateDraft('default'));
    regenerateDraftBtn.addEventListener('click', () => generateDraft(defaultDraftOption.checked ? 'default' : 'random'));
    applyFeedbackBtn.addEventListener('click', () => processFeedback());
    
    // Draft view options
    defaultDraftOption.addEventListener('change', () => {
        if (defaultDraftOption.checked) {
            generateDraft('default');
        }
    });
    randomDraftOption.addEventListener('change', () => {
        if (randomDraftOption.checked) {
            generateDraft('random');
        }
    });
    
    // Results button
    document.getElementById('view-results-folder-btn').addEventListener('click', () => 
        ipcRenderer.invoke('show-output-folder'));
});
