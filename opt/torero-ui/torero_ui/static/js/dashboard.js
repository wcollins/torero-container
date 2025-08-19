// torero dashboard javascript

let refreshTimer = null;
let isRefreshing = false;

// initialize dashboard when page loads
document.addEventListener('DOMContentLoaded', function() {
    console.log('torero dashboard initialized');
    
    // start auto-refresh
    startAutoRefresh();
    
    // update last refresh time
    updateLastRefreshTime();
    
    // set up keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        if (e.key === 'r' && (e.ctrlKey || e.metaKey)) {
            e.preventDefault();
            refreshDashboard();
        }
        if (e.key === 's' && (e.ctrlKey || e.metaKey)) {
            e.preventDefault();
            syncServices();
        }
        if (e.key === 'Escape') {
            closeExecutionModal();
        }
    });
});

// auto-refresh functionality
function startAutoRefresh() {
    if (refreshTimer) {
        clearInterval(refreshTimer);
    }
    
    if (window.dashboardConfig && window.dashboardConfig.refreshInterval > 0) {
        refreshTimer = setInterval(refreshDashboard, window.dashboardConfig.refreshInterval);
        console.log(`auto-refresh started: ${window.dashboardConfig.refreshInterval}ms`);
    }
}

function stopAutoRefresh() {
    if (refreshTimer) {
        clearInterval(refreshTimer);
        refreshTimer = null;
        console.log('auto-refresh stopped');
    }
}

// refresh dashboard data
async function refreshDashboard() {
    if (isRefreshing) return;
    
    isRefreshing = true;
    const indicator = document.getElementById('refresh-indicator');
    const status = document.getElementById('refresh-status');
    
    try {
        indicator.classList.add('updating');
        status.textContent = 'Updating...';
        
        const response = await fetch(window.dashboardConfig.apiUrls.data);
        if (!response.ok) {
            throw new Error(`http error: ${response.status}`);
        }
        
        const data = await response.json();
        updateDashboardData(data);
        
        status.textContent = 'Auto-refresh enabled';
        updateLastRefreshTime();
        
    } catch (error) {
        console.error('refresh failed:', error);
        status.textContent = 'Update failed';
        
        // show error for a few seconds
        setTimeout(() => {
            status.textContent = 'Auto-refresh enabled';
        }, 3000);
        
    } finally {
        indicator.classList.remove('updating');
        isRefreshing = false;
    }
}

// update dashboard with new data
function updateDashboardData(data) {
    // update summary statistics
    updateElement('total-services', data.stats.total_services);
    updateElement('total-executions', data.stats.total_executions);
    updateElement('success-rate', `${data.stats.success_rate.toFixed(1)}%`);
    
    if (data.stats.avg_duration_seconds !== null) {
        updateElement('avg-duration', `${data.stats.avg_duration_seconds.toFixed(1)}s`);
    } else {
        updateElement('avg-duration', 'N/A');
    }
    
    // update service status
    updateServiceStatus(data.services);
    
    // update execution history
    updateExecutionHistory(data.recent_executions);
}

function updateElement(id, value) {
    const element = document.getElementById(id);
    if (element && element.textContent !== value) {
        element.textContent = value;
        // add a subtle flash effect
        element.style.transition = 'color 0.3s ease';
        element.style.color = '#5cfcfe';
        setTimeout(() => {
            element.style.color = '';
        }, 300);
    }
}

// update service status grid
function updateServiceStatus(services) {
    const container = document.getElementById('service-status');
    if (!container) return;
    
    // clear existing content
    container.innerHTML = '';
    
    if (services.length === 0) {
        container.innerHTML = `
            <div class="status-card">
                <div class="service-name">No Services</div>
                <div class="status-info">
                    <span class="status-label">Click sync to load services</span>
                </div>
            </div>
        `;
        return;
    }
    
    services.forEach(service => {
        const statusClass = service.latest_status ? `status-${service.latest_status}` : 'status-value';
        const statusText = service.latest_status ? service.latest_status.toUpperCase() : 'NEVER RUN';
        
        const card = document.createElement('div');
        card.className = 'status-card';
        card.dataset.service = service.name;
        
        card.innerHTML = `
            <div class="service-name">${service.name}</div>
            <div class="status-info">
                <span class="status-label">Type:</span>
                <span class="status-value">${service.service_type}</span>
            </div>
            <div class="status-info">
                <span class="status-label">Status:</span>
                <span class="${statusClass}">${statusText}</span>
            </div>
            <div class="status-info">
                <span class="status-label">Executions:</span>
                <span class="status-value">${service.total_executions}</span>
            </div>
            <div class="status-info">
                <span class="status-label">Success Rate:</span>
                <span class="status-success">${service.success_rate.toFixed(1)}%</span>
            </div>
        `;
        
        container.appendChild(card);
    });
}

// update execution history
function updateExecutionHistory(executions) {
    updateExecutionList('recent-executions', executions);
    updateExecutionList('successful-executions', executions.filter(e => e.status === 'success'));
    updateExecutionList('failed-executions', executions.filter(e => e.status === 'failed'));
}

function updateExecutionList(listId, executions) {
    const list = document.getElementById(listId);
    if (!list) return;
    
    list.innerHTML = '';
    
    if (executions.length === 0) {
        const emptyItem = document.createElement('li');
        emptyItem.className = 'execution-item';
        emptyItem.innerHTML = `
            <div class="execution-header">
                <span class="execution-service">No executions found</span>
            </div>
        `;
        list.appendChild(emptyItem);
        return;
    }
    
    executions.forEach(execution => {
        const item = document.createElement('li');
        item.className = 'execution-item';
        item.onclick = () => showExecutionDetails(execution.id);
        
        const startTime = new Date(execution.started_at);
        const timeStr = startTime.toLocaleDateString('en-US', { 
            month: 'short', 
            day: 'numeric', 
            hour: '2-digit', 
            minute: '2-digit' 
        });
        
        item.innerHTML = `
            <div class="execution-header">
                <span class="execution-service">${execution.service_name}</span>
                <span class="execution-status ${execution.status}">${execution.status.toUpperCase()}</span>
            </div>
            <div class="execution-details">
                <span>${execution.service_type}</span>
                <span>${timeStr}</span>
                <span>${execution.execution_time_display}</span>
            </div>
        `;
        
        list.appendChild(item);
    });
}

// sync services from torero api
async function syncServices() {
    const button = event.target;
    const originalText = button.textContent;
    
    try {
        button.textContent = 'Syncing...';
        button.disabled = true;
        
        const response = await fetch(window.dashboardConfig.apiUrls.sync, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            }
        });
        
        if (!response.ok) {
            throw new Error(`sync failed: ${response.status}`);
        }
        
        const result = await response.json();
        console.log('sync result:', result);
        
        // refresh dashboard after sync
        setTimeout(refreshDashboard, 1000);
        
    } catch (error) {
        console.error('sync error:', error);
        alert('Failed to sync services. Check console for details.');
        
    } finally {
        button.textContent = originalText;
        button.disabled = false;
    }
}

// show execution details modal
async function showExecutionDetails(executionId) {
    const modal = document.getElementById('execution-modal');
    const content = document.getElementById('execution-detail-content');
    
    try {
        content.innerHTML = '<div class="loading">Loading execution details...</div>';
        modal.classList.add('active');
        
        const url = window.dashboardConfig.apiUrls.executionDetails.replace('{id}', executionId);
        const response = await fetch(url);
        
        if (!response.ok) {
            throw new Error(`failed to load execution details: ${response.status}`);
        }
        
        const execution = await response.json();
        content.innerHTML = generateExecutionDetailHTML(execution);
        
    } catch (error) {
        console.error('error loading execution details:', error);
        content.innerHTML = `<div class="text-error">Failed to load execution details: ${error.message}</div>`;
    }
}

function generateExecutionDetailHTML(execution) {
    const startTime = new Date(execution.started_at);
    const completedTime = execution.completed_at ? new Date(execution.completed_at) : null;
    
    let html = `
        <h2 class="text-info mb-20">Execution Details</h2>
        
        <div class="execution-info">
            <div class="info-row">
                <span class="status-label">Service:</span>
                <span class="status-value">${execution.service_name}</span>
            </div>
            <div class="info-row">
                <span class="status-label">Type:</span>
                <span class="status-value">${execution.service_type}</span>
            </div>
            <div class="info-row">
                <span class="status-label">Status:</span>
                <span class="status-${execution.status}">${execution.status.toUpperCase()}</span>
            </div>
            <div class="info-row">
                <span class="status-label">Started:</span>
                <span class="status-value">${startTime.toLocaleString()}</span>
            </div>
    `;
    
    if (completedTime) {
        html += `
            <div class="info-row">
                <span class="status-label">Completed:</span>
                <span class="status-value">${completedTime.toLocaleString()}</span>
            </div>
        `;
    }
    
    if (execution.duration_seconds !== null) {
        html += `
            <div class="info-row">
                <span class="status-label">Duration:</span>
                <span class="status-value">${execution.duration_seconds.toFixed(2)}s</span>
            </div>
        `;
    }
    
    if (execution.return_code !== null) {
        html += `
            <div class="info-row">
                <span class="status-label">Return Code:</span>
                <span class="status-value">${execution.return_code}</span>
            </div>
        `;
    }
    
    html += '</div>';
    
    // add stdout if available
    if (execution.stdout) {
        html += `
            <h3 class="text-info mt-20 mb-10">Standard Output</h3>
            <div class="execution-output">${escapeHtml(execution.stdout)}</div>
        `;
    }
    
    // add stderr if available
    if (execution.stderr) {
        html += `
            <h3 class="text-error mt-20 mb-10">Standard Error</h3>
            <div class="execution-output">${escapeHtml(execution.stderr)}</div>
        `;
    }
    
    // add execution data if available
    if (execution.execution_data && Object.keys(execution.execution_data).length > 0) {
        html += `
            <h3 class="text-info mt-20 mb-10">Execution Data</h3>
            <div class="execution-output">${escapeHtml(JSON.stringify(execution.execution_data, null, 2))}</div>
        `;
    }
    
    return html;
}

function closeExecutionModal() {
    const modal = document.getElementById('execution-modal');
    modal.classList.remove('active');
}

// tab switching
function switchTab(tabName) {
    // hide all tab contents
    const contents = document.querySelectorAll('.tab-content');
    contents.forEach(content => {
        content.classList.remove('active');
    });
    
    // remove active class from all buttons
    const buttons = document.querySelectorAll('.tab-button');
    buttons.forEach(button => {
        button.classList.remove('active');
    });
    
    // show selected tab
    const targetTab = document.getElementById(tabName);
    if (targetTab) {
        targetTab.classList.add('active');
    }
    
    // mark button as active
    if (event && event.target) {
        event.target.classList.add('active');
    }
}

// utility functions
function updateLastRefreshTime() {
    const element = document.getElementById('last-update');
    if (element) {
        const now = new Date();
        element.textContent = `Last update: ${now.toLocaleTimeString()}`;
    }
}

function getCsrfToken() {
    const cookieValue = document.cookie
        .split('; ')
        .find(row => row.startsWith('csrftoken='))
        ?.split('=')[1];
    return cookieValue || '';
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// close modal when clicking outside
window.onclick = function(event) {
    const modal = document.getElementById('execution-modal');
    if (event.target === modal) {
        closeExecutionModal();
    }
};