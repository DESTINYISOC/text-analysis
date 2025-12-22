// Configuration
const API_BASE_URL = 'http://localhost:5000';
let responseTime = 0;

// DOM Elements
const apiStatus = document.getElementById('apiStatus');
const statusText = document.getElementById('statusText');
const apiStatusBadge = document.getElementById('apiStatusBadge');
const baseUrlElement = document.getElementById('baseUrl');
const responseTimeElement = document.getElementById('responseTime');
const rawResponse = document.getElementById('rawResponse');

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    baseUrlElement.textContent = API_BASE_URL;
    checkApiStatus();
    setupEventListeners();
});

// Event Listeners
function setupEventListeners() {
    // Tab switching
    document.querySelectorAll('.tab').forEach(tab => {
        tab.addEventListener('click', () => {
            const tabId = tab.getAttribute('data-tab');
            switchTab(tabId);
        });
    });
    
    // Range inputs
    document.getElementById('augmentationCount').addEventListener('input', function() {
        document.getElementById('countValue').textContent = this.value;
    });
    
    document.getElementById('summarySentences').addEventListener('input', function() {
        document.getElementById('summaryCount').textContent = this.value;
    });
    
    document.getElementById('topNKeywords').addEventListener('input', function() {
        document.getElementById('keywordsCount').textContent = this.value;
    });
}

// Tab Management
function switchTab(tabId) {
    // Update active tab
    document.querySelectorAll('.tab').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelector(`[data-tab="${tabId}"]`).classList.add('active');
    
    // Show active content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(`${tabId}Tab`).classList.add('active');
}

// Batch Form Management
function showBatchType(type) {
    document.querySelectorAll('.batch-form').forEach(form => {
        form.style.display = 'none';
    });
    document.getElementById(`batch${type.charAt(0).toUpperCase() + type.slice(1)}Form`).style.display = 'block';
}

// Premium Tab Management
function showPremiumTab(tab) {
    document.querySelectorAll('.premium-tab').forEach(tab => {
        tab.classList.remove('active');
    });
    event.target.classList.add('active');
    
    document.querySelectorAll('.premium-form').forEach(form => {
        form.style.display = 'none';
    });
    document.getElementById(`${tab}Form`).style.display = 'block';
}

// API Status Check
async function checkApiStatus() {
    try {
        const startTime = Date.now();
        const response = await fetch(`${API_BASE_URL}/health/`);
        responseTime = Date.now() - startTime;
        
        if (response.ok) {
            apiStatus.classList.add('active');
            statusText.textContent = 'API Active';
            apiStatusBadge.textContent = 'Active';
            responseTimeElement.textContent = `${responseTime} ms`;
        } else {
            throw new Error('API not responding');
        }
    } catch (error) {
        apiStatus.classList.remove('active');
        statusText.textContent = 'API Offline';
        apiStatusBadge.textContent = 'Offline';
        responseTimeElement.textContent = '-- ms';
        showToast('API is offline. Make sure the server is running.', 'error');
    }
}

// API Test Functions
async function testEnrichText() {
    const text = document.getElementById('enrichText').value;
    const augmentationCount = document.getElementById('augmentationCount').value;
    
    if (!text.trim()) {
        showToast('Please enter some text', 'warning');
        return;
    }
    
    showLoading('enrichResult', 'Processing text enrichment...');
    
    try {
        const startTime = Date.now();
        const response = await fetch(`${API_BASE_URL}/api/v1/enrich/text`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                text, 
                augmentation_count: parseInt(augmentationCount) 
            })
        });
        
        responseTime = Date.now() - startTime;
        updateResponseTime();
        
        const data = await response.json();
        displayRawResponse(data);
        
        if (response.ok) {
            displayEnrichmentResults(data);
        } else {
            showToast(`Error: ${data.message || 'Unknown error'}`, 'error');
        }
    } catch (error) {
        showToast(`Network error: ${error.message}`, 'error');
    }
}

async function testSentimentAnalysis() {
    const text = document.getElementById('sentimentText').value;
    const detailed = document.getElementById('detailedAnalysis').checked;
    
    if (!text.trim()) {
        showToast('Please enter some text', 'warning');
        return;
    }
    
    showLoading('sentimentResult', 'Analyzing sentiment...');
    
    try {
        const startTime = Date.now();
        const response = await fetch(`${API_BASE_URL}/api/v1/analyze/sentiment`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text, detailed })
        });
        
        responseTime = Date.now() - startTime;
        updateResponseTime();
        
        const data = await response.json();
        displayRawResponse(data);
        
        if (response.ok) {
            displaySentimentResults(data);
        } else {
            showToast(`Error: ${data.message || 'Unknown error'}`, 'error');
        }
    } catch (error) {
        showToast(`Network error: ${error.message}`, 'error');
    }
}

async function testBatchTwo() {
    const texts = Array.from(document.querySelectorAll('.batch-text')).map(t => t.value);
    
    if (texts.some(t => !t.trim())) {
        showToast('Please fill in all text fields', 'warning');
        return;
    }
    
    showLoading('batchResult', 'Processing batch...');
    
    try {
        const startTime = Date.now();
        const response = await fetch(`${API_BASE_URL}/api/v1/enrich/two`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                texts: texts.map(text => ({ text, augmentation_count: 2 }))
            })
        });
        
        responseTime = Date.now() - startTime;
        updateResponseTime();
        
        const data = await response.json();
        displayRawResponse(data);
        
        if (response.ok) {
            displayBatchResults(data);
        } else {
            showToast(`Error: ${data.message || 'Unknown error'}`, 'error');
        }
    } catch (error) {
        showToast(`Network error: ${error.message}`, 'error');
    }
}

async function testSummarization() {
    const text = document.getElementById('summarizeText').value;
    const sentences = document.getElementById('summarySentences').value;
    
    if (!text.trim()) {
        showToast('Please enter some text', 'warning');
        return;
    }
    
    showLoading('premiumResult', 'Generating summary...');
    
    try {
        const startTime = Date.now();
        const response = await fetch(`${API_BASE_URL}/api/v1/summarize`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text, sentences: parseInt(sentences) })
        });
        
        responseTime = Date.now() - startTime;
        updateResponseTime();
        
        const data = await response.json();
        displayRawResponse(data);
        
        if (response.ok) {
            displaySummarizationResults(data);
        } else {
            showToast(`Error: ${data.message || 'Unknown error'}`, 'error');
        }
    } catch (error) {
        showToast(`Network error: ${error.message}`, 'error');
    }
}

async function testKeywordExtraction() {
    const text = document.getElementById('keywordsText').value;
    const top_n = document.getElementById('topNKeywords').value;
    
    if (!text.trim()) {
        showToast('Please enter some text', 'warning');
        return;
    }
    
    showLoading('premiumResult', 'Extracting keywords...');
    
    try {
        const startTime = Date.now();
        const response = await fetch(`${API_BASE_URL}/api/v1/keywords`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text, top_n: parseInt(top_n) })
        });
        
        responseTime = Date.now() - startTime;
        updateResponseTime();
        
        const data = await response.json();
        displayRawResponse(data);
        
        if (response.ok) {
            displayKeywordResults(data);
        } else {
            showToast(`Error: ${data.message || 'Unknown error'}`, 'error');
        }
    } catch (error) {
        showToast(`Network error: ${error.message}`, 'error');
    }
}

// Display Functions
function displayEnrichmentResults(data) {
    const container = document.getElementById('enrichResult');
    
    if (!data.success) {
        container.innerHTML = `
            <h3>Error:</h3>
            <div class="error-message">${data.message}</div>
        `;
        return;
    }
    
    const result = data.data;
    const sentiment = result.sentiment;
    
    let html = `
        <h3><i class="fas fa-check-circle" style="color: #10b981;"></i> Enrichment Results</h3>
        
        <div class="sentiment-display">
            <div class="sentiment-emoji">${sentiment.emoji}</div>
            <div>
                <div class="sentiment-label">${sentiment.label}</div>
                <div style="color: #64748b; font-size: 0.9rem;">
                    Polarity: ${sentiment.polarity} • Subjectivity: ${sentiment.subjectivity}
                </div>
            </div>
            <div class="sentiment-score">Confidence: ${Math.round(sentiment.confidence * 100)}%</div>
        </div>
        
        <div style="margin: 20px 0; padding: 15px; background: #f8fafc; border-radius: 10px;">
            <strong>Original:</strong> ${result.original}
        </div>
        
        <h4>Augmented Versions (${result.augmentations.length}):</h4>
        <div class="augmentations-list">
    `;
    
    result.augmentations.forEach((aug, index) => {
        html += `
            <div class="augmentation-item">
                <strong>Version ${index + 1}:</strong> ${aug}
            </div>
        `;
    });
    
    html += `
        </div>
        
        <div style="margin-top: 20px; padding: 15px; background: #f1f5f9; border-radius: 10px;">
            <strong>Metadata:</strong><br>
            • Words: ${result.metadata.word_count}<br>
            • Replaceable Words: ${result.metadata.replaceable_words}<br>
            • Processing Time: ${result.metadata.processing_time_ms}ms
        </div>
    `;
    
    container.innerHTML = html;
}

function displaySentimentResults(data) {
    const container = document.getElementById('sentimentResult');
    
    if (!data.success) {
        container.innerHTML = `
            <h3>Error:</h3>
            <div class="error-message">${data.message}</div>
        `;
        return;
    }
    
    const result = data.data;
    const sentiment = result.sentiment;
    
    let html = `
        <h3><i class="fas fa-chart-bar" style="color: #3b82f6;"></i> Sentiment Analysis</h3>
        
        <div class="sentiment-display">
            <div class="sentiment-emoji">${sentiment.emoji}</div>
            <div>
                <div class="sentiment-label">${sentiment.label}</div>
                <div style="color: #64748b; font-size: 0.9rem;">
                    Tone: ${result.tone || 'N/A'}
                </div>
            </div>
            <div class="sentiment-score">${sentiment.polarity > 0 ? '+' : ''}${sentiment.polarity}</div>
        </div>
        
        <div style="margin: 15px 0;">
            <div style="background: linear-gradient(90deg, #ef4444 ${Math.max(0, -sentiment.polarity) * 50}%, #10b981 ${Math.max(0, sentiment.polarity) * 50}%); 
                    height: 8px; border-radius: 4px; margin: 10px 0;"></div>
            <div style="display: flex; justify-content: space-between; color: #64748b; font-size: 0.9rem;">
                <span>Negative</span>
                <span>Neutral</span>
                <span>Positive</span>
            </div>
        </div>
        
        <div style="margin: 20px 0; padding: 15px; background: #f8fafc; border-radius: 10px;">
            <strong>Text Analyzed:</strong> ${result.original.substring(0, 150)}${result.original.length > 150 ? '...' : ''}
        </div>
        
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-top: 20px;">
            <div style="padding: 15px; background: #fef3c7; border-radius: 10px;">
                <strong>Polarity</strong><br>
                <span style="font-size: 1.5rem; font-weight: 700; color: #d97706;">${sentiment.polarity}</span>
            </div>
            <div style="padding: 15px; background: #dbeafe; border-radius: 10px;">
                <strong>Subjectivity</strong><br>
                <span style="font-size: 1.5rem; font-weight: 700; color: #1d4ed8;">${sentiment.subjectivity}</span>
            </div>
        </div>
        
        <div style="margin-top: 20px; padding: 15px; background: #f1f5f9; border-radius: 10px;">
            <strong>Metadata:</strong><br>
            • Word Count: ${result.metadata.word_count}<br>
            • Character Count: ${result.metadata.character_count}<br>
            • Confidence: ${Math.round(sentiment.confidence * 100)}%
        </div>
    `;
    
    if (result.detailed_analysis) {
        html += `
            <h4 style="margin-top: 20px;">Detailed Analysis:</h4>
            <div style="max-height: 200px; overflow-y: auto; padding: 10px; background: #f8fafc; border-radius: 8px;">
                ${JSON.stringify(result.detailed_analysis, null, 2)}
            </div>
        `;
    }
    
    container.innerHTML = html;
}

function displayBatchResults(data) {
    const container = document.getElementById('batchResult');
    
    if (!data.success) {
        container.innerHTML = `
            <h3>Error:</h3>
            <div class="error-message">${data.message}</div>
        `;
        return;
    }
    
    const results = data.data.results;
    const metadata = data.data.batch_metadata;
    
    let html = `
        <h3><i class="fas fa-layer-group" style="color: #8b5cf6;"></i> Batch Processing Results</h3>
        
        <div style="margin-bottom: 20px; padding: 15px; background: linear-gradient(135deg, #8b5cf6, #7c3aed); color: white; border-radius: 10px;">
            <strong>Batch Summary:</strong><br>
            • Processed: ${metadata.text_count} texts<br>
            • Parallel Processing: ${metadata.parallel_processing ? 'Yes' : 'No'}<br>
            • Total Time: ${metadata.processing_time_ms}ms
        </div>
    `;
    
    results.forEach((result, index) => {
        const sentiment = result.sentiment;
        html += `
            <div style="margin: 15px 0; padding: 15px; border: 2px solid #e2e8f0; border-radius: 10px;">
                <h4>Text ${index + 1}: ${result.success ? '✅' : '❌'}</h4>
                <div style="margin: 10px 0; padding: 10px; background: #f8fafc; border-radius: 8px;">
                    <strong>Original:</strong> ${result.original.substring(0, 100)}${result.original.length > 100 ? '...' : ''}
                </div>
        `;
        
        if (result.success) {
            html += `
                <div style="display: flex; align-items: center; gap: 10px; margin: 10px 0;">
                    <span style="font-size: 1.5rem;">${sentiment.emoji}</span>
                    <span><strong>${sentiment.label}</strong> (${sentiment.polarity})</span>
                </div>
                <div style="color: #64748b;">
                    Augmentations: ${result.augmentations ? result.augmentations.length : 0}
                </div>
            `;
        } else {
            html += `<div style="color: #ef4444;">Error: ${result.error}</div>`;
        }
        
        html += `</div>`;
    });
    
    container.innerHTML = html;
}

function displaySummarizationResults(data) {
    const container = document.getElementById('premiumResult');
    
    if (!data.success) {
        container.innerHTML = `
            <h3>Error:</h3>
            <div class="error-message">${data.message}</div>
        `;
        return;
    }
    
    const result = data.data;
    const metrics = result.metrics;
    
    let html = `
        <h3><i class="fas fa-file-contract" style="color: #f59e0b;"></i> Text Summarization</h3>
        
        <div style="margin: 20px 0; padding: 15px; background: #f8fafc; border-radius: 10px;">
            <strong>Original Text (${metrics.original_words} words):</strong><br>
            ${result.original}
        </div>
        
        <div style="margin: 20px 0; padding: 15px; background: #fef3c7; border-radius: 10px; border-left: 4px solid #f59e0b;">
            <strong>Summary (${metrics.summary_words} words):</strong><br>
            ${result.summary}
        </div>
        
        <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 15px; margin-top: 20px;">
            <div style="padding: 15px; background: #f1f5f9; border-radius: 10px; text-align: center;">
                <div style="font-size: 0.9rem; color: #64748b;">Reduction</div>
                <div style="font-size: 1.8rem; font-weight: 700; color: #10b981;">${metrics.reduction_percent}%</div>
            </div>
            <div style="padding: 15px; background: #f1f5f9; border-radius: 10px; text-align: center;">
                <div style="font-size: 0.9rem; color: #64748b;">Sentences</div>
                <div style="font-size: 1.8rem; font-weight: 700; color: #3b82f6;">${metrics.original_sentences} → ${metrics.summary_sentences}</div>
            </div>
            <div style="padding: 15px; background: #f1f5f9; border-radius: 10px; text-align: center;">
                <div style="font-size: 0.9rem; color: #64748b;">Time</div>
                <div style="font-size: 1.8rem; font-weight: 700; color: #8b5cf6;">${metrics.processing_time_ms}ms</div>
            </div>
        </div>
    `;
    
    container.innerHTML = html;
}

function displayKeywordResults(data) {
    const container = document.getElementById('premiumResult');
    
    if (!data.success) {
        container.innerHTML = `
            <h3>Error:</h3>
            <div class="error-message">${data.message}</div>
        `;
        return;
    }
    
    const result = data.data;
    const keywords = result.keywords;
    const metrics = result.metrics;
    
    let html = `
        <h3><i class="fas fa-key" style="color: #10b981;"></i> Keyword Extraction</h3>
        
        <div style="margin: 20px 0; padding: 15px; background: #f8fafc; border-radius: 10px;">
            <strong>Analyzed Text (${metrics.words_analyzed} words):</strong><br>
            ${result.original}
        </div>
        
        <h4>Top Keywords:</h4>
        <div class="keywords-container">
    `;
    
    keywords.forEach(keyword => {
        const importance = keyword.importance_score;
        let color;
        if (importance > 10) color = '#ef4444';
        else if (importance > 5) color = '#f59e0b';
        else color = '#10b981';
        
        html += `
            <div class="keyword-tag" style="background: linear-gradient(135deg, ${color}, ${color}dd);">
                ${keyword.keyword} <small>(${importance}%)</small>
            </div>
        `;
    });
    
    html += `
        </div>
        
        <div style="margin-top: 20px; padding: 15px; background: #f1f5f9; border-radius: 10px;">
            <strong>Analysis Metrics:</strong><br>
            • Total Keywords Found: ${metrics.total_keywords_found}<br>
            • Text Complexity: ${metrics.text_complexity}/100<br>
            • Processing Time: ${metrics.processing_time_ms}ms
        </div>
        
        <div style="margin-top: 20px; max-height: 200px; overflow-y: auto;">
            <table style="width: 100%; border-collapse: collapse;">
                <thead>
                    <tr style="background: #e2e8f0;">
                        <th style="padding: 10px; text-align: left;">Keyword</th>
                        <th style="padding: 10px; text-align: left;">Frequency</th>
                        <th style="padding: 10px; text-align: left;">Importance</th>
                        <th style="padding: 10px; text-align: left;">Category</th>
                    </tr>
                </thead>
                <tbody>
    `;
    
    keywords.forEach(keyword => {
        html += `
            <tr style="border-bottom: 1px solid #e2e8f0;">
                <td style="padding: 10px;">${keyword.keyword}</td>
                <td style="padding: 10px;">${keyword.frequency}</td>
                <td style="padding: 10px;">${keyword.importance_score}%</td>
                <td style="padding: 10px;">
                    <span style="padding: 4px 8px; background: #f1f5f9; border-radius: 4px; font-size: 0.8rem;">
                        ${keyword.category}
                    </span>
                </td>
            </tr>
        `;
    });
    
    html += `
                </tbody>
            </table>
        </div>
    `;
    
    container.innerHTML = html;
}

// Utility Functions
function showLoading(elementId, message = 'Loading...') {
    const container = document.getElementById(elementId);
    container.innerHTML = `
        <h3>Processing...</h3>
        <div style="text-align: center; padding: 40px;">
            <div class="spinner"></div>
            <p style="color: #64748b; margin-top: 15px;">${message}</p>
        </div>
    `;
    
    // Add spinner CSS
    if (!document.querySelector('#spinner-style')) {
        const style = document.createElement('style');
        style.id = 'spinner-style';
        style.textContent = `
            .spinner {
                border: 4px solid #f1f5f9;
                border-top: 4px solid #4f46e5;
                border-radius: 50%;
                width: 40px;
                height: 40px;
                animation: spin 1s linear infinite;
                margin: 0 auto;
            }
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
        `;
        document.head.appendChild(style);
    }
}

function displayRawResponse(data) {
    rawResponse.textContent = JSON.stringify(data, null, 2);
    
    // Syntax highlighting for JSON
    rawResponse.innerHTML = rawResponse.textContent
        .replace(/("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g, 
        match => {
            let cls = 'number';
            if (/^"/.test(match)) {
                if (/:$/.test(match)) {
                    cls = 'key';
                } else {
                    cls = 'string';
                }
            } else if (/true|false/.test(match)) {
                cls = 'boolean';
            } else if (/null/.test(match)) {
                cls = 'null';
            }
            return `<span class="${cls}">${match}</span>`;
        });
    
    // Add CSS for syntax highlighting
    if (!document.querySelector('#json-highlight')) {
        const style = document.createElement('style');
        style.id = 'json-highlight';
        style.textContent = `
            #rawResponse .string { color: #10b981; }
            #rawResponse .number { color: #3b82f6; }
            #rawResponse .boolean { color: #f59e0b; }
            #rawResponse .null { color: #ef4444; }
            #rawResponse .key { color: #8b5cf6; }
        `;
        document.head.appendChild(style);
    }
}

function updateResponseTime() {
    responseTimeElement.textContent = `${responseTime} ms`;
}

function copyToClipboard(elementId) {
    const text = document.getElementById(elementId).textContent;
    navigator.clipboard.writeText(text).then(() => {
        showToast('Copied to clipboard!', 'success');
    });
}

function copyEndpoint(path, method) {
    const endpoint = `${API_BASE_URL}${path}`;
    navigator.clipboard.writeText(endpoint).then(() => {
        showToast(`${method} ${path} copied!`, 'success');
    });
}

function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    
    // Set color based on type
    if (type === 'success') toast.style.background = '#10b981';
    else if (type === 'error') toast.style.background = '#ef4444';
    else if (type === 'warning') toast.style.background = '#f59e0b';
    else toast.style.background = '#3b82f6';
    
    toast.classList.add('show');
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

// Export functions for HTML onclick attributes
window.testEnrichText = testEnrichText;
window.testSentimentAnalysis = testSentimentAnalysis;
window.testBatchTwo = testBatchTwo;
window.testBatchThree = testBatchThree;
window.testSummarization = testSummarization;
window.testKeywordExtraction = testKeywordExtraction;
window.showBatchType = showBatchType;
window.showPremiumTab = showPremiumTab;
window.copyToClipboard = copyToClipboard;
window.copyEndpoint = copyEndpoint;