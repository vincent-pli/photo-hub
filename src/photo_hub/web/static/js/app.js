// photo-hub Web Interface
const API_BASE = 'http://localhost:8000/api';

// DOM elements
let currentScanTaskId = null;
let scanInterval = null;

// Initialize app after i18n is ready
function initApp() {
    // Navigation already handled in inline script
    
    // Set up browse button (simulated)
    document.getElementById('browse-btn').addEventListener('click', function() {
        // In a real app, this would open a directory picker
        // For now, just show a prompt
        const path = prompt(t('scan.browsePrompt'));
        if (path) {
            document.getElementById('directory').value = path;
        }
    });
    
    // Start scan button
    document.getElementById('start-scan').addEventListener('click', startScan);
    
    // Search button
    document.getElementById('search-btn').addEventListener('click', performSearch);
    
    // Load initial data
    loadRecentScans();
    loadStats();
}

// API Helper Functions
async function apiRequest(endpoint, method = 'GET', data = null) {
    const url = `${API_BASE}${endpoint}`;
    const options = {
        method: method,
        headers: {
            'Content-Type': 'application/json',
        },
    };
    
    if (data && (method === 'POST' || method === 'PUT')) {
        options.body = JSON.stringify(data);
    }
    
    try {
        const response = await fetch(url, options);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        return await response.json();
    } catch (error) {
        console.error('API request failed:', error);
        showError(`API Error: ${error.message}`);
        throw error;
    }
}

function showError(message) {
    showStatus(message, 'error');
}

function showSuccess(message) {
    showStatus(message, 'success');
}

function showInfo(message) {
    showStatus(message, 'info');
}

// Helper to get i18n translation
function t(key, params = {}) {
    return window.i18n ? window.i18n.t(key, params) : key;
}

function showStatus(message, type = 'info') {
    // Clear any existing status
    const statusEl = document.getElementById('scan-status');
    if (!statusEl) return;
    
    statusEl.textContent = message;
    statusEl.className = 'status-message';
    
    switch (type) {
        case 'error':
            statusEl.classList.add('status-error');
            break;
        case 'success':
            statusEl.classList.add('status-success');
            break;
        case 'info':
            statusEl.classList.add('status-info');
            break;
    }
    
    statusEl.style.display = 'block';
}

// Scan Functions
async function startScan() {
    const directory = document.getElementById('directory').value.trim();
    if (!directory) {
        showError(t('scan.enterDirectory'));
        return;
    }
    
    const recursive = document.getElementById('recursive').checked;
    const skipExisting = document.getElementById('skip-existing').checked;
    
    // Disable button and show progress
    const button = document.getElementById('start-scan');
    button.disabled = true;
    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> ' + t('scan.starting');
    
    document.getElementById('scan-progress').style.display = 'block';
    showInfo(t('scan.starting'));
    
    try {
        const data = {
            directory: directory,
            recursive: recursive,
            skip_existing: skipExisting
        };
        
        const response = await apiRequest('/scan', 'POST', data);
        currentScanTaskId = response.task_id;
        
        showInfo(t('scan.taskStarted', { taskId: response.task_id }));
        
        // Start polling for progress
        if (scanInterval) clearInterval(scanInterval);
        scanInterval = setInterval(() => pollScanStatus(response.task_id), 2000);
        
    } catch (error) {
        button.disabled = false;
        button.innerHTML = '<i class="fas fa-play"></i> ' + t('scan.startScan');
        showError(t('scan.failed', { error: error.message }));
    }
}

async function pollScanStatus(taskId) {
    try {
        const status = await apiRequest(`/scan/${taskId}`);
        
        // Update progress
        const progress = (status.progress * 100).toFixed(1);
        document.getElementById('progress-bar').style.width = `${progress}%`;
        document.getElementById('progress-text').textContent = `${progress}%`;
        
        // Update file counts
        if (status.total_files !== null) {
            const processed = status.processed_files || 0;
            const total = status.total_files;
            document.getElementById('file-count').textContent = 
                t('scan.filesProcessed', { processed, total });
        }
        
        // Update current file
        if (status.current_file) {
            document.getElementById('current-file').textContent = 
                t('scan.processingFile', { file: status.current_file });
        }
        
        // Update status message
        if (status.status === 'scanning') {
            showInfo(t('scan.scanning'));
        } else if (status.status === 'analyzing') {
            showInfo(t('scan.analyzing'));
        } else if (status.status === 'completed') {
            clearInterval(scanInterval);
            const analyzed = status.successful_analyses || 0;
            const skipped = status.skipped_files || 0;
            if (skipped > 0) {
                showSuccess(t('scan.completed', { analyzed, skipped }));
            } else {
                showSuccess(t('scan.completedNoSkip', { analyzed }));
            }
            
            // Re-enable button
            const button = document.getElementById('start-scan');
            button.disabled = false;
            button.innerHTML = '<i class="fas fa-play"></i> ' + t('scan.startScan');
            
            // Reload recent scans and stats
            loadRecentScans();
            loadStats();
            
        } else if (status.status === 'error') {
            clearInterval(scanInterval);
            showError(t('scan.failed', { error: status.error_message || 'Unknown error' }));
            
            // Re-enable button
            const button = document.getElementById('start-scan');
            button.disabled = false;
            button.innerHTML = '<i class="fas fa-play"></i> ' + t('scan.startScan');
        }
        
    } catch (error) {
        console.error('Failed to poll scan status:', error);
    }
}

async function loadRecentScans() {
    const container = document.getElementById('recent-scans');
    if (!container) return;
    
    try {
        const scans = await apiRequest('/scan?limit=5');
        
        if (scans.length === 0) {
            container.innerHTML = '<p>' + t('recentScans.none') + '</p>';
            return;
        }
        
        let html = '<div class="recent-scans-list">';
        scans.forEach(scan => {
            const started = new Date(scan.started_at).toLocaleString();
            const statusClass = scan.status === 'completed' ? 'status-success' : 
                               scan.status === 'error' ? 'status-error' : 'status-info';
            
            html += `
                 <div class="status-message ${statusClass}" style="margin-bottom: 15px;">
                    <strong>${started}</strong><br>
                    ${t('recentScans.directory', { directory: scan.request?.directory || 'Unknown' })}<br>
                    ${t('recentScans.status', { status: scan.status, progress: (scan.progress * 100).toFixed(1) })}<br>
                    ${scan.successful_analyses ? t('recentScans.photosAnalyzed', { count: scan.successful_analyses }) : ''}
                    ${scan.skipped_files ? ' | ' + t('recentScans.skipped', { count: scan.skipped_files }) : ''}
                </div>
            `;
        });
        html += '</div>';
        
        container.innerHTML = html;
    } catch (error) {
        container.innerHTML = '<p class="status-error">' + t('recentScans.failed') + '</p>';
    }
}

// Search Functions
async function performSearch() {
    const query = document.getElementById('search-query').value.trim();
    if (!query) {
        showError(t('search.enterTerms'));
        return;
    }
    
    const limit = document.getElementById('search-limit').value;
    const button = document.getElementById('search-btn');
    const resultsContainer = document.getElementById('search-results');
    
    button.disabled = true;
    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> ' + t('search.searching');
    resultsContainer.innerHTML = '<div class="loading"><div class="loading-spinner"></div><p>' + t('search.searching') + '</p></div>';
    
    try {
        const data = {
            query: query,
            limit: parseInt(limit)
        };
        
        const response = await apiRequest('/search', 'POST', data);
        displaySearchResults(response.results, response.total);
        
    } catch (error) {
        resultsContainer.innerHTML = '<p class="status-error">' + t('search.failed') + '</p>';
    } finally {
        button.disabled = false;
        button.innerHTML = '<i class="fas fa-search"></i> ' + t('search.searchButton');
    }
}

function displaySearchResults(results, total) {
    const container = document.getElementById('search-results');
    
    if (!results || results.length === 0) {
        container.innerHTML = '<p class="status-info">' + t('search.noResults') + '</p>';
        return;
    }
    
    let html = `<p style="margin-bottom: 20px; color: #475569;">${t('search.foundResults', { total })}</p>`;
    html += '<div class="photo-grid">';
    
    results.forEach(photo => {
        const filename = photo.filename || 'Unknown';
        const description = photo.description ? 
            (photo.description.length > 150 ? photo.description.substring(0, 150) + '...' : photo.description) : 
            t('search.noDescription');
        
        const tags = photo.tags ? photo.tags.slice(0, 5).join(', ') : '';
        
        html += `
            <div class="photo-card">
                <div class="photo-thumbnail">
                    <i class="fas fa-image"></i>
                </div>
                <div class="photo-info">
                    <div class="photo-title">${filename}</div>
                    <div class="photo-description">${description}</div>
                    ${tags ? `<div style="margin-top: 10px; font-size: 0.8rem; color: #4f46e5;"><i class="fas fa-tags"></i> ${tags}</div>` : ''}
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    container.innerHTML = html;
}

// Stats Functions
async function loadStats() {
    const container = document.getElementById('stats-content');
    if (!container) return;
    
    try {
        const stats = await apiRequest('/stats');
        
        const html = `
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-number">${stats.total_photos}</div>
                    <div class="stat-label">${t('stats.totalPhotos')}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">${stats.total_analyses}</div>
                    <div class="stat-label">${t('stats.totalAnalyses')}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">${stats.models_used}</div>
                    <div class="stat-label">${t('stats.modelsUsed')}</div>
                </div>
            </div>
            <div style="margin-top: 30px; color: #64748b;">
                <p><i class="fas fa-database"></i> ${t('stats.database', { path: stats.database_path })}</p>
            </div>
        `;
        
        container.innerHTML = html;
    } catch (error) {
        container.innerHTML = '<p class="status-error">' + t('stats.failed') + '</p>';
    }
}

// Health check on startup
async function checkApiHealth() {
    try {
        const response = await fetch(`${API_BASE}/health`);
        if (response.ok) {
            console.log('API is healthy');
        } else {
            console.warn('API health check failed');
        }
    } catch (error) {
        console.error('API is not reachable:', error);
        showError(t('api.connectionError'));
    }
}

// Run health check after a short delay
setTimeout(checkApiHealth, 1000);