// Import required modules
const { ipcRenderer } = require('electron');
const axios = require('axios');

// Backend API URL - will be updated with the correct port when the app starts
let API_BASE_URL = 'http://127.0.0.1:3000/api';

// For debugging
console.log(`Initial API base URL: ${API_BASE_URL}`);

// Function to update the API base URL with the correct port
function updateApiBaseUrl(port) {
  API_BASE_URL = `http://127.0.0.1:${port}/api`;
  console.log(`API base URL updated to: ${API_BASE_URL}`);
}

// Listen for port updates from the main process
ipcRenderer.on('update-backend-port', (event, port) => {
  console.log(`Received backend port update: ${port}`);
  updateApiBaseUrl(port);
});

// Configure axios defaults - don't set Content-Type globally as it conflicts with file uploads
axios.defaults.headers.common = {
  'Accept': 'application/json'
};

// For JSON requests, set the content type manually
const jsonRequestInterceptor = axios.interceptors.request.use(
  config => {
    if (!config.data || !(config.data instanceof FormData)) {
      // If not FormData, it's a JSON request
      config.headers['Content-Type'] = 'application/json';
    }
    return config;
  },
  error => Promise.reject(error)
);

// Add request interceptor for debugging
axios.interceptors.request.use(request => {
  console.log('Request:', request.method, request.url);
  return request;
}, error => {
  console.error('Request error:', error);
  return Promise.reject(error);
});

// Add response interceptor for debugging
axios.interceptors.response.use(response => {
  console.log('Response:', response.status, response.config.url);
  return response;
}, error => {
  console.error('Response error:', error.message, error.response?.status, error.response?.config?.url);
  return Promise.reject(error);
});

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
const editVariablesModal = new bootstrap.Modal(document.getElementById('editVariablesModal'));
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
const editVariationsBtn = document.getElementById('edit-variations-btn');
const saveVariableEditsBtn = document.getElementById('save-variable-edits-btn');
const editVariablesAccordion = document.getElementById('editVariablesAccordion');
const newLevelVariable = document.getElementById('new-level-variable');
const newLevelId = document.getElementById('new-level-id');
const newLevelValue = document.getElementById('new-level-value');
const addNewLevelBtn = document.getElementById('add-new-level-btn');

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
    console.log("Displaying variation data:", variationData);
    
    if (!variationData || !variationData.variables || variationData.variables.length === 0) {
        variationListEmpty.style.display = 'block';
        variationListContent.style.display = 'none';
        return;
    }
    
    const variables = variationData.variables;
    const levels = variationData.levels || {};
    
    // Calculate total possible variations
    let totalVariations = 1;
    variables.forEach(variable => {
        if (levels[variable]) {
            totalVariations *= levels[variable].length;
        }
    });
    
    // Update total variations count
    document.getElementById('total-variations-count').textContent = totalVariations.toLocaleString();
    
    // Create a container for all variable tables
    let tablesContainer = document.getElementById('variables-tables-container');
    tablesContainer.innerHTML = '';
    
    // Create a card for each variable
    variables.forEach(variable => {
        const variableLevels = levels[variable] || [];
        const isAcademicField = variable.toLowerCase().includes('academic') || variable.toLowerCase().includes('field');
        
        // Create a card for this variable
        const variableCard = document.createElement('div');
        variableCard.className = 'card mb-3';
        variableCard.dataset.variable = variable;
        
        // Card header with variable name
        const cardHeader = document.createElement('div');
        cardHeader.className = 'card-header';
        cardHeader.innerHTML = `<h6 class="mb-0">${variable} <span class="badge bg-secondary ms-2">${variableLevels.length} levels</span></h6>`;
        variableCard.appendChild(cardHeader);
        
        // Card body with levels table
        const cardBody = document.createElement('div');
        cardBody.className = 'card-body p-0';
        
        const table = document.createElement('table');
        table.className = 'table table-sm mb-0';
        
        // Table header
        const tableHeader = document.createElement('thead');
        tableHeader.innerHTML = `
            <tr>
                <th>ID</th>
                <th>Level</th>
                ${isAcademicField ? '<th>CIP Code</th>' : ''}
            </tr>
        `;
        table.appendChild(tableHeader);
        
        // Table body
        const tableBody = document.createElement('tbody');
        variableLevels.forEach(level => {
            const row = document.createElement('tr');
            
            // Apply special styling for the academic field variable
            if (isAcademicField) {
                row.className = 'academic-field-row';
            }
            
            // ID column (either "Default" or a number)
            const idCell = document.createElement('td');
            idCell.className = 'text-center';
            idCell.style.width = '80px';
            
            // Format the ID column with special styling for Default
            if (level.data && level.data.toLowerCase() === 'default') {
                idCell.innerHTML = `<span class="badge bg-secondary">Default</span>`;
            } else {
                idCell.textContent = level.data || '';
            }
            row.appendChild(idCell);
            
            // Level/value column
            const valueCell = document.createElement('td');
            valueCell.textContent = level.value;
            row.appendChild(valueCell);
            
            // Add CIP code column for academic field
            if (isAcademicField) {
                const cipCell = document.createElement('td');
                cipCell.className = 'text-muted';
                cipCell.textContent = level.data || '';
                row.appendChild(cipCell);
            }
            
            tableBody.appendChild(row);
        });
        table.appendChild(tableBody);
        
        cardBody.appendChild(table);
        variableCard.appendChild(cardBody);
        
        // Add special info for Academic Field variable
        if (isAcademicField) {
            const academicFieldInfo = document.createElement('div');
            academicFieldInfo.className = 'card-footer bg-light small';
            academicFieldInfo.innerHTML = `
                <div class="d-flex align-items-center">
                    <div class="text-muted">
                        <i class="bi bi-info-circle"></i> The ID values match with <code>eab_cip_code</code> in JSON files
                    </div>
                    <div class="ms-auto">
                        <button class="btn btn-sm btn-outline-secondary check-json-match-btn">
                            Check JSON Match
                        </button>
                    </div>
                </div>
            `;
            variableCard.appendChild(academicFieldInfo);
            
            // Show the JSON matching info when academic field is present
            document.getElementById('json-academic-field-match').style.display = 'block';
        }
        
        // Add the card to the container
        tablesContainer.appendChild(variableCard);
    });
    
    // Show the variation content and hide the empty message
    variationListEmpty.style.display = 'none';
    variationListContent.style.display = 'block';
    
    // Add event listener for the check JSON match button
    document.querySelectorAll('.check-json-match-btn').forEach(button => {
        button.addEventListener('click', checkJsonFieldMatch);
    });
    
    // Add event listener for the preview variations button
    const previewBtn = document.getElementById('preview-variations-btn');
    if (previewBtn) {
        previewBtn.addEventListener('click', previewSampleVariations);
    }
}

// Function to check the match between Academic Field IDs and JSON CIP codes
function checkJsonFieldMatch() {
    if (!currentSession || 
        !currentSession.instruction_set || 
        !currentSession.instruction_set.variation_list_data ||
        !currentSession.imported_data) {
        return;
    }
    
    try {
        // Find the Academic Field variable and its levels
        const academicFieldVariable = currentSession.instruction_set.variation_list_data.variables.find(
            v => v.toLowerCase().includes('academic') || v.toLowerCase().includes('field')
        );
        
        if (!academicFieldVariable) {
            alert('Academic Field of Interest variable not found in variation data.');
            return;
        }
        
        const academicFieldLevels = currentSession.instruction_set.variation_list_data.levels[academicFieldVariable] || [];
        
        // Get the available CIP codes from JSON data
        const programsCipCodes = currentSession.imported_data.programs ? 
            Object.keys(currentSession.imported_data.programs.by_cip_code || {}) : [];
        
        const clubsCipCodes = currentSession.imported_data.clubs ? 
            Object.keys(currentSession.imported_data.clubs.by_cip_code || {}) : [];
        
        // Create a match report
        let matchedCount = 0;
        let unmatchedCodes = [];
        
        academicFieldLevels.forEach(level => {
            const cipCode = level.data;
            if (!cipCode || cipCode.toLowerCase() === 'default') return;
            
            const hasPrograms = programsCipCodes.includes(cipCode);
            const hasClubs = clubsCipCodes.includes(cipCode);
            
            if (!hasPrograms && !hasClubs) {
                unmatchedCodes.push({
                    field: level.value,
                    code: cipCode
                });
            } else {
                matchedCount++;
            }
        });
        
        // Show the results
        let message = `<strong>Match Results:</strong><br>`;
        message += `${matchedCount} out of ${academicFieldLevels.length} Academic Fields have matching content in JSON files.<br>`;
        
        if (unmatchedCodes.length > 0) {
            message += `<br><strong>Fields without matching content:</strong><ul>`;
            unmatchedCodes.forEach(item => {
                message += `<li>${item.field} (ID: ${item.code})</li>`;
            });
            message += `</ul>`;
        }
        
        // Display in a modal or alert
        alert(message);
        
    } catch (error) {
        console.error('Error checking JSON match:', error);
        alert('An error occurred while checking JSON matches. See console for details.');
    }
}

// Update JSON data display
function updateJsonDataDisplay(importedData) {
    console.log("Updating JSON data display with:", JSON.stringify(importedData, null, 2));
    
    if (!importedData) {
        console.log("No imported data");
        jsonDataEmpty.style.display = 'block';
        jsonDataContent.style.display = 'none';
        return;
    }
    
    // Check if we have either programs or clubs data
    const hasPrograms = importedData.programs && (typeof importedData.programs === 'object');
    const hasClubs = importedData.clubs && (typeof importedData.clubs === 'object');
    
    console.log(`Has programs: ${hasPrograms}, Has clubs: ${hasClubs}`);
    
    if (!hasPrograms && !hasClubs) {
        jsonDataEmpty.style.display = 'block';
        jsonDataContent.style.display = 'none';
        return;
    }
    
    jsonDataEmpty.style.display = 'none';
    jsonDataContent.style.display = 'block';
    
    // Display programs data status with CIP code count
    if (hasPrograms) {
        console.log("Showing programs data");
        programsJsonItem.style.display = 'flex';
        
        // Count CIP codes
        const cipCount = Object.keys(importedData.programs.by_cip_code || {}).length;
        
        // Update the count display
        const programsCipCount = document.getElementById('programs-cip-count');
        if (programsCipCount) {
            programsCipCount.textContent = `${cipCount} unique CIP codes`;
        }
    } else {
        console.log("Hiding programs data");
        programsJsonItem.style.display = 'none';
    }
    
    // Display clubs data status with CIP code count
    if (hasClubs) {
        console.log("Showing clubs data");
        clubsJsonItem.style.display = 'flex';
        
        // Count CIP codes
        const cipCount = Object.keys(importedData.clubs.by_cip_code || {}).length;
        
        // Update the count display
        const clubsCipCount = document.getElementById('clubs-cip-count');
        if (clubsCipCount) {
            clubsCipCount.textContent = `${cipCount} unique CIP codes`;
        }
    } else {
        console.log("Hiding clubs data");
        clubsJsonItem.style.display = 'none';
    }
    
    // Show the JSON academic field match warning if variation data is loaded
    if (currentSession && 
        currentSession.instruction_set && 
        currentSession.instruction_set.variation_list_data &&
        currentSession.instruction_set.variation_list_data.variables) {
        
        // Check if we have Academic Field in the variation data
        const hasAcademicField = currentSession.instruction_set.variation_list_data.variables.some(
            variable => variable.toLowerCase().includes('academic') || variable.toLowerCase().includes('field')
        );
        
        if (hasAcademicField) {
            document.getElementById('json-academic-field-match').style.display = 'block';
        }
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
        
        // Read the file directly using Node.js fs
        const fs = require('fs');
        const path = require('path');
        const filePath = filePaths[0];
        const fileContent = fs.readFileSync(filePath);
        const filename = path.basename(filePath);
        
        // Create FormData for file upload
        const formData = new FormData();
        const blob = new Blob([fileContent], { type: 'application/pdf' });
        const file = new File([blob], filename);
        formData.append('file', file);
        
        console.log('Uploading file:', filename, 'size:', fileContent.length);
        
        // Upload and parse PDF with formData (axios will set the content-type boundary automatically)
        const response = await axios.post(`${API_BASE_URL}/parse/pdf`, formData, {
            // DO NOT set Content-Type header manually, let axios set it with the correct boundary
            headers: {
                // Clear any default headers that might interfere
                'Accept': 'application/json'
            },
            // Increase timeout for large files
            timeout: 60000
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
        
        // Read the file directly using Node.js fs
        const fs = require('fs');
        const path = require('path');
        const filePath = filePaths[0];
        const fileContent = fs.readFileSync(filePath);
        const filename = path.basename(filePath);
        
        // Create FormData for file upload
        const formData = new FormData();
        const blob = new Blob([fileContent], { type: 'application/json' });
        const file = new File([blob], filename);
        formData.append('file', file);
        
        console.log('Uploading JSON file:', filename, 'size:', fileContent.length);
        
        // Upload and parse JSON with formData (axios will set the content-type boundary automatically)
        const response = await axios.post(`${API_BASE_URL}/parse/json`, formData, {
            // DO NOT set Content-Type header manually, let axios set it with the correct boundary
            headers: {
                // Clear any default headers that might interfere
                'Accept': 'application/json'
            },
            // Increase timeout for large files
            timeout: 60000
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

// Preview sample variations to see how different combinations would look
async function previewSampleVariations() {
    try {
        // Validate that we have the necessary data
        if (!currentSession || 
            !currentSession.instruction_set || 
            !currentSession.instruction_set.variation_list_data || 
            !currentSession.original_copy) {
            await ipcRenderer.invoke('show-error-dialog', {
                title: 'Preview Error',
                message: 'Please load a variation definition and enter original copy before previewing variations.'
            });
            return;
        }
        
        setStatusMessage('Generating variation previews...', true);
        
        // Request sample variations from the backend
        const response = await axios.post(`${API_BASE_URL}/variations/preview_samples`);
        
        if (response.data.success) {
            // Create a modal to display the samples
            const previewModalHTML = `
                <div class="modal fade" id="previewSamplesModal" tabindex="-1" aria-hidden="true">
                    <div class="modal-dialog modal-lg modal-dialog-scrollable">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h5 class="modal-title">Sample Variations Preview</h5>
                                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                            </div>
                            <div class="modal-body">
                                <p>Below are sample variations based on different combinations of your variation levels:</p>
                                <div id="preview-samples-container"></div>
                            </div>
                            <div class="modal-footer">
                                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            // Add the modal to the DOM if it doesn't exist
            if (!document.getElementById('previewSamplesModal')) {
                document.body.insertAdjacentHTML('beforeend', previewModalHTML);
            }
            
            // Generate the samples UI
            const samplesContainer = document.getElementById('preview-samples-container');
            samplesContainer.innerHTML = '';
            
            response.data.samples.forEach((sample, index) => {
                const sampleCard = document.createElement('div');
                sampleCard.className = 'card mb-3';
                
                // Create the card header with variation levels
                const cardHeader = document.createElement('div');
                cardHeader.className = 'card-header';
                
                let levelText = '';
                for (const [variable, level] of Object.entries(sample.levels)) {
                    if (levelText) levelText += ', ';
                    levelText += `${variable}: ${level.value || level}`;
                }
                
                cardHeader.innerHTML = `<strong>Sample ${index + 1}</strong> - ${levelText}`;
                sampleCard.appendChild(cardHeader);
                
                // Create the card body with the preview content
                const cardBody = document.createElement('div');
                cardBody.className = 'card-body';
                
                const preElement = document.createElement('pre');
                preElement.className = 'form-control';
                preElement.style.maxHeight = '200px';
                preElement.textContent = sample.content;
                
                cardBody.appendChild(preElement);
                sampleCard.appendChild(cardBody);
                
                samplesContainer.appendChild(sampleCard);
            });
            
            // Show the modal
            const previewModal = new bootstrap.Modal(document.getElementById('previewSamplesModal'));
            previewModal.show();
            
            setStatusMessage('Sample variations generated');
        } else {
            throw new Error(response.data.error || 'Unknown error');
        }
    } catch (error) {
        console.error('Failed to preview sample variations:', error);
        setStatusMessage('Error: Failed to preview sample variations');
        await ipcRenderer.invoke('show-error-dialog', {
            title: 'Preview Error',
            message: `Failed to preview sample variations: ${error.response?.data?.error || error.message}`
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
// Parse pasted variation definitions
function parsePastedVariations(text) {
    const variationData = { variables: [], levels: {} };
    // Split text into blocks separated by blank lines
    const blocks = text.split(/\r?\n\s*\r?\n/).map(b => b.trim()).filter(b => b);
    blocks.forEach(block => {
        const lines = block.split(/\r?\n/).map(l => l.trim()).filter(l => l);
        if (lines.length < 2) return;
        const varName = lines[0];
        variationData.variables.push(varName);
        variationData.levels[varName] = [];
        lines.slice(1).forEach(line => {
            let data, value;
            if (line.includes('\t')) {
                [data, value] = line.split('\t', 2);
            } else if (line.includes(',')) {
                [data, value] = line.split(',', 2);
            } else if (line.includes('|')) {
                [data, value] = line.split('|', 2);
            } else {
                data = line;
                value = line;
            }
            data = data.trim();
            value = (value || data).trim();
            variationData.levels[varName].push({ data, value });
        });
    });
    return variationData;
}

// Handler for parsing pasted variation definitions
async function handleParsePastedDefinitions() {
    const textarea = document.getElementById('paste-variation-textarea');
    const text = textarea ? textarea.value : '';
    if (!text.trim()) {
        alert('Please paste variation definitions before parsing.');
        return;
    }
    try {
        const variationData = parsePastedVariations(text);
        if (!variationData.variables.length) {
            alert('No variables parsed. Please check the format.');
            return;
        }
        // Update session data
        currentSession.instruction_set.variation_list_data = variationData;
        // Persist to server
        setStatusMessage('Saving variation definitions...', true);
        await axios.put(`${API_BASE_URL}/session/update`, { session: currentSession });
        // Update UI
        displayVariationListData(variationData);
        document.getElementById('variation-list-empty').style.display = 'none';
        document.getElementById('variation-list-content').style.display = 'block';
        setStatusMessage('Variation definitions loaded from paste');
    } catch (error) {
        console.error('Error parsing pasted variations:', error);
        alert(`Error parsing pasted variations: ${error.message}`);
        setStatusMessage('Error: Failed to parse pasted variations');
    }
}
// Add a single pasted variable definition
async function handleAddPastedVariable() {
    const textarea = document.getElementById('paste-variation-textarea');
    const text = textarea ? textarea.value.trim() : '';
    if (!text) {
        alert('Please paste a variable definition before adding.');
        return;
    }
    const lines = text.split(/\r?\n/).map(l => l.trim()).filter(l => l);
    if (lines.length < 2) {
        alert('Please provide a variable name and at least one level.');
        return;
    }
    const varName = lines[0];
    const levelLines = lines.slice(1);
    // Ensure variation_list_data has the proper structure
    let variationData = currentSession.instruction_set.variation_list_data;
    if (!variationData || !Array.isArray(variationData.variables) || typeof variationData.levels !== 'object') {
        variationData = { variables: [], levels: {} };
        currentSession.instruction_set.variation_list_data = variationData;
    }
    if (variationData.variables.includes(varName)) {
        alert(`Variable "${varName}" already added.`);
        textarea.value = '';
        return;
    }
    variationData.variables.push(varName);
    variationData.levels[varName] = [];
    levelLines.forEach((lvl, idx) => {
        variationData.levels[varName].push({ data: (idx + 1).toString(), value: lvl });
    });
    setStatusMessage(`Adding variable "${varName}"...`, true);
    try {
        await axios.put(`${API_BASE_URL}/session/update`, { session: currentSession });
        displayVariationListData(variationData);
        textarea.value = '';
        setStatusMessage(`Variable "${varName}" added`);
    } catch (e) {
        console.error('Error adding variable via paste:', e);
        alert(`Error adding variable: ${e.message}`);
        setStatusMessage('Error: Failed to add variable');
    }
}

// Finish pasting variables
function handleFinishPastedDefinitions() {
    const section = document.getElementById('paste-variation-section');
    if (section) {
        try {
            // Collapse the paste section using Bootstrap
            if (window.bootstrap && window.bootstrap.Collapse) {
                window.bootstrap.Collapse.getOrCreateInstance(section).hide();
            } else {
                section.style.display = 'none';
            }
        } catch (e) {
            section.style.display = 'none';
        }
    }
    setStatusMessage('Finished pasting variables');
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
    // (Deprecated) Parse pasted variation definitions (for multiple blocks)
    if (document.getElementById('parse-paste-btn')) {
        document.getElementById('parse-paste-btn').addEventListener('click', () => handleParsePastedDefinitions());
    }
    // Add variable via paste
    if (document.getElementById('add-paste-btn')) {
        document.getElementById('add-paste-btn').addEventListener('click', () => handleAddPastedVariable());
    }
    // Finish pasting variables
    if (document.getElementById('finish-paste-btn')) {
        document.getElementById('finish-paste-btn').addEventListener('click', () => handleFinishPastedDefinitions());
    }
        
    // Edit variables functionality
    if (document.getElementById('edit-variations-btn')) {
        document.getElementById('edit-variations-btn').addEventListener('click', () => showEditVariablesModal());
    }
    
    if (document.getElementById('save-variable-edits-btn')) {
        document.getElementById('save-variable-edits-btn').addEventListener('click', () => saveVariableEdits());
    }
    
    if (document.getElementById('add-new-level-btn')) {
        document.getElementById('add-new-level-btn').addEventListener('click', () => addNewVariableLevel());
    }
});

// Show the edit variables modal
function showEditVariablesModal() {
    // Check if we have variation data loaded
    if (!currentSession || 
        !currentSession.instruction_set ||
        !currentSession.instruction_set.variation_list_data) {
        alert('Please load a variation definition first');
        return;
    }
    
    const variationData = currentSession.instruction_set.variation_list_data;
    const variables = variationData.variables || [];
    const levels = variationData.levels || {};
    
    // Clear existing accordion content
    editVariablesAccordion.innerHTML = '';
    
    // Populate the accordion with variables and their levels
    variables.forEach((variable, index) => {
        const variableLevels = levels[variable] || [];
        
        // Create accordion item for each variable
        const accordionItem = document.createElement('div');
        accordionItem.className = 'accordion-item';
        
        // Accordion header
        const headerId = `heading-${index}`;
        const collapseId = `collapse-${index}`;
        
        accordionItem.innerHTML = `
            <h2 class="accordion-header" id="${headerId}">
                <button class="accordion-button ${index === 0 ? '' : 'collapsed'}" type="button" 
                    data-bs-toggle="collapse" data-bs-target="#${collapseId}" 
                    aria-expanded="${index === 0 ? 'true' : 'false'}" aria-controls="${collapseId}">
                    ${variable} (${variableLevels.length} levels)
                </button>
            </h2>
            <div id="${collapseId}" class="accordion-collapse collapse ${index === 0 ? 'show' : ''}" 
                aria-labelledby="${headerId}" data-bs-parent="#editVariablesAccordion">
                <div class="accordion-body p-0">
                    <table class="table table-striped table-sm mb-0">
                        <thead>
                            <tr>
                                <th style="width: 80px;">ID</th>
                                <th>Value</th>
                                <th style="width: 100px;">Actions</th>
                            </tr>
                        </thead>
                        <tbody id="variable-levels-${index}">
                        </tbody>
                    </table>
                </div>
            </div>
        `;
        
        editVariablesAccordion.appendChild(accordionItem);
        
        // Add level rows for this variable
        const tableBody = document.getElementById(`variable-levels-${index}`);
        variableLevels.forEach((level, levelIndex) => {
            const row = document.createElement('tr');
            row.dataset.variable = variable;
            row.dataset.levelIndex = levelIndex;
            
            // ID column
            const idCell = document.createElement('td');
            idCell.textContent = level.data || '';
            row.appendChild(idCell);
            
            // Value column with editable input
            const valueCell = document.createElement('td');
            const valueInput = document.createElement('input');
            valueInput.type = 'text';
            valueInput.className = 'form-control form-control-sm level-value-input';
            valueInput.value = level.value || '';
            valueInput.dataset.variable = variable;
            valueInput.dataset.levelIndex = levelIndex;
            valueInput.dataset.levelId = level.data || '';
            valueCell.appendChild(valueInput);
            row.appendChild(valueCell);
            
            // Actions column
            const actionsCell = document.createElement('td');
            const deleteBtn = document.createElement('button');
            deleteBtn.className = 'btn btn-sm btn-danger';
            deleteBtn.innerHTML = '<i class="bi bi-trash"></i>';
            deleteBtn.dataset.variable = variable;
            deleteBtn.dataset.levelIndex = levelIndex;
            deleteBtn.addEventListener('click', () => {
                if (confirm(`Delete this level from ${variable}?`)) {
                    deleteVariableLevel(variable, levelIndex);
                }
            });
            actionsCell.appendChild(deleteBtn);
            row.appendChild(actionsCell);
            
            tableBody.appendChild(row);
        });
    });
    
    // Populate variable dropdown for new level form
    newLevelVariable.innerHTML = '';
    variables.forEach(variable => {
        const option = document.createElement('option');
        option.value = variable;
        option.textContent = variable;
        newLevelVariable.appendChild(option);
    });
    
    // Clear input fields for new level
    newLevelId.value = '';
    newLevelValue.value = '';
    
    // Show the modal
    editVariablesModal.show();
}

// Save all variable edits
async function saveVariableEdits() {
    try {
        if (!currentSession || 
            !currentSession.instruction_set || 
            !currentSession.instruction_set.variation_list_data) {
            return;
        }
        
        const variationData = currentSession.instruction_set.variation_list_data;
        
        // Collect all edited values
        const updatedLevels = {};
        
        document.querySelectorAll('.level-value-input').forEach(input => {
            const variable = input.dataset.variable;
            const levelIndex = parseInt(input.dataset.levelIndex);
            const newValue = input.value.trim();
            
            if (!updatedLevels[variable]) {
                updatedLevels[variable] = [];
            }
            
            if (variationData.levels[variable] && 
                variationData.levels[variable][levelIndex]) {
                // Only update if value has changed
                if (variationData.levels[variable][levelIndex].value !== newValue) {
                    updatedLevels[variable].push({
                        index: levelIndex,
                        data: variationData.levels[variable][levelIndex].data,
                        newValue: newValue
                    });
                }
            }
        });
        
        // Check if we have any changes
        let hasChanges = false;
        for (const variable in updatedLevels) {
            if (updatedLevels[variable].length > 0) {
                hasChanges = true;
                break;
            }
        }
        
        if (!hasChanges) {
            alert('No changes detected');
            return;
        }
        
        // Apply the changes
        for (const variable in updatedLevels) {
            for (const update of updatedLevels[variable]) {
                variationData.levels[variable][update.index].value = update.newValue;
            }
        }
        
        // Update the session
        currentSession.instruction_set.variation_list_data = variationData;
        
        // Save to server
        setStatusMessage('Saving variable changes...', true);
        
        await axios.put(`${API_BASE_URL}/session/update`, {
            session: currentSession
        });
        
        // Update UI
        displayVariationListData(variationData);
        
        // Close modal
        editVariablesModal.hide();
        
        setStatusMessage('Variable changes saved');
        
    } catch (error) {
        console.error('Failed to save variable edits:', error);
        alert(`Error saving variable changes: ${error.message}`);
        setStatusMessage('Error: Failed to save variable changes');
    }
}

// Add a new variable level
async function addNewVariableLevel() {
    try {
        if (!currentSession || 
            !currentSession.instruction_set || 
            !currentSession.instruction_set.variation_list_data) {
            return;
        }
        
        const variable = newLevelVariable.value;
        const rawId = newLevelId.value.trim();
        const rawValue = newLevelValue.value.trim();
        
        // Validate
        if (!variable) {
            alert('Please select a variable');
            return;
        }
        
        if (!rawValue) {
            alert('Please enter a value for the new level');
            return;
        }
        
        const variationData = currentSession.instruction_set.variation_list_data;
        
        // Parse values (support bulk paste: newline separated)
        const values = rawValue.split(/\r?\n/).map(v => v.trim()).filter(v => v);

        // Add each value as a new level (skip duplicates silently)
        for (const v of values) {
            // Skip if this value already exists for the variable
            if (variationData.levels[variable].some(level => level.value === v)) {
                continue;
            }
            let levelId;
            if (values.length === 1 && rawId) {
                levelId = rawId;
                // Check for duplicate ID
                if (variationData.levels[variable].some(level => level.data === levelId)) {
                    alert(`A level with ID "${levelId}" already exists for this variable`);
                    return;
                }
            } else {
                // Auto-assign a new numeric ID
                const existingIds = variationData.levels[variable]
                    .map(level => level.data)
                    .filter(id => !isNaN(parseInt(id)))
                    .map(id => parseInt(id));
                const maxId = existingIds.length > 0 ? Math.max(...existingIds) : 0;
                levelId = (maxId + 1).toString();
            }
            variationData.levels[variable].push({
                data: levelId,
                value: v
            });
        }
        
        // Update the session
        currentSession.instruction_set.variation_list_data = variationData;
        
        // Save to server
        setStatusMessage('Adding new variable level...', true);
        
        await axios.put(`${API_BASE_URL}/session/update`, {
            session: currentSession
        });
        
        // Update UI (refresh the modal)
        showEditVariablesModal();
        
        // Also update the main display
        displayVariationListData(variationData);
        
        setStatusMessage('New variable level added');
        
    } catch (error) {
        console.error('Failed to add variable level:', error);
        alert(`Error adding variable level: ${error.message}`);
        setStatusMessage('Error: Failed to add variable level');
    }
}

// Delete a variable level
async function deleteVariableLevel(variable, levelIndex) {
    try {
        if (!currentSession || 
            !currentSession.instruction_set || 
            !currentSession.instruction_set.variation_list_data) {
            return;
        }
        
        const variationData = currentSession.instruction_set.variation_list_data;
        
        // Don't allow deleting the Default level
        const levelToDelete = variationData.levels[variable][levelIndex];
        if (levelToDelete && levelToDelete.data === 'Default') {
            alert('The Default level cannot be deleted');
            return;
        }
        
        // Remove the level
        variationData.levels[variable].splice(levelIndex, 1);
        
        // Update the session
        currentSession.instruction_set.variation_list_data = variationData;
        
        // Save to server
        setStatusMessage('Deleting variable level...', true);
        
        await axios.put(`${API_BASE_URL}/session/update`, {
            session: currentSession
        });
        
        // Update UI (refresh the modal)
        showEditVariablesModal();
        
        // Also update the main display
        displayVariationListData(variationData);
        
        setStatusMessage('Variable level deleted');
        
    } catch (error) {
        console.error('Failed to delete variable level:', error);
        alert(`Error deleting variable level: ${error.message}`);
        setStatusMessage('Error: Failed to delete variable level');
    }
}
