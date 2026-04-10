/**
 * Projects Page JavaScript
 * Handles project listing, CRUD operations, actions, and service management
 */

let projects = [];
let currentFilter = 'all';
let deleteProjectId = null;
let serviceCounter = 1;
let isLoading = false;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    console.log('[Projects] Initializing...');
    try {
        initEventListeners();
        loadProjects();
        startAutoRefresh();
        console.log('[Projects] Initialization complete');
    } catch (err) {
        console.error('[Projects] Initialization failed:', err);
        showLoadingError('Failed to initialize: ' + err.message);
    }
});

function initEventListeners() {
    console.log('[Projects] Setting up event listeners...');
    
    // Search
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        searchInput.addEventListener('input', debounce(filterProjects, 300));
    }
    
    // Filter tabs
    document.querySelectorAll('[data-filter]').forEach(tab => {
        tab.addEventListener('click', (e) => {
            e.preventDefault();
            document.querySelectorAll('[data-filter]').forEach(t => t.classList.remove('active'));
            e.target.classList.add('active');
            currentFilter = e.target.dataset.filter;
            renderProjects();
        });
    });
    
    // Add project form
    const saveBtn = document.getElementById('save-project-btn');
    if (saveBtn) {
        saveBtn.addEventListener('click', addProject);
    }
    
    // Update project form
    const updateBtn = document.getElementById('update-project-btn');
    if (updateBtn) {
        updateBtn.addEventListener('click', updateProject);
    }
    
    // Delete confirmation
    const deleteBtn = document.getElementById('confirm-delete-btn');
    if (deleteBtn) {
        deleteBtn.addEventListener('click', deleteProject);
    }
    
    // Paste from clipboard buttons
    const browseBtn = document.getElementById('browse-btn');
    if (browseBtn) {
        browseBtn.addEventListener('click', pasteFromClipboard);
    }
    
    const editBrowseBtn = document.getElementById('edit-browse-btn');
    if (editBrowseBtn) {
        editBrowseBtn.addEventListener('click', pasteFromClipboardEdit);
    }
    
    // Validate directory on input
    const dirInput = document.getElementById('project-dir');
    if (dirInput) {
        dirInput.addEventListener('blur', validateDirectory);
    }
    
    // Add service buttons
    const addServiceBtn = document.getElementById('add-service-btn');
    if (addServiceBtn) {
        addServiceBtn.addEventListener('click', () => addServiceRow());
    }
    
    const editAddServiceBtn = document.getElementById('edit-add-service-btn');
    if (editAddServiceBtn) {
        editAddServiceBtn.addEventListener('click', () => addEditServiceRow());
    }
    
    console.log('[Projects] Event listeners attached');
}

async function loadProjects() {
    if (isLoading) return;
    isLoading = true;
    
    const grid = document.getElementById('projects-grid');
    if (!grid) {
        console.error('[Projects] Grid element not found');
        isLoading = false;
        return;
    }
    
    // Show loading spinner
    grid.innerHTML = `
        <div class="col-12 text-center py-5">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <p class="mt-2 text-muted">Loading projects...</p>
        </div>
    `;
    
    try {
        console.log('[Projects] Fetching projects from API...');
        const result = await api('/api/projects');
        console.log('[Projects] Raw API response:', result);
        
        // Normalize response - handle various possible shapes
        let projectsData = null;
        
        if (Array.isArray(result)) {
            // Direct array response
            projectsData = result;
        } else if (result && typeof result === 'object') {
            if (result.success === true && Array.isArray(result.data)) {
                // Standard {success: true, data: [...]} format
                projectsData = result.data;
            } else if (result.success === true && result.projects && Array.isArray(result.projects)) {
                // Alternative {success: true, projects: [...]} format
                projectsData = result.projects;
            } else if (Array.isArray(result.data)) {
                // {data: [...]} without success flag
                projectsData = result.data;
            } else if (result.success === false) {
                // Error response
                console.error('[Projects] API returned error:', result.error);
                showLoadingError(result.error || 'Failed to load projects from server');
                isLoading = false;
                return;
            }
        }
        
        // Validate we got an array
        if (!Array.isArray(projectsData)) {
            console.error('[Projects] Invalid response format. Expected array, got:', typeof projectsData, projectsData);
            showLoadingError('Invalid response format from server. Check console for details.');
            isLoading = false;
            return;
        }
        
        projects = projectsData;
        console.log(`[Projects] Loaded ${projects.length} projects`);
        
        updateStats();
        renderProjects();
    } catch (err) {
        console.error('[Projects] Error loading projects:', err);
        showLoadingError(err.message || 'Network error loading projects');
    } finally {
        isLoading = false;
    }
}

function showLoadingError(message) {
    const grid = document.getElementById('projects-grid');
    if (!grid) return;
    
    grid.innerHTML = `
        <div class="col-12">
            <div class="empty-state">
                <i class="bi bi-exclamation-triangle-fill text-danger"></i>
                <h5 class="text-danger">Failed to load projects</h5>
                <p class="text-muted">${escapeHtml(message)}</p>
                <button class="btn btn-primary" onclick="loadProjects()">
                    <i class="bi bi-arrow-clockwise me-2"></i>Retry
                </button>
            </div>
        </div>
    `;
}

function updateStats() {
    try {
        const total = projects.length;
        const running = projects.filter(p => p.status === 'running' || p.status === 'partial').length;
        const stopped = projects.filter(p => p.status === 'stopped').length;
        const crashed = projects.filter(p => p.status === 'crashed').length;
        
        const totalEl = document.getElementById('stat-total');
        const runningEl = document.getElementById('stat-running');
        const stoppedEl = document.getElementById('stat-stopped');
        const crashedEl = document.getElementById('stat-crashed');
        
        if (totalEl) totalEl.textContent = total;
        if (runningEl) runningEl.textContent = running;
        if (stoppedEl) stoppedEl.textContent = stopped;
        if (crashedEl) crashedEl.textContent = crashed;
    } catch (err) {
        console.error('[Projects] Error updating stats:', err);
    }
}

function filterProjects() {
    renderProjects();
}

function renderProjects() {
    const grid = document.getElementById('projects-grid');
    if (!grid) return;
    
    // Validate projects is an array
    if (!Array.isArray(projects)) {
        console.error('[Projects] Cannot render: projects is not an array', projects);
        grid.innerHTML = `
            <div class="col-12">
                <div class="empty-state">
                    <i class="bi bi-exclamation-triangle-fill text-danger"></i>
                    <h5 class="text-danger">Data Error</h5>
                    <p class="text-muted">Projects data is corrupted. Check console.</p>
                    <button class="btn btn-primary" onclick="loadProjects()">
                        <i class="bi bi-arrow-clockwise me-2"></i>Retry
                    </button>
                </div>
            </div>
        `;
        return;
    }
    
    const searchInput = document.getElementById('search-input');
    const searchTerm = searchInput?.value.toLowerCase() || '';
    
    let filtered = projects.filter(p => {
        // Defensive: skip null/undefined projects
        if (!p || typeof p !== 'object') return false;
        
        const name = (p.name || '').toLowerCase();
        const dir = (p.dir || '').toLowerCase();
        const matchesSearch = name.includes(searchTerm) || dir.includes(searchTerm);
        
        if (!matchesSearch) return false;
        
        if (currentFilter === 'all') return true;
        if (currentFilter === 'auto') return p.mode === 'auto';
        if (currentFilter === 'manual') return p.mode === 'manual';
        return p.status === currentFilter;
    });
    
    if (filtered.length === 0) {
        grid.innerHTML = `
            <div class="col-12">
                <div class="empty-state">
                    <i class="bi bi-folder-x"></i>
                    <h5>No projects found</h5>
                    <p class="text-muted">
                        ${projects.length === 0 
                            ? 'Add your first project to get started' 
                            : 'Try adjusting your search or filter'}
                    </p>
                    ${projects.length === 0 
                        ? '<button class="btn btn-primary" data-bs-toggle="modal" data-bs-target="#addProjectModal"><i class="bi bi-plus-lg me-2"></i>Add Project</button>'
                        : ''}
                </div>
            </div>
        `;
        return;
    }
    
    try {
        grid.innerHTML = filtered.map(project => createProjectCard(project)).join('');
    } catch (err) {
        console.error('[Projects] Error rendering project cards:', err);
        grid.innerHTML = `
            <div class="col-12 text-center py-5 text-danger">
                <i class="bi bi-exclamation-triangle fs-1"></i>
                <p class="mt-2">Error displaying projects</p>
                <small class="text-muted">${escapeHtml(err.message)}</small>
            </div>
        `;
    }
}

function createProjectCard(project) {
    try {
        const statusClass = project.status || 'unknown';
        const isRunning = project.status === 'running' || project.status === 'partial';
        const hasMultipleServices = project.services_count > 1;
        
        // Get primary service for display
        const primaryService = project.services?.[0];
        
        // Services summary
        let servicesSummary = '';
        if (hasMultipleServices) {
            const runningCount = project.services?.filter(s => s.status === 'running').length || 0;
            servicesSummary = `
                <div class="project-services-summary">
                    <i class="bi bi-layers me-1"></i>
                    ${project.services_count} services (${runningCount} running)
                    <button class="btn btn-sm btn-link p-0 ms-2" onclick="showServicesModal('${project.id}')">
                        View all
                    </button>
                </div>
            `;
        }
        
        return `
            <div class="col-12 col-md-6 col-lg-4 fade-in">
                <div class="project-card ${statusClass}">
                    <div class="project-header">
                        <h5 class="project-title" title="${escapeHtml(project.name)}">${escapeHtml(project.name)}</h5>
                        <div class="project-badges">
                            ${App.getStatusBadge(project.status)}
                            ${App.getModeBadge(project.mode, project.id)}
                        </div>
                    </div>
                    
                    <div class="project-info">
                        <div class="project-info-item" title="${escapeHtml(project.dir)}">
                            <i class="bi bi-folder"></i>
                            <span class="value">${escapeHtml(truncatePath(project.dir, 35))}</span>
                        </div>
                        ${!hasMultipleServices && primaryService ? `
                        <div class="project-info-item" title="${escapeHtml(primaryService.cmd)}">
                            <i class="bi bi-terminal"></i>
                            <code class="value">${escapeHtml(truncatePath(primaryService.cmd, 35))}</code>
                        </div>
                        ` : ''}
                        ${primaryService?.pid ? `
                        <div class="project-info-item">
                            <i class="bi bi-hash"></i>
                            <span class="value">PID: ${primaryService.pid}</span>
                        </div>
                        ` : ''}
                        ${primaryService?.uptime ? `
                        <div class="project-info-item">
                            <i class="bi bi-clock"></i>
                            <span class="value">Uptime: ${primaryService.uptime}</span>
                        </div>
                        ` : ''}
                        ${servicesSummary}
                    </div>
                    
                    <div class="project-actions">
                        ${isRunning ? `
                            <button class="btn btn-warning btn-sm" onclick="stopProject('${project.id}')">
                                <i class="bi bi-stop-fill"></i> Stop
                            </button>
                            <button class="btn btn-info btn-sm" onclick="restartProject('${project.id}')">
                                <i class="bi bi-arrow-clockwise"></i> Restart
                            </button>
                        ` : `
                            <button class="btn btn-success btn-sm" onclick="startProject('${project.id}')">
                                <i class="bi bi-play-fill"></i> Start
                            </button>
                            <button class="btn btn-secondary btn-sm" disabled>
                                <i class="bi bi-stop-fill"></i> Stop
                            </button>
                        `}
                        <button class="btn btn-outline-secondary btn-sm" onclick="editProject('${project.id}')">
                            <i class="bi bi-pencil"></i>
                        </button>
                        <button class="btn btn-outline-danger btn-sm" onclick="confirmDelete('${project.id}')">
                            <i class="bi bi-trash"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;
    } catch (err) {
        console.error('[Projects] Error creating project card:', err, project);
        return `
            <div class="col-12 col-md-6 col-lg-4">
                <div class="project-card">
                    <div class="p-3 text-danger">
                        <i class="bi bi-exclamation-triangle"></i>
                        Error displaying project
                    </div>
                </div>
            </div>
        `;
    }
}

async function addProject() {
    console.log('[Projects] Adding new project...');
    
    const nameInput = document.getElementById('project-name');
    const dirInput = document.getElementById('project-dir');
    const modeInput = document.querySelector('input[name="project-mode"]:checked');
    
    if (!nameInput || !dirInput) {
        showToast('Form elements not found', 'error');
        return;
    }
    
    const name = nameInput.value.trim();
    const dir = dirInput.value.trim();
    const mode = modeInput?.value || 'manual';
    
    if (!name || !dir) {
        showToast('Please fill in all required fields', 'warning');
        return;
    }
    
    // Collect services
    const services = [];
    const serviceRows = document.querySelectorAll('#services-container .service-row');
    
    serviceRows.forEach((row, index) => {
        const nameInput = row.querySelector('.service-name');
        const cmdInput = row.querySelector('.service-cmd');
        const dirInput = row.querySelector('.service-dir');
        const stopCmdInput = row.querySelector('.service-stop-cmd');
        
        if (nameInput && cmdInput && cmdInput.value.trim()) {
            const serviceDir = dirInput?.value.trim() || dir;
            services.push({
                id: index === 0 ? 'default' : `svc_${index}`,
                name: nameInput.value.trim(),
                cmd: cmdInput.value.trim(),
                dir: serviceDir,
                stop_cmd: stopCmdInput?.value.trim() || ''
            });
        }
    });
    
    if (services.length === 0) {
        showToast('At least one service with a command is required', 'warning');
        return;
    }
    
    const btn = document.getElementById('save-project-btn');
    const originalText = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Creating...';
    
    try {
        const payload = { name, dir, mode, services };
        console.log('[Projects] Sending create request with payload:', payload);
        const result = await api('/api/projects', {
            method: 'POST',
            body: JSON.stringify(payload)
        });
        console.log('[Projects] Create response:', result);
        
        if (result.success) {
            showToast('Project created successfully', 'success');
            
            // Close modal
            const modalEl = document.getElementById('addProjectModal');
            const modal = bootstrap.Modal.getInstance(modalEl);
            if (modal) modal.hide();
            
            // Clear form
            document.getElementById('add-project-form')?.reset();
            dirInput.classList.remove('is-valid', 'is-invalid');
            resetServiceRows();
            
            // Reload projects
            await loadProjects();
            
            // Auto-start if in auto mode
            if (mode === 'auto' && result.data?.project?.id) {
                await startProject(result.data.project.id);
            }
        } else {
            console.error('[Projects] Create failed:', result.error);
            showToast(result.error || 'Failed to create project', 'error');
        }
    } catch (err) {
        console.error('[Projects] Error creating project:', err);
        showToast('Error: ' + err.message, 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = originalText;
    }
}

async function editProject(projectId) {
    console.log('[Projects] Editing project:', projectId);
    
    const project = projects.find(p => p.id === projectId);
    if (!project) {
        showToast('Project not found', 'error');
        return;
    }
    
    const idInput = document.getElementById('edit-project-id');
    const nameInput = document.getElementById('edit-project-name');
    const dirInput = document.getElementById('edit-project-dir');
    
    if (!idInput || !nameInput || !dirInput) {
        showToast('Form elements not found', 'error');
        return;
    }
    
    idInput.value = project.id;
    nameInput.value = project.name;
    dirInput.value = project.dir;
    
    // Load services into edit form
    const container = document.getElementById('edit-services-container');
    if (container) {
        container.innerHTML = '';
        
        if (project.services && project.services.length > 0) {
            project.services.forEach((service, index) => {
                addEditServiceRow(service, index === 0);
            });
        } else {
            // Legacy single service
            addEditServiceRow({
                name: 'Main',
                cmd: project.start_cmd || '',
                stop_cmd: project.stop_cmd || ''
            }, true);
        }
    }
    
    const modalEl = document.getElementById('editProjectModal');
    const modal = new bootstrap.Modal(modalEl);
    modal.show();
}

async function updateProject() {
    const projectId = document.getElementById('edit-project-id')?.value;
    const name = document.getElementById('edit-project-name')?.value.trim();
    const dir = document.getElementById('edit-project-dir')?.value.trim();
    
    if (!projectId || !name || !dir) {
        showToast('Please fill in all required fields', 'warning');
        return;
    }
    
    // Collect services
    const services = [];
    const serviceRows = document.querySelectorAll('#edit-services-container .service-row');
    
    serviceRows.forEach((row, index) => {
        const nameInput = row.querySelector('.service-name');
        const cmdInput = row.querySelector('.service-cmd');
        const dirInput = row.querySelector('.service-dir');
        const stopCmdInput = row.querySelector('.service-stop-cmd');
        
        if (nameInput && cmdInput && cmdInput.value.trim()) {
            const serviceDir = dirInput?.value.trim() || dir;
            services.push({
                id: index === 0 ? 'default' : `svc_${index}`,
                name: nameInput.value.trim(),
                cmd: cmdInput.value.trim(),
                dir: serviceDir,
                stop_cmd: stopCmdInput?.value.trim() || ''
            });
        }
    });
    
    if (services.length === 0) {
        showToast('At least one service with a command is required', 'warning');
        return;
    }
    
    const btn = document.getElementById('update-project-btn');
    const originalText = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Saving...';
    
    try {
        const result = await api(`/api/projects/${projectId}`, {
            method: 'PUT',
            body: JSON.stringify({ name, dir, services })
        });
        
        if (result.success) {
            showToast('Project updated successfully', 'success');
            
            const modalEl = document.getElementById('editProjectModal');
            const modal = bootstrap.Modal.getInstance(modalEl);
            if (modal) modal.hide();
            
            await loadProjects();
        } else {
            showToast(result.error || 'Failed to update project', 'error');
        }
    } catch (err) {
        showToast('Error: ' + err.message, 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = originalText;
    }
}

function confirmDelete(projectId) {
    const project = projects.find(p => p.id === projectId);
    if (!project) return;
    
    deleteProjectId = projectId;
    
    const nameEl = document.getElementById('delete-project-name');
    if (nameEl) nameEl.textContent = project.name;
    
    const modalEl = document.getElementById('deleteModal');
    const modal = new bootstrap.Modal(modalEl);
    modal.show();
}

async function deleteProject() {
    if (!deleteProjectId) return;
    
    const btn = document.getElementById('confirm-delete-btn');
    const originalText = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Deleting...';
    
    try {
        const result = await api(`/api/projects/${deleteProjectId}`, { method: 'DELETE' });
        
        if (result.success) {
            showToast('Project deleted successfully', 'success');
            
            const modalEl = document.getElementById('deleteModal');
            const modal = bootstrap.Modal.getInstance(modalEl);
            if (modal) modal.hide();
            
            deleteProjectId = null;
            await loadProjects();
        } else {
            showToast(result.error || 'Failed to delete project', 'error');
        }
    } catch (err) {
        showToast('Error: ' + err.message, 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = originalText;
    }
}

async function startProject(projectId) {
    showToast('Starting project...', 'info');
    
    try {
        const result = await api(`/api/projects/${projectId}/start`, { method: 'POST' });
        
        if (result.success) {
            showToast('Project started successfully', 'success');
        } else {
            showToast(result.error || 'Failed to start project', 'error');
        }
        await loadProjects();
    } catch (err) {
        showToast('Error: ' + err.message, 'error');
    }
}

async function stopProject(projectId) {
    showToast('Stopping project...', 'info');
    
    try {
        const result = await api(`/api/projects/${projectId}/stop`, { method: 'POST' });
        
        if (result.success) {
            showToast('Project stopped', 'success');
        } else {
            showToast(result.error || 'Failed to stop project', 'error');
        }
        await loadProjects();
    } catch (err) {
        showToast('Error: ' + err.message, 'error');
    }
}

async function restartProject(projectId) {
    showToast('Restarting project...', 'info');
    
    try {
        const result = await api(`/api/projects/${projectId}/restart`, { method: 'POST' });
        
        if (result.success) {
            showToast('Project restarted successfully', 'success');
        } else {
            showToast(result.error || 'Failed to restart project', 'error');
        }
        await loadProjects();
    } catch (err) {
        showToast('Error: ' + err.message, 'error');
    }
}

async function showServicesModal(projectId) {
    const project = projects.find(p => p.id === projectId);
    if (!project || !project.services) return;
    
    const list = document.getElementById('services-list');
    if (!list) return;
    
    list.innerHTML = project.services.map(service => {
        const isRunning = service.status === 'running';
        return `
            <div class="d-flex align-items-center justify-content-between p-3 mb-2 rounded" 
                 style="background: var(--bg-hover);">
                <div>
                    <h6 class="mb-1">${escapeHtml(service.name)}</h6>
                    <code class="small">${escapeHtml(truncatePath(service.cmd, 50))}</code>
                    ${service.pid ? `<div class="small text-muted mt-1">PID: ${service.pid}</div>` : ''}
                </div>
                <div class="d-flex align-items-center gap-2">
                    ${App.getStatusBadge(service.status)}
                    <div class="btn-group btn-group-sm">
                        ${isRunning ? `
                            <button class="btn btn-warning" onclick="stopService('${projectId}', '${service.id}')">
                                <i class="bi bi-stop-fill"></i>
                            </button>
                        ` : `
                            <button class="btn btn-success" onclick="startService('${projectId}', '${service.id}')">
                                <i class="bi bi-play-fill"></i>
                            </button>
                        `}
                    </div>
                </div>
            </div>
        `;
    }).join('');
    
    const modalEl = document.getElementById('servicesModal');
    const modal = new bootstrap.Modal(modalEl);
    modal.show();
}

async function startService(projectId, serviceId) {
    showToast('Starting service...', 'info');
    
    try {
        const result = await api(`/api/projects/${projectId}/services/${serviceId}/start`, { method: 'POST' });
        
        if (result.success) {
            showToast('Service started', 'success');
            await loadProjects();
            const modalEl = document.getElementById('servicesModal');
            if (modalEl?.classList.contains('show')) {
                showServicesModal(projectId);
            }
        } else {
            showToast(result.error || 'Failed to start service', 'error');
        }
    } catch (err) {
        showToast('Error: ' + err.message, 'error');
    }
}

async function stopService(projectId, serviceId) {
    showToast('Stopping service...', 'info');
    
    try {
        const result = await api(`/api/projects/${projectId}/services/${serviceId}/stop`, { method: 'POST' });
        
        if (result.success) {
            showToast('Service stopped', 'success');
            await loadProjects();
            const modalEl = document.getElementById('servicesModal');
            if (modalEl?.classList.contains('show')) {
                showServicesModal(projectId);
            }
        } else {
            showToast(result.error || 'Failed to stop service', 'error');
        }
    } catch (err) {
        showToast('Error: ' + err.message, 'error');
    }
}

async function pasteFromClipboard() {
    try {
        const text = await navigator.clipboard.readText();
        const input = document.getElementById('project-dir');
        if (input) {
            input.value = text;
            validateDirectory();
        }
    } catch (err) {
        showToast('Could not access clipboard. Please paste manually.', 'warning');
    }
}

async function pasteFromClipboardEdit() {
    try {
        const text = await navigator.clipboard.readText();
        const input = document.getElementById('edit-project-dir');
        if (input) input.value = text;
    } catch (err) {
        showToast('Could not access clipboard. Please paste manually.', 'warning');
    }
}

async function validateDirectory() {
    const input = document.getElementById('project-dir');
    if (!input) return;
    
    const path = input.value.trim();
    if (!path) return;
    
    try {
        const result = await api('/api/validate-directory', {
            method: 'POST',
            body: JSON.stringify({ path })
        });
        
        if (result.success && result.data?.valid) {
            input.classList.remove('is-invalid');
            input.classList.add('is-valid');
        } else {
            input.classList.remove('is-valid');
            input.classList.add('is-invalid');
        }
    } catch (err) {
        input.classList.remove('is-valid');
        input.classList.add('is-invalid');
    }
}

function addServiceRow(service = null, isFirst = false) {
    const container = document.getElementById('services-container');
    if (!container) return;
    
    const index = container.children.length;
    
    const div = document.createElement('div');
    div.className = 'service-row card mb-2';
    div.innerHTML = `
        <div class="card-body py-2 px-3">
            <div class="row g-2 align-items-center">
                <div class="col-md-3">
                    <input type="text" class="form-control form-control-sm service-name" 
                           placeholder="Service name" value="${escapeHtml(service?.name || (isFirst ? 'Main' : `Service ${index + 1}`))}" required>
                </div>
                <div class="col-md-4">
                    <input type="text" class="form-control form-control-sm service-cmd font-monospace" 
                           placeholder="Command (e.g., python app.py)" value="${escapeHtml(service?.cmd || '')}" required>
                </div>
                <div class="col-md-3">
                    <input type="text" class="form-control form-control-sm service-dir font-monospace" 
                           placeholder="Directory (optional)" value="${escapeHtml(service?.dir || '')}">
                </div>
                <div class="col-md-2">
                    <div class="input-group input-group-sm">
                        <input type="text" class="form-control form-control-sm service-stop-cmd font-monospace" 
                               placeholder="Stop cmd (optional)" value="${escapeHtml(service?.stop_cmd || '')}">
                        ${!isFirst ? `
                        <button type="button" class="btn btn-outline-danger" onclick="this.closest('.service-row').remove()">
                            <i class="bi bi-trash"></i>
                        </button>
                        ` : ''}
                    </div>
                </div>
            </div>
        </div>
    `;
    
    container.appendChild(div);
}

function addEditServiceRow(service = null, isFirst = false) {
    const container = document.getElementById('edit-services-container');
    if (!container) return;
    
    const index = container.children.length;
    
    const div = document.createElement('div');
    div.className = 'service-row card mb-2';
    div.innerHTML = `
        <div class="card-body py-2 px-3">
            <div class="row g-2 align-items-center">
                <div class="col-md-3">
                    <input type="text" class="form-control form-control-sm service-name" 
                           placeholder="Service name" value="${escapeHtml(service?.name || (isFirst ? 'Main' : `Service ${index + 1}`))}" required>
                </div>
                <div class="col-md-4">
                    <input type="text" class="form-control form-control-sm service-cmd font-monospace" 
                           placeholder="Command (e.g., python app.py)" value="${escapeHtml(service?.cmd || '')}" required>
                </div>
                <div class="col-md-3">
                    <input type="text" class="form-control form-control-sm service-dir font-monospace" 
                           placeholder="Directory (optional)" value="${escapeHtml(service?.dir || '')}">
                </div>
                <div class="col-md-2">
                    <div class="input-group input-group-sm">
                        <input type="text" class="form-control form-control-sm service-stop-cmd font-monospace" 
                               placeholder="Stop cmd (optional)" value="${escapeHtml(service?.stop_cmd || '')}">
                        ${!isFirst ? `
                        <button type="button" class="btn btn-outline-danger" onclick="this.closest('.service-row').remove()">
                            <i class="bi bi-trash"></i>
                        </button>
                        ` : ''}
                    </div>
                </div>
            </div>
        </div>
    `;
    
    container.appendChild(div);
}

function resetServiceRows() {
    const container = document.getElementById('services-container');
    if (!container) return;
    
    container.innerHTML = `
        <div class="service-row card mb-2" data-service-index="0">
            <div class="card-body py-2 px-3">
                <div class="row g-2">
                    <div class="col-md-3">
                        <input type="text" class="form-control form-control-sm service-name" 
                               placeholder="Service name" value="Main" required>
                    </div>
                    <div class="col-md-4">
                        <input type="text" class="form-control form-control-sm service-cmd font-monospace" 
                               placeholder="Command (e.g., python app.py)" required>
                    </div>
                    <div class="col-md-3">
                        <input type="text" class="form-control form-control-sm service-dir font-monospace" 
                               placeholder="Directory (optional)">
                    </div>
                    <div class="col-md-2">
                        <input type="text" class="form-control form-control-sm service-stop-cmd font-monospace" 
                               placeholder="Stop cmd (optional)">
                    </div>
                </div>
            </div>
        </div>
    `;
}

function startAutoRefresh() {
    const settings = JSON.parse(localStorage.getItem('pm_settings') || '{}');
    const interval = (settings.refreshInterval || 5) * 1000;
    
    setInterval(() => {
        loadProjects();
    }, interval);
}

// Utility functions
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function truncatePath(path, maxLength) {
    if (!path) return '';
    if (path.length <= maxLength) return path;
    
    const start = path.substring(0, 15);
    const end = path.substring(path.length - (maxLength - 20));
    return `${start}...${end}`;
}
