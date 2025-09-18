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
        
        // Determine logo based on service type
        let logoHtml = '';
        if (service.service_type === 'ansible-playbook') {
            logoHtml = '<img src="/static/img/ansible.svg" alt="Ansible" class="service-logo">';
        } else if (service.service_type === 'opentofu-plan') {
            logoHtml = '<img src="/static/img/opentofu.svg" alt="OpenTofu" class="service-logo">';
        } else if (service.service_type === 'python-script') {
            logoHtml = '<img src="/static/img/python.svg" alt="Python" class="service-logo">';
        }
        
        const card = document.createElement('div');
        card.className = 'status-card';
        card.dataset.service = service.name;
        
        card.innerHTML = `
            <div class="service-header">
                ${logoHtml}
                <div class="service-name">${service.name}</div>
            </div>
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
            <div class="execute-container">
                <button class="execute-btn execute-icon-btn" onclick="showInputForm('${service.name}', '${service.type || service.service_type}')" title="Execute Service">
                    <img src="/static/img/execute.svg" alt="Execute" class="execute-icon">
                    <span class="btn-spinner" style="display: none;">
                        <span class="spinner"></span>
                    </span>
                </button>
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
        
        // Determine logo based on service type
        let logoHtml = '';
        if (execution.service_type === 'ansible-playbook') {
            logoHtml = '<img src="/static/img/ansible.svg" alt="Ansible" class="execution-logo">';
        } else if (execution.service_type === 'opentofu-plan') {
            logoHtml = '<img src="/static/img/opentofu.svg" alt="OpenTofu" class="execution-logo">';
        } else if (execution.service_type === 'python-script') {
            logoHtml = '<img src="/static/img/python.svg" alt="Python" class="execution-logo">';
        }
        
        item.innerHTML = `
            <div class="execution-header">
                <div class="execution-service-with-logo">
                    ${logoHtml}
                    <span class="execution-service">${execution.service_name}</span>
                </div>
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

        // parse execution_data if it's a json string
        if (execution.execution_data && typeof execution.execution_data === 'string') {
            try {
                execution.execution_data = JSON.parse(execution.execution_data);
            } catch (e) {
                console.error('Failed to parse execution_data as JSON:', e);
            }
        }

        content.innerHTML = generateExecutionDetailHTML(execution);

    } catch (error) {
        console.error('error loading execution details:', error);
        content.innerHTML = `<div class="text-error">Failed to load execution details: ${error.message}</div>`;
    }
}

function generateExecutionDetailHTML(execution) {
    // handle raw execution data without wrapper fields
    if (!execution.service_name && !execution.status && execution.stdout !== undefined) {
        return formatOpenTofuOutput(execution);
    }

    const startTime = execution.started_at ? new Date(execution.started_at) : null;
    const completedTime = execution.completed_at ? new Date(execution.completed_at) : null;

    let html = `
        <h2 class="text-info mb-20">Execution Details</h2>

        <div class="execution-info">
            ${execution.service_name ? `
            <div class="info-row">
                <span class="status-label">Service:</span>
                <span class="status-value">${execution.service_name}</span>
            </div>
            ` : ''}
            ${execution.service_type ? `
            <div class="info-row">
                <span class="status-label">Type:</span>
                <span class="status-value">${execution.service_type}</span>
            </div>
            ` : ''}
            ${execution.status ? `
            <div class="info-row">
                <span class="status-label">Status:</span>
                <span class="status-${execution.status}">${execution.status.toUpperCase()}</span>
            </div>
            ` : ''}
            ${startTime ? `
            <div class="info-row">
                <span class="status-label">Started:</span>
                <span class="status-value">${startTime.toLocaleString()}</span>
            </div>
            ` : ''}
    `;
    
    if (completedTime) {
        html += `
            <div class="info-row">
                <span class="status-label">Completed:</span>
                <span class="status-value">${completedTime.toLocaleString()}</span>
            </div>
        `;
    }

    if (execution.duration_seconds !== null && execution.duration_seconds !== undefined) {
        html += `
            <div class="info-row">
                <span class="status-label">Duration:</span>
                <span class="status-value">${execution.duration_seconds.toFixed(2)}s</span>
            </div>
        `;
    }

    if (execution.return_code !== null && execution.return_code !== undefined) {
        html += `
            <div class="info-row">
                <span class="status-label">Return Code:</span>
                <span class="status-value">${execution.return_code}</span>
            </div>
        `;
    }

    html += '</div>';
    
    // check service type and use appropriate formatter
    let executionData = execution.execution_data;

    // handle nested json in execution_data.stdout
    if (executionData && executionData.stdout && typeof executionData.stdout === 'string') {
        const trimmedStdout = executionData.stdout.trim();
        if (trimmedStdout.startsWith('{') || trimmedStdout.startsWith('[')) {
            try {
                const parsedStdout = JSON.parse(executionData.stdout);
                executionData = parsedStdout;
            } catch (e) {
                // keep original if parse fails
            }
        }
    }

    // determine if we should use a specialized formatter
    let useSpecializedFormatter = false;

    if (executionData && typeof executionData === 'object') {
        // check if execution_data contains stdout/stderr
        if (executionData.stdout !== undefined || executionData.stderr !== undefined) {
            useSpecializedFormatter = true;

            // auto-detect opentofu if not already set
            if (!execution.service_type && executionData.state_file !== undefined) {
                execution.service_type = 'opentofu-plan';
            }
        }
    }

    // use the appropriate formatter based on service type
    if (useSpecializedFormatter) {
        if (execution.service_type === 'opentofu-plan' || execution.service_type === 'opentofu-apply') {
            html += formatOpenTofuOutput(executionData);
        } else if (execution.service_type === 'python-script') {
            html += formatPythonOutput(executionData);
        } else if (execution.service_type === 'ansible-playbook') {
            html += formatAnsibleOutput(executionData);
        } else {
            // generic formatter for execution data with stdout/stderr
            html += formatOpenTofuOutput(executionData);
        }
    } else {
        // fall back to displaying raw stdout/stderr from the execution object
        if (execution.stdout) {
            html += `
                <h3 class="text-info mt-20 mb-10">Standard Output</h3>
                <div class="execution-output">${escapeHtml(execution.stdout)}</div>
            `;
        }

        if (execution.stderr) {
            html += `
                <h3 class="text-error mt-20 mb-10">Standard Error</h3>
                <div class="execution-output">${escapeHtml(execution.stderr)}</div>
            `;
        }

        // only show raw execution_data if it doesn't contain stdout/stderr
        if (executionData && Object.keys(executionData).length > 0 &&
            executionData.stdout === undefined && executionData.stderr === undefined) {
            html += `
                <h3 class="text-info mt-20 mb-10">Execution Data</h3>
                <div class="execution-output">${escapeHtml(JSON.stringify(executionData, null, 2))}</div>
            `;
        }
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

// opentofu output formatting functions
function formatOpenTofuOutput(executionData) {
    // parse the data if it's a string
    const data = typeof executionData === 'string' ? JSON.parse(executionData) : executionData;

    return `
        <div class="opentofu-output mt-20">
            <h3 class="text-info mb-10">Execution Output</h3>
            <div class="opentofu-console">
                ${formatConsoleOutput(data)}
            </div>
        </div>`;
}

// format console output with ansi to html conversion
function formatConsoleOutput(data) {
    // handle data that might be a json string
    let parsedData = data;
    if (typeof data === 'string') {
        try {
            parsedData = JSON.parse(data);
        } catch (e) {
            // if it's not json, treat it as stdout directly
            parsedData = { stdout: data };
        }
    }

    if (!parsedData.stdout && !parsedData.stderr) {
        return '<div class="no-output">No console output available</div>';
    }

    let html = '';

    // add timing information if available
    if (parsedData.start_time || parsedData.end_time || parsedData.elapsed_time) {
        html += formatTimingInfo(parsedData);
    }

    if (parsedData.stdout) {
        // ensure we have actual string data
        let stdoutText = parsedData.stdout;
        if (typeof stdoutText !== 'string') {
            stdoutText = String(stdoutText);
        }

        const formattedStdout = convertAnsiToHtml(stdoutText);
        html += `
            <div class="console-section">
                <h4 class="console-header">Standard Output</h4>
                <pre class="tofu-console-output">${formattedStdout}</pre>
            </div>
        `;
    }

    if (parsedData.stderr) {
        let stderrText = parsedData.stderr;
        if (typeof stderrText !== 'string') {
            stderrText = String(stderrText);
        }

        const formattedStderr = convertAnsiToHtml(stderrText);
        html += `
            <div class="console-section">
                <h4 class="console-header console-header-error">Standard Error</h4>
                <pre class="tofu-console-output tofu-console-error">${formattedStderr}</pre>
            </div>
        `;
    }

    // add state file information if available
    if (parsedData.state_file) {
        html += formatStateFile(parsedData.state_file);
    }

    return html;
}

// convert ansi escape codes to html with gruvbox theme colors
function convertAnsiToHtml(text) {
    if (!text) return '';

    // gruvbox dark theme colors
    const gruvbox = {
        black: '#282828',
        red: '#cc241d',
        green: '#98971a',
        yellow: '#d79921',
        blue: '#458588',
        magenta: '#b16286',
        cyan: '#689d6a',
        white: '#a89984',
        brightBlack: '#928374',
        brightRed: '#fb4934',
        brightGreen: '#b8bb26',
        brightYellow: '#fabd2f',
        brightBlue: '#83a598',
        brightMagenta: '#d3869b',
        brightCyan: '#8ec07c',
        brightWhite: '#ebdbb2'
    };

    // first escape html to prevent xss
    let result = escapeHtml(text);

    // replace ansi color codes with html spans
    // handle 8-color and 16-color ansi codes
    result = result
        // reset
        .replace(/\x1b\[0m/g, '</span>')
        .replace(/\x1b\[m/g, '</span>')
        
        // bold/bright
        .replace(/\x1b\[1m/g, '<span style="font-weight: bold;">')
        .replace(/\x1b\[22m/g, '</span>')
        
        // dim
        .replace(/\x1b\[2m/g, '<span style="opacity: 0.7;">')
        
        // italic
        .replace(/\x1b\[3m/g, '<span style="font-style: italic;">')
        .replace(/\x1b\[23m/g, '</span>')
        
        // underline
        .replace(/\x1b\[4m/g, '<span style="text-decoration: underline;">')
        .replace(/\x1b\[24m/g, '</span>')
        
        // foreground colors (30-37, 90-97)
        .replace(/\x1b\[30m/g, `<span style="color: ${gruvbox.black};">`)
        .replace(/\x1b\[31m/g, `<span style="color: ${gruvbox.red};">`)
        .replace(/\x1b\[32m/g, `<span style="color: ${gruvbox.green};">`)
        .replace(/\x1b\[33m/g, `<span style="color: ${gruvbox.yellow};">`)
        .replace(/\x1b\[34m/g, `<span style="color: ${gruvbox.blue};">`)
        .replace(/\x1b\[35m/g, `<span style="color: ${gruvbox.magenta};">`)
        .replace(/\x1b\[36m/g, `<span style="color: ${gruvbox.cyan};">`)
        .replace(/\x1b\[37m/g, `<span style="color: ${gruvbox.white};">`)
        
        // bright foreground colors
        .replace(/\x1b\[90m/g, `<span style="color: ${gruvbox.brightBlack};">`)
        .replace(/\x1b\[91m/g, `<span style="color: ${gruvbox.brightRed};">`)
        .replace(/\x1b\[92m/g, `<span style="color: ${gruvbox.brightGreen};">`)
        .replace(/\x1b\[93m/g, `<span style="color: ${gruvbox.brightYellow};">`)
        .replace(/\x1b\[94m/g, `<span style="color: ${gruvbox.brightBlue};">`)
        .replace(/\x1b\[95m/g, `<span style="color: ${gruvbox.brightMagenta};">`)
        .replace(/\x1b\[96m/g, `<span style="color: ${gruvbox.brightCyan};">`)
        .replace(/\x1b\[97m/g, `<span style="color: ${gruvbox.brightWhite};">`)
        
        // background colors (40-47, 100-107)
        .replace(/\x1b\[40m/g, `<span style="background-color: ${gruvbox.black};">`)
        .replace(/\x1b\[41m/g, `<span style="background-color: ${gruvbox.red};">`)
        .replace(/\x1b\[42m/g, `<span style="background-color: ${gruvbox.green};">`)
        .replace(/\x1b\[43m/g, `<span style="background-color: ${gruvbox.yellow};">`)
        .replace(/\x1b\[44m/g, `<span style="background-color: ${gruvbox.blue};">`)
        .replace(/\x1b\[45m/g, `<span style="background-color: ${gruvbox.magenta};">`)
        .replace(/\x1b\[46m/g, `<span style="background-color: ${gruvbox.cyan};">`)
        .replace(/\x1b\[47m/g, `<span style="background-color: ${gruvbox.white};">`)
        
        // handle combined codes like \x1b[1;32m (bold green)
        .replace(/\x1b\[1;30m/g, `<span style="font-weight: bold; color: ${gruvbox.black};">`)
        .replace(/\x1b\[1;31m/g, `<span style="font-weight: bold; color: ${gruvbox.red};">`)
        .replace(/\x1b\[1;32m/g, `<span style="font-weight: bold; color: ${gruvbox.green};">`)
        .replace(/\x1b\[1;33m/g, `<span style="font-weight: bold; color: ${gruvbox.yellow};">`)
        .replace(/\x1b\[1;34m/g, `<span style="font-weight: bold; color: ${gruvbox.blue};">`)
        .replace(/\x1b\[1;35m/g, `<span style="font-weight: bold; color: ${gruvbox.magenta};">`)
        .replace(/\x1b\[1;36m/g, `<span style="font-weight: bold; color: ${gruvbox.cyan};">`)
        .replace(/\x1b\[1;37m/g, `<span style="font-weight: bold; color: ${gruvbox.white};">`)
        
        // handle any remaining escape sequences
        .replace(/\x1b\[[0-9;]*m/g, '');
    
    // clean up any unclosed spans at the end
    const openSpans = (result.match(/<span[^>]*>/g) || []).length;
    const closeSpans = (result.match(/<\/span>/g) || []).length;
    if (openSpans > closeSpans) {
        result += '</span>'.repeat(openSpans - closeSpans);
    }
    
    return result;
}

// format state file information
function formatStateFile(stateFile) {
    if (!stateFile) {
        return '<div class="no-output">No state information available</div>';
    }
    
    const resources = stateFile.resources || [];
    const outputs = stateFile.outputs || {};
    
    return `
        <div class="state-container">
            <div class="state-summary">
                <h4 class="state-header">State Summary</h4>
                <div class="state-metadata">
                    <div class="metadata-item">
                        <span class="metadata-label">Resources:</span>
                        <span class="metadata-value">${resources.length}</span>
                    </div>
                    <div class="metadata-item">
                        <span class="metadata-label">Outputs:</span>
                        <span class="metadata-value">${Object.keys(outputs).length}</span>
                    </div>
                    <div class="metadata-item">
                        <span class="metadata-label">Terraform Version:</span>
                        <span class="metadata-value">${stateFile.terraform_version || 'N/A'}</span>
                    </div>
                    <div class="metadata-item">
                        <span class="metadata-label">Serial:</span>
                        <span class="metadata-value">${stateFile.serial || 'N/A'}</span>
                    </div>
                </div>
            </div>
            
            ${resources.length > 0 ? formatResources(resources) : ''}
        </div>
    `;
}

// format resource list from state file
function formatResources(resources) {
    if (!resources || resources.length === 0) {
        return '';
    }
    
    return `
        <div class="resources-section">
            <h4 class="state-header">Resources (${resources.length})</h4>
            <div class="resource-grid">
                ${resources.map(resource => `
                    <div class="resource-card">
                        <div class="resource-header">
                            <span class="resource-type">${resource.type || 'unknown'}</span>
                            <span class="resource-mode">${resource.mode || ''}</span>
                        </div>
                        <div class="resource-name">${resource.name || 'unnamed'}</div>
                        <div class="resource-details">
                            <span class="resource-provider">${extractProviderName(resource.provider)}</span>
                            <span class="resource-instances">Instances: ${resource.instances ? resource.instances.length : 0}</span>
                        </div>
                    </div>
                `).join('')}
            </div>
        </div>
    `;
}

// extract provider name from full provider string
function extractProviderName(provider) {
    if (!provider) return 'unknown';
    // extract from format like: provider["registry.opentofu.org/hashicorp/null"]
    const match = provider.match(/provider\["[^/]*\/([^/]*)\/([^"]*)/);
    if (match) {
        return `${match[1]}/${match[2]}`;
    }
    return provider;
}

// format tofu outputs
function formatTofuOutputs(outputs) {
    if (!outputs || Object.keys(outputs).length === 0) {
        return '<div class="no-output">No outputs defined</div>';
    }
    
    return `
        <div class="outputs-container">
            <h4 class="outputs-header">Terraform Outputs</h4>
            <div class="outputs-grid">
                ${Object.entries(outputs).map(([key, value]) => `
                    <div class="output-item">
                        <div class="output-key">${key}</div>
                        <div class="output-value-container">
                            <span class="output-value">${formatOutputValue(value.value)}</span>
                            <span class="output-type">${value.type || 'unknown'}</span>
                        </div>
                    </div>
                `).join('')}
            </div>
        </div>
    `;
}

// format output value based on type
function formatOutputValue(value) {
    if (value === null || value === undefined) {
        return 'null';
    }
    if (typeof value === 'object') {
        return JSON.stringify(value, null, 2);
    }
    return String(value);
}

// format timing information
function formatTimingInfo(data) {
    if (!data.start_time && !data.end_time && !data.elapsed_time) {
        return '';
    }

    const startTime = data.start_time ? new Date(data.start_time) : null;
    const endTime = data.end_time ? new Date(data.end_time) : null;

    // format the elapsed time properly
    let elapsedTimeStr = '';
    if (data.elapsed_time !== null && data.elapsed_time !== undefined) {
        if (typeof data.elapsed_time === 'number') {
            elapsedTimeStr = `${data.elapsed_time.toFixed(3)}s`;
        } else {
            elapsedTimeStr = String(data.elapsed_time);
        }
    }

    return `
        <div class="timing-container">
            <h4 class="timing-header">Execution Details</h4>
            <div class="timing-grid">
                ${startTime ? `
                    <div class="timing-item">
                        <span class="timing-label">Start Time:</span>
                        <span class="timing-value">${startTime.toISOString()}</span>
                    </div>
                ` : ''}
                ${endTime ? `
                    <div class="timing-item">
                        <span class="timing-label">End Time:</span>
                        <span class="timing-value">${endTime.toISOString()}</span>
                    </div>
                ` : ''}
                ${elapsedTimeStr ? `
                    <div class="timing-item">
                        <span class="timing-label">Elapsed Time:</span>
                        <span class="timing-value">${elapsedTimeStr}</span>
                    </div>
                ` : ''}
                ${data.return_code !== undefined && data.return_code !== null ? `
                    <div class="timing-item">
                        <span class="timing-label">Return Code:</span>
                        <span class="timing-value ${data.return_code === 0 ? 'timing-success' : 'timing-error'}">${data.return_code}</span>
                    </div>
                ` : ''}
            </div>
        </div>
    `;
}

// switch between opentofu output tabs
function switchOpenTofuTab(tabId, button) {
    // find the parent container
    const container = button.closest('.opentofu-tabs');
    
    // hide all tab contents in this container
    const contents = container.querySelectorAll('.opentofu-tab-content');
    contents.forEach(content => {
        content.classList.remove('active');
    });
    
    // remove active class from all buttons in this container
    const buttons = container.querySelectorAll('.tab-button');
    buttons.forEach(btn => {
        btn.classList.remove('active');
    });
    
    // show selected tab
    const targetTab = document.getElementById(tabId);
    if (targetTab) {
        targetTab.classList.add('active');
    }
    
    // mark button as active
    button.classList.add('active');
}

// python script output formatting functions
function formatPythonOutput(executionData) {
    const data = typeof executionData === 'string' ? JSON.parse(executionData) : executionData;
    
    return `
        <div class="python-output mt-20">
            <h3 class="text-info mb-10">Console Output</h3>
            <div class="python-console">
                ${formatPythonConsoleOutput(data)}
            </div>
        </div>`;
}

// format python console output with log level detection
function formatPythonConsoleOutput(data) {
    if (!data.stdout && !data.stderr) {
        return '<div class="no-output">No console output available</div>';
    }
    
    let html = '';
    
    if (data.stdout) {
        const formattedStdout = formatPythonLogOutput(data.stdout);
        html += `
            <div class="console-section">
                <h4 class="console-header">Standard Output</h4>
                <pre class="python-console-output">${formattedStdout}</pre>
            </div>
        `;
    }
    
    if (data.stderr) {
        const formattedStderr = formatPythonLogOutput(data.stderr);
        html += `
            <div class="console-section">
                <h4 class="console-header console-header-error">Standard Error</h4>
                <pre class="python-console-output python-console-error">${formattedStderr}</pre>
            </div>
        `;
    }
    
    return html;
}

// format python output with log level detection and syntax highlighting
function formatPythonLogOutput(text) {
    if (!text) return '';
    
    let result = escapeHtml(text);
    
    // python log level patterns with colors
    result = result
        .replace(/\b(CRITICAL|FATAL)(\s*[:\-]|\b)/gi, '<span class="python-critical">$1$2</span>')
        .replace(/\b(ERROR)(\s*[:\-]|\b)/gi, '<span class="python-error">$1$2</span>')
        .replace(/\b(WARNING|WARN)(\s*[:\-]|\b)/gi, '<span class="python-warning">$1$2</span>')
        .replace(/\b(INFO)(\s*[:\-]|\b)/gi, '<span class="python-info">$1$2</span>')
        .replace(/\b(DEBUG)(\s*[:\-]|\b)/gi, '<span class="python-debug">$1$2</span>')
        
        // highlight json objects
        .replace(/(\{[^{}]*\})/g, '<span class="python-json">$1</span>')
        
        // highlight file paths and line numbers
        .replace(/(\w+\.py):(\d+)/g, '<span class="python-file">$1</span>:<span class="python-line">$2</span>')
        
        // highlight execution times
        .replace(/(\d+\.?\d*)\s*(s|ms|seconds?|milliseconds?)\b/gi, '<span class="python-timing">$1$2</span>')
        
        // highlight success indicators
        .replace(/\b(SUCCESS|PASSED|OK|COMPLETE)\b/gi, '<span class="python-success">$1</span>')
        
        // highlight failure indicators
        .replace(/\b(FAILED?|FAILURE|ERROR|EXCEPTION|TRACEBACK)\b/gi, '<span class="python-error">$1</span>');
    
    return result;
}

// format python stack trace with file links
function formatPythonStackTrace(data) {
    const text = data.stderr || data.stdout || '';
    
    if (!text.includes('Traceback') && !text.includes('Exception')) {
        return '<div class="no-output">No stack trace information available</div>';
    }
    
    // extract traceback sections
    const tracebackPattern = /Traceback \(most recent call last\):[\s\S]*?(?=\n\n|\n[A-Z]|\n$|$)/g;
    const tracebacks = text.match(tracebackPattern) || [];
    
    if (tracebacks.length === 0) {
        return '<div class="no-output">No stack trace information available</div>';
    }
    
    return `
        <div class="stacktrace-container">
            <h4 class="stacktrace-header">Stack Traces (${tracebacks.length})</h4>
            ${tracebacks.map((trace, index) => `
                <div class="stacktrace-item">
                    <div class="stacktrace-title">Traceback ${index + 1}</div>
                    <pre class="stacktrace-content">${formatStackTraceText(trace)}</pre>
                </div>
            `).join('')}
        </div>
    `;
}

// format individual stack trace with enhanced readability
function formatStackTraceText(text) {
    let result = escapeHtml(text);
    
    result = result
        // highlight file paths and line numbers
        .replace(/(File\s+)"([^"]+)",\s+line\s+(\d+)/g, 
                 '$1"<span class="stacktrace-file">$2</span>", line <span class="stacktrace-line">$3</span>')
        
        // highlight function names
        .replace(/in\s+([a-zA-Z_][a-zA-Z0-9_]*)/g, 'in <span class="stacktrace-function">$1</span>')
        
        // highlight exception types
        .replace(/^([A-Z][a-zA-Z]*Error|[A-Z][a-zA-Z]*Exception):/gm, 
                 '<span class="stacktrace-exception">$1</span>:')
        
        // highlight traceback header
        .replace(/(Traceback \(most recent call last\):)/, '<span class="stacktrace-header-text">$1</span>');
    
    return result;
}

// format python performance metrics
function formatPythonPerformance(data) {
    const text = (data.stdout || '') + (data.stderr || '');
    
    // extract timing information
    const timingPatterns = [
        /executed in (\d+\.?\d*)\s*(s|ms|seconds?|milliseconds?)/gi,
        /took (\d+\.?\d*)\s*(s|ms|seconds?|milliseconds?)/gi,
        /duration[:\s]+(\d+\.?\d*)\s*(s|ms|seconds?|milliseconds?)/gi,
        /time[:\s]+(\d+\.?\d*)\s*(s|ms|seconds?|milliseconds?)/gi
    ];
    
    let timings = [];
    timingPatterns.forEach(pattern => {
        let match;
        while ((match = pattern.exec(text)) !== null) {
            timings.push({
                value: parseFloat(match[1]),
                unit: match[2],
                context: text.substring(Math.max(0, match.index - 50), match.index + 100)
            });
        }
    });
    
    if (timings.length === 0 && !data.elapsed_time) {
        return '<div class="no-output">No performance information available</div>';
    }
    
    return `
        <div class="performance-container">
            <h4 class="performance-header">Performance Metrics</h4>
            <div class="performance-grid">
                ${data.elapsed_time ? `
                    <div class="performance-item">
                        <span class="performance-label">Total Execution Time:</span>
                        <span class="performance-value">${data.elapsed_time.toFixed(3)}s</span>
                    </div>
                ` : ''}
                ${data.return_code !== undefined ? `
                    <div class="performance-item">
                        <span class="performance-label">Exit Code:</span>
                        <span class="performance-value ${data.return_code === 0 ? 'performance-success' : 'performance-error'}">${data.return_code}</span>
                    </div>
                ` : ''}
                ${timings.map((timing, index) => `
                    <div class="performance-item">
                        <span class="performance-label">Timing ${index + 1}:</span>
                        <span class="performance-value">${timing.value}${timing.unit}</span>
                    </div>
                `).join('')}
            </div>
            ${timings.length > 0 ? `
                <div class="performance-details">
                    <h5 class="performance-subheader">Timing Context</h5>
                    ${timings.map((timing, index) => `
                        <div class="timing-context">
                            <strong>Timing ${index + 1}:</strong>
                            <pre>${escapeHtml(timing.context)}</pre>
                        </div>
                    `).join('')}
                </div>
            ` : ''}
        </div>
    `;
}

// format python environment information
function formatPythonEnvironment(data) {
    const text = (data.stdout || '') + (data.stderr || '');
    
    // extract import statements and module information
    const imports = extractPythonImports(text);
    const modules = extractPythonModules(text);
    
    return `
        <div class="environment-container">
            <h4 class="environment-header">Environment Information</h4>
            
            ${data.start_time ? `
                <div class="env-section">
                    <h5 class="env-subheader">Execution Context</h5>
                    <div class="env-grid">
                        <div class="env-item">
                            <span class="env-label">Started:</span>
                            <span class="env-value">${new Date(data.start_time).toLocaleString()}</span>
                        </div>
                        ${data.end_time ? `
                            <div class="env-item">
                                <span class="env-label">Completed:</span>
                                <span class="env-value">${new Date(data.end_time).toLocaleString()}</span>
                            </div>
                        ` : ''}
                    </div>
                </div>
            ` : ''}
            
            ${imports.length > 0 ? `
                <div class="env-section">
                    <h5 class="env-subheader">Detected Imports (${imports.length})</h5>
                    <div class="import-grid">
                        ${imports.map(imp => `
                            <span class="import-item">${imp}</span>
                        `).join('')}
                    </div>
                </div>
            ` : ''}
            
            ${modules.length > 0 ? `
                <div class="env-section">
                    <h5 class="env-subheader">Module Information</h5>
                    <div class="module-list">
                        ${modules.map(module => `
                            <div class="module-item">
                                <span class="module-name">${module.name}</span>
                                ${module.version ? `<span class="module-version">${module.version}</span>` : ''}
                            </div>
                        `).join('')}
                    </div>
                </div>
            ` : ''}
        </div>
    `;
}

// extract python imports from output
function extractPythonImports(text) {
    const importPatterns = [
        /^import\s+([a-zA-Z_][a-zA-Z0-9_.]*)/gm,
        /^from\s+([a-zA-Z_][a-zA-Z0-9_.]*)\s+import/gm
    ];
    
    let imports = new Set();
    
    importPatterns.forEach(pattern => {
        let match;
        while ((match = pattern.exec(text)) !== null) {
            imports.add(match[1]);
        }
    });
    
    return Array.from(imports).slice(0, 20); // limit to 20 imports
}

// extract python module versions from output
function extractPythonModules(text) {
    const modulePattern = /([a-zA-Z_][a-zA-Z0-9_-]+)[:\s]+(\d+\.\d+(?:\.\d+)?)/g;
    let modules = [];
    let match;
    
    while ((match = modulePattern.exec(text)) !== null) {
        modules.push({
            name: match[1],
            version: match[2]
        });
    }
    
    return modules.slice(0, 10); // limit to 10 modules
}

// switch between python output tabs
function switchPythonTab(tabId, button) {
    const container = button.closest('.python-tabs');
    
    const contents = container.querySelectorAll('.python-tab-content');
    contents.forEach(content => {
        content.classList.remove('active');
    });
    
    const buttons = container.querySelectorAll('.tab-button');
    buttons.forEach(btn => {
        btn.classList.remove('active');
    });
    
    const targetTab = document.getElementById(tabId);
    if (targetTab) {
        targetTab.classList.add('active');
    }
    
    button.classList.add('active');
}

// ansible playbook output formatting functions
function formatAnsibleOutput(executionData) {
    const data = typeof executionData === 'string' ? JSON.parse(executionData) : executionData;
    
    return `
        <div class="ansible-output mt-20">
            <h3 class="text-info mb-10">Console Output</h3>
            <div class="ansible-console">
                ${formatAnsibleConsoleOutput(data)}
            </div>
        </div>`;
}

// format ansible console output
function formatAnsibleConsoleOutput(data) {
    if (!data.stdout && !data.stderr) {
        return '<div class="no-output">No console output available</div>';
    }
    
    let html = '';
    
    if (data.stdout) {
        html += `
            <div class="console-section">
                <h4 class="console-header">Standard Output</h4>
                <pre class="ansible-console-output">${escapeHtml(data.stdout)}</pre>
            </div>
        `;
    }
    
    if (data.stderr) {
        html += `
            <div class="console-section">
                <h4 class="console-header console-header-error">Standard Error</h4>
                <pre class="ansible-console-output ansible-console-error">${escapeHtml(data.stderr)}</pre>
            </div>
        `;
    }
    
    return html;
}

// format ansible play summary
function formatAnsibleSummary(data) {
    const text = (data.stdout || '') + (data.stderr || '');
    
    // extract play and task summary information
    const playResults = extractAnsiblePlayResults(text);
    const hostSummary = extractAnsibleHostSummary(text);
    
    return `
        <div class="ansible-summary-container">
            <h4 class="ansible-summary-header">Playbook Summary</h4>
            
            <div class="ansible-overview">
                <div class="summary-grid">
                    <div class="summary-item">
                        <span class="summary-label">Total Plays:</span>
                        <span class="summary-value">${playResults.length}</span>
                    </div>
                    <div class="summary-item">
                        <span class="summary-label">Hosts:</span>
                        <span class="summary-value">${Object.keys(hostSummary).length}</span>
                    </div>
                    <div class="summary-item">
                        <span class="summary-label">Duration:</span>
                        <span class="summary-value">${data.elapsed_time ? data.elapsed_time.toFixed(2) + 's' : 'N/A'}</span>
                    </div>
                    <div class="summary-item">
                        <span class="summary-label">Result:</span>
                        <span class="summary-value ${data.return_code === 0 ? 'ansible-success' : 'ansible-failed'}">${data.return_code === 0 ? 'SUCCESS' : 'FAILED'}</span>
                    </div>
                </div>
            </div>
            
            ${Object.keys(hostSummary).length > 0 ? `
                <div class="host-summary-section">
                    <h5 class="ansible-section-header">Host Summary</h5>
                    <div class="host-summary-grid">
                        ${Object.entries(hostSummary).map(([host, stats]) => `
                            <div class="host-summary-card">
                                <div class="host-name">${host}</div>
                                <div class="host-stats">
                                    <span class="stat-item ansible-ok">${stats.ok || 0} ok</span>
                                    <span class="stat-item ansible-changed">${stats.changed || 0} changed</span>
                                    <span class="stat-item ansible-failed">${stats.failed || 0} failed</span>
                                    <span class="stat-item ansible-skipped">${stats.skipped || 0} skipped</span>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            ` : ''}
            
            ${playResults.length > 0 ? `
                <div class="plays-section">
                    <h5 class="ansible-section-header">Play Results</h5>
                    <div class="plays-list">
                        ${playResults.map((play, index) => `
                            <div class="play-item">
                                <div class="play-header">
                                    <span class="play-name">${play.name || `Play ${index + 1}`}</span>
                                    <span class="play-status ${play.status}">${play.status.toUpperCase()}</span>
                                </div>
                                <div class="play-details">
                                    <span>Tasks: ${play.tasks || 0}</span>
                                    <span>Hosts: ${play.hosts || 0}</span>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            ` : ''}
        </div>
    `;
}

// format ansible task details
function formatAnsibleTasks(data) {
    const text = (data.stdout || '') + (data.stderr || '');
    const tasks = extractAnsibleTasks(text);
    
    if (tasks.length === 0) {
        return '<div class="no-output">No task information available</div>';
    }
    
    return `
        <div class="ansible-tasks-container">
            <h4 class="ansible-tasks-header">Task Details (${tasks.length})</h4>
            
            <div class="tasks-timeline">
                ${tasks.map((task, index) => `
                    <div class="task-item">
                        <div class="task-indicator ${task.status}"></div>
                        <div class="task-content">
                            <div class="task-header">
                                <span class="task-name">${task.name || `Task ${index + 1}`}</span>
                                <span class="task-status ${task.status}">${task.status.toUpperCase()}</span>
                            </div>
                            <div class="task-details">
                                <div class="task-module">${task.module || 'unknown'}</div>
                                ${task.duration ? `<div class="task-duration">${task.duration}</div>` : ''}
                            </div>
                            ${task.hosts && task.hosts.length > 0 ? `
                                <div class="task-hosts">
                                    <span class="hosts-label">Affected hosts:</span>
                                    ${task.hosts.map(host => `<span class="host-tag">${host}</span>`).join('')}
                                </div>
                            ` : ''}
                            ${task.changes && task.changes.length > 0 ? `
                                <div class="task-changes">
                                    <div class="changes-header">Changes:</div>
                                    <pre class="changes-content">${escapeHtml(task.changes.join('\n'))}</pre>
                                </div>
                            ` : ''}
                        </div>
                    </div>
                `).join('')}
            </div>
        </div>
    `;
}

// format ansible host results
function formatAnsibleHosts(data) {
    const text = (data.stdout || '') + (data.stderr || '');
    const hostResults = extractAnsibleHostResults(text);
    
    if (Object.keys(hostResults).length === 0) {
        return '<div class="no-output">No host results available</div>';
    }
    
    return `
        <div class="ansible-hosts-container">
            <h4 class="ansible-hosts-header">Host Results</h4>
            
            <div class="hosts-grid">
                ${Object.entries(hostResults).map(([host, result]) => `
                    <div class="host-result-card">
                        <div class="host-result-header">
                            <span class="host-result-name">${host}</span>
                            <span class="host-result-status ${result.overall_status}">${result.overall_status.toUpperCase()}</span>
                        </div>
                        
                        <div class="host-result-stats">
                            <div class="result-stat">
                                <span class="stat-label">OK:</span>
                                <span class="stat-value ansible-ok">${result.ok || 0}</span>
                            </div>
                            <div class="result-stat">
                                <span class="stat-label">Changed:</span>
                                <span class="stat-value ansible-changed">${result.changed || 0}</span>
                            </div>
                            <div class="result-stat">
                                <span class="stat-label">Failed:</span>
                                <span class="stat-value ansible-failed">${result.failed || 0}</span>
                            </div>
                            <div class="result-stat">
                                <span class="stat-label">Skipped:</span>
                                <span class="stat-value ansible-skipped">${result.skipped || 0}</span>
                            </div>
                            <div class="result-stat">
                                <span class="stat-label">Unreachable:</span>
                                <span class="stat-value ansible-unreachable">${result.unreachable || 0}</span>
                            </div>
                        </div>
                        
                        ${result.tasks && result.tasks.length > 0 ? `
                            <div class="host-tasks">
                                <div class="host-tasks-header">Tasks:</div>
                                <div class="host-tasks-list">
                                    ${result.tasks.slice(0, 5).map(task => `
                                        <div class="host-task-item ${task.status}">
                                            <span class="task-indicator"></span>
                                            <span class="task-text">${task.name}</span>
                                        </div>
                                    `).join('')}
                                    ${result.tasks.length > 5 ? `<div class="more-tasks">+${result.tasks.length - 5} more tasks</div>` : ''}
                                </div>
                            </div>
                        ` : ''}
                    </div>
                `).join('')}
            </div>
        </div>
    `;
}

// format ansible variables
function formatAnsibleVariables(data) {
    const text = (data.stdout || '') + (data.stderr || '');
    const variables = extractAnsibleVariables(text);
    
    if (Object.keys(variables).length === 0) {
        return '<div class="no-output">No variable information available</div>';
    }
    
    return `
        <div class="ansible-variables-container">
            <h4 class="ansible-variables-header">Variables & Facts</h4>
            
            <div class="variables-sections">
                ${Object.entries(variables).map(([category, vars]) => `
                    <div class="variable-section">
                        <h5 class="variable-category">${category}</h5>
                        <div class="variables-list">
                            ${Object.entries(vars).slice(0, 10).map(([key, value]) => `
                                <div class="variable-item">
                                    <div class="variable-key">${key}</div>
                                    <div class="variable-value">
                                        ${typeof value === 'object' ? 
                                          `<pre>${escapeHtml(JSON.stringify(value, null, 2))}</pre>` : 
                                          escapeHtml(String(value))
                                        }
                                    </div>
                                </div>
                            `).join('')}
                            ${Object.keys(vars).length > 10 ? `<div class="more-vars">+${Object.keys(vars).length - 10} more variables</div>` : ''}
                        </div>
                    </div>
                `).join('')}
            </div>
        </div>
    `;
}

// format ansible console output
function formatAnsibleConsole(data) {
    if (!data.stdout && !data.stderr) {
        return '<div class="no-output">No console output available</div>';
    }
    
    let html = '';
    
    if (data.stdout) {
        const formattedStdout = formatAnsibleLogOutput(data.stdout);
        html += `
            <div class="console-section">
                <h4 class="console-header">Standard Output</h4>
                <pre class="ansible-console-output">${formattedStdout}</pre>
            </div>
        `;
    }
    
    if (data.stderr) {
        const formattedStderr = formatAnsibleLogOutput(data.stderr);
        html += `
            <div class="console-section">
                <h4 class="console-header console-header-error">Standard Error</h4>
                <pre class="ansible-console-output ansible-console-error">${formattedStderr}</pre>
            </div>
        `;
    }
    
    return html;
}

// format ansible log output with color coding
function formatAnsibleLogOutput(text) {
    if (!text) return '';
    
    let result = escapeHtml(text);
    
    // ansible status patterns with colors
    result = result
        .replace(/\b(PLAY RECAP)\b/g, '<span class="ansible-recap">$1</span>')
        .replace(/\b(TASK|PLAY)\s*\[(.*?)\]/g, '<span class="ansible-task">$1</span> [<span class="ansible-task-name">$2</span>]')
        .replace(/\b(ok|OK)\b/g, '<span class="ansible-ok">$1</span>')
        .replace(/\b(changed|CHANGED)\b/g, '<span class="ansible-changed">$1</span>')
        .replace(/\b(failed|FAILED|fatal)\b/g, '<span class="ansible-failed">$1</span>')
        .replace(/\b(skipping|skipped|SKIPPED)\b/g, '<span class="ansible-skipped">$1</span>')
        .replace(/\b(unreachable|UNREACHABLE)\b/g, '<span class="ansible-unreachable">$1</span>')
        
        // highlight ansible host references
        .replace(/(\w+\.[\w.-]+|\d+\.\d+\.\d+\.\d+)\s*:/g, '<span class="ansible-host">$1</span>:')
        
        // highlight timing
        .replace(/(\d+\.?\d*)\s*(s|sec|seconds?)\b/gi, '<span class="ansible-timing">$1$2</span>')
        
        // highlight json/yaml content
        .replace(/(\{[^{}]*\})/g, '<span class="ansible-json">$1</span>')
        .replace(/(---|\.\.\.|^[\s]*[-\w]+:)/gm, '<span class="ansible-yaml">$1</span>');
    
    return result;
}

// extraction functions for ansible data
function extractAnsiblePlayResults(text) {
    const playPattern = /PLAY \[(.*?)\]/g;
    let plays = [];
    let match;
    
    while ((match = playPattern.exec(text)) !== null) {
        plays.push({
            name: match[1],
            status: text.includes('fatal:') ? 'failed' : 'ok',
            tasks: 0,
            hosts: 0
        });
    }
    
    return plays;
}

function extractAnsibleHostSummary(text) {
    const recapPattern = /PLAY RECAP[\s\S]*?(?=\n\n|$)/;
    const match = text.match(recapPattern);
    
    if (!match) return {};
    
    const recapText = match[0];
    const hostPattern = /(\S+)\s+:\s+ok=(\d+)\s+changed=(\d+)(?:\s+unreachable=(\d+))?\s+failed=(\d+)(?:\s+skipped=(\d+))?/g;
    let hosts = {};
    let hostMatch;
    
    while ((hostMatch = hostPattern.exec(recapText)) !== null) {
        hosts[hostMatch[1]] = {
            ok: parseInt(hostMatch[2]),
            changed: parseInt(hostMatch[3]),
            unreachable: parseInt(hostMatch[4] || 0),
            failed: parseInt(hostMatch[5]),
            skipped: parseInt(hostMatch[6] || 0)
        };
    }
    
    return hosts;
}

function extractAnsibleTasks(text) {
    const taskPattern = /TASK \[(.*?)\][\s\S]*?(?=TASK \[|PLAY \[|PLAY RECAP|$)/g;
    let tasks = [];
    let match;
    
    while ((match = taskPattern.exec(text)) !== null) {
        const taskText = match[0];
        const name = match[1];
        
        tasks.push({
            name: name,
            status: taskText.includes('failed:') ? 'failed' : 
                   taskText.includes('changed:') ? 'changed' : 
                   taskText.includes('skipping:') ? 'skipped' : 'ok',
            module: extractModuleName(taskText),
            hosts: extractTaskHosts(taskText),
            changes: extractTaskChanges(taskText)
        });
    }
    
    return tasks;
}

function extractAnsibleHostResults(text) {
    const hostSummary = extractAnsibleHostSummary(text);
    const tasks = extractAnsibleTasks(text);
    
    let hostResults = {};
    
    Object.entries(hostSummary).forEach(([host, stats]) => {
        hostResults[host] = {
            ...stats,
            overall_status: stats.failed > 0 ? 'failed' : 
                           stats.changed > 0 ? 'changed' : 'ok',
            tasks: tasks.filter(task => task.hosts.includes(host))
        };
    });
    
    return hostResults;
}

function extractAnsibleVariables(text) {
    // basic variable extraction - could be enhanced based on actual ansible output format
    return {
        'Facts': extractAnsibleFacts(text),
        'Variables': extractAnsibleVars(text)
    };
}

function extractModuleName(taskText) {
    const moduleMatch = taskText.match(/(\w+):\s*\{/);
    return moduleMatch ? moduleMatch[1] : 'unknown';
}

function extractTaskHosts(taskText) {
    const hostMatches = taskText.match(/(\w+[\w.-]*)\s*:/g);
    return hostMatches ? hostMatches.map(h => h.replace(':', '')) : [];
}

function extractTaskChanges(taskText) {
    const changePattern = /changed:\s*\[(.*?)\]/g;
    let changes = [];
    let match;
    
    while ((match = changePattern.exec(taskText)) !== null) {
        changes.push(match[1]);
    }
    
    return changes;
}

function extractAnsibleFacts(text) {
    // extract common ansible facts from output
    const facts = {};
    const factPatterns = {
        'ansible_os_family': /ansible_os_family['"]\s*:\s*['"]([^'"]+)['"]/,
        'ansible_distribution': /ansible_distribution['"]\s*:\s*['"]([^'"]+)['"]/,
        'ansible_python_version': /ansible_python_version['"]\s*:\s*['"]([^'"]+)['"]/
    };
    
    Object.entries(factPatterns).forEach(([key, pattern]) => {
        const match = text.match(pattern);
        if (match) facts[key] = match[1];
    });
    
    return facts;
}

function extractAnsibleVars(text) {
    // extract ansible variables from output
    const vars = {};
    const varPattern = /(\w+)\s*:\s*([^,}\n]+)/g;
    let match;
    
    while ((match = varPattern.exec(text)) !== null && Object.keys(vars).length < 10) {
        if (!match[1].startsWith('ansible_')) {
            vars[match[1]] = match[2].trim();
        }
    }
    
    return vars;
}

// switch between ansible output tabs
function switchAnsibleTab(tabId, button) {
    const container = button.closest('.ansible-tabs');
    
    const contents = container.querySelectorAll('.ansible-tab-content');
    contents.forEach(content => {
        content.classList.remove('active');
    });
    
    const buttons = container.querySelectorAll('.tab-button');
    buttons.forEach(btn => {
        btn.classList.remove('active');
    });
    
    const targetTab = document.getElementById(tabId);
    if (targetTab) {
        targetTab.classList.add('active');
    }
    
    button.classList.add('active');
}

// close modal when clicking outside
window.onclick = function(event) {
    const modal = document.getElementById('execution-modal');
    if (event.target === modal) {
        closeExecutionModal();
    }
};

// toggle execute dropdown for opentofu services
function toggleExecuteDropdown(button) {
    const dropdown = button.nextElementSibling;
    const isOpen = dropdown.classList.contains('show');
    
    // close all other dropdowns first
    document.querySelectorAll('.dropdown-menu.show').forEach(menu => {
        menu.classList.remove('show');
        menu.previousElementSibling.classList.remove('open');
    });
    
    // toggle this dropdown
    if (!isOpen) {
        dropdown.classList.add('show');
        button.classList.add('open');
    }
}

// close dropdowns when clicking outside
// removed dropdown click handler - no longer needed after removing opentofu dropdown

// removed executeOpenTofu function - opentofu now uses standard input form with operation selection

// execute service functionality
async function executeService(serviceName, button) {
    // update button state to executing
    const btnText = button.querySelector('.btn-text');
    const btnIcon = button.querySelector('.execute-icon');
    const btnSpinner = button.querySelector('.btn-spinner');

    if (btnText) btnText.style.display = 'none';
    if (btnIcon) btnIcon.style.display = 'none';
    btnSpinner.style.display = 'inline-flex';
    button.disabled = true;
    
    try {
        const response = await fetch(`/api/execute/${serviceName}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCsrfToken(),
                'Content-Type': 'application/json',
            },
        });
        
        const result = await response.json();
        
        if (result.status === 'queued' || result.status === 'started') {
            // show success feedback
            const message = result.status === 'queued' ? 
                `execution queued (position ${result.position || 1})` : 
                'execution started';
            showExecutionFeedback(button, 'success', message);
            
            // refresh dashboard and queue after short delay
            setTimeout(() => {
                refreshDashboard();
                refreshQueueStatus();
            }, 1000);
            
        } else {
            showExecutionFeedback(button, 'error', result.message);
        }
        
    } catch (error) {
        console.error('execution error:', error);
        showExecutionFeedback(button, 'error', 'network error');
    }
}

// show execution feedback on service card
function showExecutionFeedback(button, type, message) {
    const card = button.closest('.status-card');
    
    // add visual feedback class
    card.classList.add(`execution-${type}`);
    
    // reset button
    resetExecuteButton(button);
    
    // remove feedback after 2 seconds
    setTimeout(() => {
        card.classList.remove(`execution-${type}`);
    }, 2000);
    
    // show toast notification
    showToast(message, type);
}

// reset execute button to default state
function resetExecuteButton(button) {
    const btnText = button.querySelector('.btn-text');
    const btnIcon = button.querySelector('.execute-icon');
    const btnSpinner = button.querySelector('.btn-spinner');
    const btnArrow = button.querySelector('.dropdown-arrow');

    if (btnText) {
        btnText.style.display = 'inline';
    }
    if (btnIcon) {
        btnIcon.style.display = 'block';
    }
    btnSpinner.style.display = 'none';
    if (btnArrow) {
        btnArrow.style.display = 'inline';
    }
    button.disabled = false;
}

// show service history (placeholder for future implementation)
function showServiceHistory(serviceName) {
    showToast(`history for ${serviceName} (coming soon)`, 'info');
}

// show toast notification
function showToast(message, type = 'info') {
    // create toast element
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    
    // add to page
    document.body.appendChild(toast);
    
    // show toast
    setTimeout(() => {
        toast.classList.add('show');
    }, 100);
    
    // hide and remove toast
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => {
            document.body.removeChild(toast);
        }, 300);
    }, 3000);
}

// get csrf token for requests
function getCsrfToken() {
    // get from django's hidden csrf input
    const csrfInput = document.querySelector('input[name="csrfmiddlewaretoken"]');
    if (csrfInput) {
        return csrfInput.value;
    }
    
    // fallback to cookie method
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
        const [name, value] = cookie.trim().split('=');
        if (name === 'csrftoken') {
            return value;
        }
    }
    
    return '';
}

// execution queue management
let executionPanelCollapsed = false;
let queueRefreshInterval = null;

function toggleExecutionPanel() {
    const panel = document.getElementById('execution-panel');
    const content = document.getElementById('panel-content');
    const toggle = document.querySelector('.panel-toggle');
    
    executionPanelCollapsed = !executionPanelCollapsed;
    
    if (executionPanelCollapsed) {
        content.style.display = 'none';
        toggle.textContent = '▶';
        panel.classList.add('collapsed');
    } else {
        content.style.display = 'block';
        toggle.textContent = '▼';
        panel.classList.remove('collapsed');
    }
}

async function refreshQueueStatus() {
    try {
        const response = await fetch('/api/queue/status/');
        if (!response.ok) throw new Error('Failed to fetch queue status');
        
        const data = await response.json();
        updateQueueDisplay(data);
    } catch (error) {
        console.error('Error fetching queue status:', error);
    }
}

function updateQueueDisplay(data) {
    // update counts
    document.getElementById('active-count').textContent = data.running_count || 0;
    document.getElementById('queued-count').textContent = data.queued_count || 0;
    document.getElementById('completed-count').textContent = data.completed_count || 0;
    
    // update running list
    const runningList = document.getElementById('running-list');
    if (data.running && data.running.length > 0) {
        runningList.innerHTML = data.running.map(item => createExecutionItem(item, 'running')).join('');
    } else {
        runningList.innerHTML = '<div class="empty-message">No running executions</div>';
    }
    
    // update queued list
    const queuedList = document.getElementById('queued-list');
    if (data.queued && data.queued.length > 0) {
        queuedList.innerHTML = data.queued.map((item, index) => 
            createExecutionItem(item, 'queued', index + 1)
        ).join('');
    } else {
        queuedList.innerHTML = '<div class="empty-message">No queued executions</div>';
    }
    
    // update completed list
    const completedList = document.getElementById('completed-list');
    if (data.completed && data.completed.length > 0) {
        completedList.innerHTML = data.completed.map(item => createExecutionItem(item, 'completed')).join('');
    } else {
        completedList.innerHTML = '<div class="empty-message">No recent completions</div>';
    }
}

function createExecutionItem(item, type, position = null) {
    const progressBar = type === 'running' ? `
        <div class="progress-bar">
            <div class="progress-fill" style="width: ${item.progress_percent || 0}%"></div>
        </div>
    ` : '';
    
    const positionText = position ? `<span class="queue-position">Position: ${position}</span>` : '';
    
    const cancelButton = (type === 'queued') ? `
        <button class="btn-cancel" onclick="cancelExecution(${item.id})">Cancel</button>
    ` : '';
    
    const statusClass = {
        'running': 'status-running',
        'queued': 'status-queued',
        'completed': 'status-completed',
        'failed': 'status-failed',
        'cancelled': 'status-cancelled'
    }[item.status] || '';
    
    const timingInfo = type === 'running' && item.started_at ? 
        `Started ${formatTimeAgo(item.started_at)}` :
        type === 'completed' && item.completed_at ? 
        `Completed ${formatTimeAgo(item.completed_at)}` :
        type === 'queued' && item.created_at ?
        `Queued ${formatTimeAgo(item.created_at)}` : '';
    
    return `
        <div class="execution-item ${statusClass}">
            <div class="execution-header">
                <span class="service-name">${item.service_name}</span>
                <span class="service-type">${item.service_type}</span>
                ${cancelButton}
            </div>
            <div class="execution-details">
                ${positionText}
                <span class="timing-info">${timingInfo}</span>
                ${item.operation ? `<span class="operation">${item.operation}</span>` : ''}
            </div>
            ${progressBar}
        </div>
    `;
}

async function cancelExecution(queueId) {
    if (!confirm('Are you sure you want to cancel this execution?')) return;
    
    try {
        const response = await fetch(`/api/queue/${queueId}/cancel/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCsrfToken(),
                'Content-Type': 'application/json',
            },
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showToast('Execution cancelled', 'success');
            refreshQueueStatus();
        } else {
            showToast(result.message || 'Failed to cancel execution', 'error');
        }
    } catch (error) {
        console.error('Error cancelling execution:', error);
        showToast('Failed to cancel execution', 'error');
    }
}

function formatTimeAgo(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const seconds = Math.floor((now - date) / 1000);
    
    if (seconds < 60) return `${seconds}s ago`;
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes}m ago`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours}h ago`;
    const days = Math.floor(hours / 24);
    return `${days}d ago`;
}

// start queue refresh interval
function startQueueRefresh() {
    refreshQueueStatus();
    queueRefreshInterval = setInterval(refreshQueueStatus, 5000); // refresh every 5 seconds
}

function stopQueueRefresh() {
    if (queueRefreshInterval) {
        clearInterval(queueRefreshInterval);
        queueRefreshInterval = null;
    }
}

// initialize queue panel on page load
document.addEventListener('DOMContentLoaded', function() {
    startQueueRefresh();
});

// cleanup on page unload
window.addEventListener('beforeunload', function() {
    stopQueueRefresh();
});


// service input form functionality
class ServiceInputForm {
    constructor() {
        this.currentService = null;
        this.currentManifest = null;
    }

    async loadServiceInputs(serviceName) {
        try {
            const response = await fetch(`/api/services/${serviceName}/inputs/`);
            if (!response.ok) {
                if (response.status === 404) {
                    // no manifest found, use default form
                    return null;
                }
                throw new Error('Failed to load service inputs');
            }

            const data = await response.json();
            this.currentService = serviceName;
            this.currentManifest = data.manifest;
            return data;
        } catch (error) {
            console.error('Error loading service inputs:', error);
            return null;
        }
    }

    async loadAvailableInputFiles(serviceName) {
        try {
            const response = await fetch(`/api/services/${serviceName}/input-files/`);
            if (!response.ok) {
                console.warn('Could not load available input files');
                return [];
            }

            const data = await response.json();
            return data.files || [];
        } catch (error) {
            console.error('Error loading available input files:', error);
            return [];
        }
    }

    async generateForm(serviceName, serviceType, operation = null) {
        // load input manifest
        const inputData = await this.loadServiceInputs(serviceName);

        if (!inputData || !inputData.manifest) {
            return this.generateBasicForm(serviceName, serviceType, operation);
        }

        const manifest = inputData.manifest;
        const form = document.createElement('form');
        form.className = 'service-input-form';
        form.id = 'service-input-form';

        // load available input files
        const availableFiles = await this.loadAvailableInputFiles(serviceName);

        // add service info and file loader
        form.innerHTML = `
            <div class="form-header">
                <h3>Execute Service: ${serviceName}</h3>
                <p class="service-type">Type: ${serviceType}</p>
            </div>

            ${serviceType === 'opentofu-plan' ? `
                <div class="form-section opentofu-operation-section">
                    <div class="operation-selector">
                        <label class="operation-option ${!operation || operation === 'apply' ? 'selected' : ''}">
                            <input type="radio" name="operation" value="apply" ${!operation || operation === 'apply' ? 'checked' : ''}>
                            <span class="operation-text">
                                <strong>APPLY</strong>
                                <small>Provision Infrastructure</small>
                            </span>
                        </label>
                        <label class="operation-option ${operation === 'destroy' ? 'selected' : ''}">
                            <input type="radio" name="operation" value="destroy" ${operation === 'destroy' ? 'checked' : ''}>
                            <span class="operation-text">
                                <strong>DESTROY</strong>
                                <small>Deprovision Infrastructure</small>
                            </span>
                        </label>
                    </div>
                </div>
            ` : ''}

            <div class="input-file-loader">
                <div class="loader-header">
                    <h4>Load from Input File (Optional)</h4>
                    <button type="button" class="btn btn-sm btn-secondary" onclick="toggleInputFileLoader()">
                        ▼ Show/Hide
                    </button>
                </div>
                <div id="input-file-section" class="input-file-section" style="display: none;">
                    <div class="form-field">
                        <label for="input-file-path">Input File Path</label>
                        <input type="text" id="input-file-path" class="form-control"
                               placeholder="@inputs/vpc.yaml or /absolute/path/config.yaml">
                        <small class="help-text">Use @ prefix for paths relative to /home/admin/data</small>
                    </div>
                    ${availableFiles && availableFiles.length > 0 ? `
                        <div class="form-field">
                            <label>Or Select Available File:</label>
                            <select id="preset-selector" class="form-control" onchange="selectPresetFile(this.value)">
                                <option value="">-- Select an input file --</option>
                                ${availableFiles.map(file => `
                                    <option value="${file.path}">
                                        ${file.filename}
                                    </option>
                                `).join('')}
                            </select>
                        </div>
                    ` : '<p class="no-files-message">No pre-configured input files found for this service</p>'}
                    <button type="button" class="btn btn-info" onclick="loadInputFile('${serviceName}')">
                        Load File
                    </button>
                    <hr>
                </div>
            </div>
        `;

        // generate variable fields
        if (manifest.inputs && manifest.inputs.variables) {
            const variablesSection = document.createElement('div');
            variablesSection.className = 'form-section';
            variablesSection.innerHTML = '<h4>Variables</h4>';

            manifest.inputs.variables.forEach(input => {
                const field = this.createFormField(input);
                variablesSection.appendChild(field);
            });

            form.appendChild(variablesSection);
        }

        // generate secret fields
        if (manifest.inputs && manifest.inputs.secrets && manifest.inputs.secrets.length > 0) {
            const secretsSection = document.createElement('div');
            secretsSection.className = 'form-section';
            secretsSection.innerHTML = '<h4>Secrets</h4>';

            const secretsField = this.createSecretsField(manifest.inputs.secrets);
            secretsSection.appendChild(secretsField);

            form.appendChild(secretsSection);
        }

        // generate file fields
        if (manifest.inputs && manifest.inputs.files && manifest.inputs.files.length > 0) {
            const filesSection = document.createElement('div');
            filesSection.className = 'form-section';
            filesSection.innerHTML = '<h4>Files</h4>';

            const filesField = this.createFilesField(manifest.inputs.files);
            filesSection.appendChild(filesField);

            form.appendChild(filesSection);
        }

        // operation selector for opentofu moved to top of form

        // add action buttons
        form.innerHTML += `
            <div class="form-actions">
                <button type="submit" class="btn btn-primary">Execute</button>
                <button type="button" class="btn btn-secondary" onclick="closeInputForm()">Cancel</button>
                <button type="button" class="btn btn-info" onclick="validateInputs('${serviceName}')">Validate</button>
            </div>
        `;

        return form;
    }

    async generateBasicForm(serviceName, serviceType, operation = null) {
        const form = document.createElement('form');
        form.className = 'service-input-form basic-form';
        form.id = 'service-input-form';

        // load available input files even for basic form
        const availableFiles = await this.loadAvailableInputFiles(serviceName);

        form.innerHTML = `
            <div class="form-header">
                <h3>Execute Service: ${serviceName}</h3>
                <p class="service-type">Type: ${serviceType}</p>
                <p class="form-note">No input manifest found. Using basic form.</p>
            </div>

            ${serviceType === 'opentofu-plan' ? `
                <div class="form-section opentofu-operation-section">
                    <div class="operation-selector">
                        <label class="operation-option ${!operation || operation === 'apply' ? 'selected' : ''}">
                            <input type="radio" name="operation" value="apply" ${!operation || operation === 'apply' ? 'checked' : ''}>
                            <span class="operation-text">
                                <strong>APPLY</strong>
                                <small>Provision Infrastructure</small>
                            </span>
                        </label>
                        <label class="operation-option ${operation === 'destroy' ? 'selected' : ''}">
                            <input type="radio" name="operation" value="destroy" ${operation === 'destroy' ? 'checked' : ''}>
                            <span class="operation-text">
                                <strong>DESTROY</strong>
                                <small>Deprovision Infrastructure</small>
                            </span>
                        </label>
                    </div>
                </div>
            ` : ''}

            <div class="input-file-loader">
                <div class="loader-header">
                    <h4>Load from Input File (Optional)</h4>
                    <button type="button" class="btn btn-sm btn-secondary" onclick="toggleInputFileLoader()">
                        ▼ Show/Hide
                    </button>
                </div>
                <div id="input-file-section" class="input-file-section" style="display: none;">
                    <div class="form-field">
                        <label for="input-file-path">Input File Path</label>
                        <input type="text" id="input-file-path" class="form-control"
                               placeholder="@inputs/vpc.yaml or /absolute/path/config.yaml">
                        <small class="help-text">Use @ prefix for paths relative to /home/admin/data</small>
                    </div>
                    ${availableFiles && availableFiles.length > 0 ? `
                        <div class="form-field">
                            <label>Or Select Available File:</label>
                            <select id="preset-selector" class="form-control" onchange="selectPresetFile(this.value)">
                                <option value="">-- Select an input file --</option>
                                ${availableFiles.map(file => `
                                    <option value="${file.path}">
                                        ${file.filename}
                                    </option>
                                `).join('')}
                            </select>
                        </div>
                    ` : '<p class="no-files-message">No pre-configured input files found for this service</p>'}
                    <button type="button" class="btn btn-info" onclick="loadInputFile('${serviceName}')">
                        Load File
                    </button>
                    <hr>
                </div>
            </div>

            <div class="form-section">
                <h4>Parameters</h4>
                <div class="form-field">
                    <label for="basic-params">Parameters (JSON format)</label>
                    <textarea id="basic-params" name="parameters" rows="4"
                              placeholder='{"key": "value"}'></textarea>
                </div>
            </div>

            <!-- operation selector for opentofu moved to top of form -->

            <div class="form-actions">
                <button type="submit" class="btn btn-primary">Execute</button>
                <button type="button" class="btn btn-secondary" onclick="closeInputForm()">Cancel</button>
            </div>
        `;

        return form;
    }

    createFormField(input) {
        const container = document.createElement('div');
        container.className = 'form-field';

        const label = document.createElement('label');
        label.textContent = input.description || input.name;
        if (input.required) {
            label.classList.add('required');
            label.innerHTML += ' <span class="required-mark">*</span>';
        }
        label.setAttribute('for', `input-${input.name}`);

        let field;
        switch (input.type) {
            case 'string':
                if (input.validation && input.validation.enum) {
                    field = this.createSelectField(input);
                } else {
                    field = this.createTextField(input);
                }
                break;
            case 'integer':
            case 'number':
                field = this.createNumberField(input);
                break;
            case 'boolean':
                field = this.createCheckboxField(input);
                break;
            case 'file':
                field = this.createFileField(input);
                break;
            case 'array':
            case 'object':
                field = this.createJsonField(input);
                break;
            default:
                field = this.createTextField(input);
        }

        container.appendChild(label);
        container.appendChild(field);

        // add help text if available
        if (input.description && input.description !== input.name) {
            const helpText = document.createElement('small');
            helpText.className = 'help-text';
            helpText.textContent = input.description;
            container.appendChild(helpText);
        }

        return container;
    }

    createTextField(input) {
        const field = document.createElement('input');
        field.type = 'text';
        field.id = `input-${input.name}`;
        field.name = input.name;
        field.className = 'form-control';

        if (input.default !== undefined) {
            field.value = input.default;
        }

        if (input.required) {
            field.required = true;
        }

        if (input.validation) {
            if (input.validation.min_length) {
                field.minLength = input.validation.min_length;
            }
            if (input.validation.max_length) {
                field.maxLength = input.validation.max_length;
            }
        }

        return field;
    }

    createSelectField(input) {
        const field = document.createElement('select');
        field.id = `input-${input.name}`;
        field.name = input.name;
        field.className = 'form-control';

        if (input.required) {
            field.required = true;
        }

        // add options
        if (input.validation && input.validation.enum) {
            input.validation.enum.forEach(value => {
                const option = document.createElement('option');
                option.value = value;
                option.textContent = value;
                if (input.default === value) {
                    option.selected = true;
                }
                field.appendChild(option);
            });
        }

        return field;
    }

    createNumberField(input) {
        const field = document.createElement('input');
        field.type = 'number';
        field.id = `input-${input.name}`;
        field.name = input.name;
        field.className = 'form-control';

        if (input.default !== undefined) {
            field.value = input.default;
        }

        if (input.required) {
            field.required = true;
        }

        if (input.validation) {
            if (input.validation.min !== undefined) {
                field.min = input.validation.min;
            }
            if (input.validation.max !== undefined) {
                field.max = input.validation.max;
            }
        }

        return field;
    }

    createCheckboxField(input) {
        const container = document.createElement('div');
        container.className = 'checkbox-container';

        const field = document.createElement('input');
        field.type = 'checkbox';
        field.id = `input-${input.name}`;
        field.name = input.name;
        field.className = 'form-check';

        if (input.default === true) {
            field.checked = true;
        }

        container.appendChild(field);
        return container;
    }

    createFileField(input) {
        const field = document.createElement('input');
        field.type = 'text';
        field.id = `input-${input.name}`;
        field.name = input.name;
        field.className = 'form-control';
        field.placeholder = input.path || 'Enter file path or use @notation';

        if (input.default !== undefined) {
            field.value = input.default;
        }

        if (input.required) {
            field.required = true;
        }

        return field;
    }

    createJsonField(input) {
        const field = document.createElement('textarea');
        field.id = `input-${input.name}`;
        field.name = input.name;
        field.className = 'form-control json-field';
        field.rows = 3;
        field.setAttribute('data-type', input.type);

        // Set placeholder based on type
        if (input.type === 'array') {
            field.placeholder = input.placeholder || '["value1", "value2", ...]';
        } else {
            field.placeholder = input.placeholder || '{"key": "value", ...}';
        }

        // Set default value - stringify if it's an object/array
        if (input.default !== undefined) {
            if (typeof input.default === 'object') {
                field.value = JSON.stringify(input.default, null, 2);
            } else {
                field.value = input.default;
            }
        }

        if (input.required) {
            field.required = true;
        }

        return field;
    }

    createSecretsField(secrets) {
        const container = document.createElement('div');
        container.className = 'secrets-container';

        secrets.forEach(secret => {
            const secretDiv = document.createElement('div');
            secretDiv.className = 'secret-item';

            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.id = `secret-${secret.name}`;
            checkbox.name = 'secrets';
            checkbox.value = secret.name;

            if (secret.required) {
                checkbox.checked = true;
                checkbox.disabled = true;
            }

            const label = document.createElement('label');
            label.setAttribute('for', `secret-${secret.name}`);
            label.textContent = secret.description || secret.name;

            secretDiv.appendChild(checkbox);
            secretDiv.appendChild(label);
            container.appendChild(secretDiv);
        });

        return container;
    }

    createFilesField(files) {
        const container = document.createElement('div');
        container.className = 'files-container';

        files.forEach(file => {
            const fileDiv = document.createElement('div');
            fileDiv.className = 'file-item form-field';

            const label = document.createElement('label');
            label.textContent = file.description || file.name;
            label.setAttribute('for', `file-${file.name}`);

            const input = document.createElement('input');
            input.type = 'text';
            input.id = `file-${file.name}`;
            input.name = `file-${file.name}`;
            input.className = 'form-control';
            input.placeholder = file.path || 'Enter file path';

            if (file.default) {
                input.value = file.default;
            }

            fileDiv.appendChild(label);
            fileDiv.appendChild(input);
            container.appendChild(fileDiv);
        });

        return container;
    }

    async submitForm(formData) {
        const serviceName = this.currentService;
        const inputs = this.extractFormInputs(formData);

        // Check if there's an input file path specified
        const inputFilePath = document.getElementById('input-file-path')?.value;

        try {
            const requestBody = {
                operation: formData.get('operation')
            };

            // If input file is specified, use it; otherwise use form inputs
            if (inputFilePath) {
                requestBody.input_file = inputFilePath;
                // Still include form inputs as overrides
                if (Object.keys(inputs.variables).length > 0 ||
                    inputs.secrets.length > 0 ||
                    Object.keys(inputs.files).length > 0) {
                    requestBody.inputs = inputs;
                }
            } else {
                requestBody.inputs = inputs;
            }

            const response = await fetch(`/api/execute/${serviceName}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCsrfToken(),
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestBody)
            });

            const result = await response.json();

            if (response.ok) {
                showToast('Service execution started', 'success');
                closeInputForm();
                refreshDashboard();
                refreshQueueStatus();
            } else {
                showToast(result.message || 'Execution failed', 'error');
            }
        } catch (error) {
            console.error('Error submitting form:', error);
            showToast('Failed to execute service', 'error');
        }
    }

    extractFormInputs(formData) {
        const inputs = {
            variables: {},
            secrets: [],
            files: {}
        };

        // extract variables
        for (const [key, value] of formData.entries()) {
            if (!key.startsWith('secret-') && !key.startsWith('file-') &&
                key !== 'operation' && key !== 'parameters') {

                // Get the field element to check its data-type
                const field = document.getElementById(`input-${key}`);
                const isJsonField = field && (field.getAttribute('data-type') === 'array' ||
                                             field.getAttribute('data-type') === 'object');

                if (isJsonField && value) {
                    // Parse JSON fields
                    try {
                        inputs.variables[key] = JSON.parse(value);
                    } catch (e) {
                        console.error(`Failed to parse JSON for ${key}:`, e);
                        // If parsing fails, keep it as string
                        inputs.variables[key] = value;
                    }
                } else if (field && field.type === 'checkbox') {
                    // Handle checkbox as boolean
                    inputs.variables[key] = field.checked;
                } else if (value === '') {
                    // Empty string stays empty (not false)
                    // Skip empty non-required fields
                    if (field && !field.required) {
                        continue;
                    }
                    inputs.variables[key] = value;
                } else {
                    // Regular string value
                    inputs.variables[key] = value;
                }
            }
        }

        // extract secrets
        const secretCheckboxes = document.querySelectorAll('input[name="secrets"]:checked');
        secretCheckboxes.forEach(checkbox => {
            inputs.secrets.push(checkbox.value);
        });

        // extract files
        formData.forEach((value, key) => {
            if (key.startsWith('file-') && value) {
                const fileName = key.replace('file-', '');
                inputs.files[fileName] = value;
            }
        });

        // handle basic form with raw parameters
        if (formData.has('parameters')) {
            try {
                const params = JSON.parse(formData.get('parameters'));
                inputs.variables = params;
            } catch (e) {
                console.error('Invalid JSON in parameters:', e);
            }
        }

        return inputs;
    }
}

// global instance
const serviceInputForm = new ServiceInputForm();

// wrapper function for OpenTofu with operation
// show input form modal
async function showInputForm(serviceName, serviceType, operation = null) {
    const modal = document.getElementById('input-form-modal');
    if (!modal) {
        // create modal if it doesn't exist
        const modalHtml = `
            <div id="input-form-modal" class="modal">
                <div class="modal-content input-form-content">
                    <span class="close" onclick="closeInputForm()">&times;</span>
                    <div id="input-form-container"></div>
                </div>
            </div>
        `;
        document.body.insertAdjacentHTML('beforeend', modalHtml);
    }

    const container = document.getElementById('input-form-container');
    const form = await serviceInputForm.generateForm(serviceName, serviceType, operation);

    container.innerHTML = '';
    container.appendChild(form);

    // attach submit handler
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(form);
        await serviceInputForm.submitForm(formData);
    });

    document.getElementById('input-form-modal').style.display = 'block';
}

// close input form modal
function closeInputForm() {
    const modal = document.getElementById('input-form-modal');
    if (modal) {
        modal.style.display = 'none';
    }
}

// handle OpenTofu operation selection
document.addEventListener('change', function(event) {
    if (event.target.type === 'radio' && event.target.name === 'operation') {
        const operationOptions = document.querySelectorAll('.operation-option');
        operationOptions.forEach(option => {
            const radio = option.querySelector('input[type="radio"]');
            if (radio && radio.checked) {
                option.classList.add('selected');
            } else {
                option.classList.remove('selected');
            }
        });
    }
});

// validate inputs
async function validateInputs(serviceName) {
    const form = document.getElementById('service-input-form');
    if (!form) return;

    const formData = new FormData(form);
    const inputs = serviceInputForm.extractFormInputs(formData);

    try {
        const response = await fetch(`/api/services/${serviceName}/validate/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCsrfToken(),
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(inputs)
        });

        const result = await response.json();

        if (result.valid) {
            showToast('Inputs are valid', 'success');
        } else {
            const errorMsg = 'Validation errors:\n' + result.errors.join('\n');
            alert(errorMsg);
        }
    } catch (error) {
        console.error('Error validating inputs:', error);
        showToast('Failed to validate inputs', 'error');
    }
}

// enhanced execute service with input form
async function executeServiceWithInputs(serviceName, serviceType, button) {
    // show input form instead of direct execution
    showInputForm(serviceName, serviceType);
}

// toggle input file loader section
function toggleInputFileLoader() {
    const section = document.getElementById('input-file-section');
    if (section) {
        section.style.display = section.style.display === 'none' ? 'block' : 'none';
    }
}

// select preset file
function selectPresetFile(filePath) {
    if (filePath) {
        document.getElementById('input-file-path').value = filePath;
    }
}

// load input file and populate form
async function loadInputFile(serviceName) {
    const filePath = document.getElementById('input-file-path').value;
    if (!filePath) {
        showToast('Please enter a file path', 'warning');
        return;
    }

    try {
        // Call API to load the input file
        const response = await fetch('/api/load-input-file/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCsrfToken(),
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                file_path: filePath,
                service_name: serviceName
            })
        });

        if (!response.ok) {
            throw new Error('Failed to load input file');
        }

        const data = await response.json();

        if (data.status === 'success' && data.inputs) {
            // Populate form fields with loaded data
            populateFormFromInputs(data.inputs);
            showToast('Input file loaded successfully', 'success');

            // Hide the loader section after successful load
            document.getElementById('input-file-section').style.display = 'none';
        } else {
            showToast(data.message || 'Failed to load input file', 'error');
        }
    } catch (error) {
        console.error('Error loading input file:', error);
        showToast('Failed to load input file', 'error');
    }
}

// populate form fields from loaded inputs
function populateFormFromInputs(inputs) {
    // Populate variables
    if (inputs.variables) {
        Object.entries(inputs.variables).forEach(([key, value]) => {
            const field = document.getElementById(`input-${key}`);
            if (field) {
                if (field.type === 'checkbox') {
                    field.checked = value === true || value === 'true';
                } else if (field.type === 'select-one') {
                    field.value = value;
                } else {
                    field.value = typeof value === 'object' ? JSON.stringify(value) : value;
                }
            }
        });
    }

    // Populate secrets
    if (inputs.secrets) {
        inputs.secrets.forEach(secretName => {
            const checkbox = document.getElementById(`secret-${secretName}`);
            if (checkbox) {
                checkbox.checked = true;
            }
        });
    }

    // Populate files
    if (inputs.files) {
        Object.entries(inputs.files).forEach(([key, value]) => {
            const field = document.getElementById(`file-${key}`);
            if (field) {
                field.value = value;
            }
        });
    }

    // Handle basic form with parameters field
    const paramsField = document.getElementById('basic-params');
    if (paramsField && inputs.variables) {
        paramsField.value = JSON.stringify(inputs.variables, null, 2);
    }
}