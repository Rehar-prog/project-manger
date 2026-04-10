/**
 * Main Application JavaScript
 * Handles common functionality, sidebar, toasts, theme, and API calls
 */

// Global state
const App = {
    refreshInterval: null,
    refreshDelay: 5000,
    isLoading: false,
    sidebarCollapsed: false,
    theme: 'dark',
    
    init() {
        this.loadSettings();
        this.initSidebar();
        this.initTheme();
        this.startAutoRefresh();
        this.updateNavbarMetrics();
    },
    
    loadSettings() {
        const settings = JSON.parse(localStorage.getItem('pm_settings') || '{}');
        if (settings.refreshInterval) {
            this.refreshDelay = parseInt(settings.refreshInterval) * 1000;
        }
        if (settings.theme) {
            this.theme = settings.theme;
        }
    },
    
    initSidebar() {
        const sidebarCollapse = document.getElementById('sidebarCollapse');
        const sidebar = document.getElementById('sidebar');
        
        if (sidebarCollapse && sidebar) {
            sidebarCollapse.addEventListener('click', () => {
                this.sidebarCollapsed = !this.sidebarCollapsed;
                sidebar.classList.toggle('collapsed', this.sidebarCollapsed);
                localStorage.setItem('sidebar_collapsed', this.sidebarCollapsed);
            });
            
            // Restore state
            const saved = localStorage.getItem('sidebar_collapsed');
            if (saved === 'true') {
                this.sidebarCollapsed = true;
                sidebar.classList.add('collapsed');
            }
        }
    },
    
    initTheme() {
        // Check for theme from server-rendered HTML
        const htmlTheme = document.documentElement.getAttribute('data-theme');
        if (htmlTheme) {
            this.theme = htmlTheme;
        }
        
        // Apply theme to body
        document.body.className = `theme-${this.theme}`;
    },
    
    setTheme(theme) {
        this.theme = theme;
        document.documentElement.setAttribute('data-theme', theme);
        document.body.className = `theme-${theme}`;
        
        // Update charts if they exist
        if (typeof updateChartColors === 'function') {
            updateChartColors();
        }
    },
    
    startAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
        }
        this.refreshInterval = setInterval(() => {
            this.updateNavbarMetrics();
        }, this.refreshDelay);
    },
    
    async updateNavbarMetrics() {
        try {
            const response = await fetch('/api/system/metrics');
            if (!response.ok) return;
            
            const data = await response.json();
            
            // Update CPU
            const cpuEl = document.getElementById('cpu-indicator');
            if (cpuEl) {
                const cpuValue = cpuEl.querySelector('.value');
                if (cpuValue) cpuValue.textContent = `${Math.round(data.cpu_percent)}%`;
            }
            
            // Update Memory
            const memEl = document.getElementById('memory-indicator');
            if (memEl) {
                const memValue = memEl.querySelector('.value');
                if (memValue) memValue.textContent = `${Math.round(data.memory_percent)}%`;
            }
            
            // Update Uptime
            const uptimeEl = document.getElementById('uptime-display');
            if (uptimeEl && data.uptime_formatted) {
                uptimeEl.textContent = data.uptime_formatted;
            }
        } catch (err) {
            // Silently fail for navbar updates
        }
    },
    
    async api(url, options = {}) {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json'
            }
        };
        
        try {
            console.log(`[API] ${options.method || 'GET'} ${url}`);
            const response = await fetch(url, { ...defaultOptions, ...options });
            const data = await response.json();
            
            console.log(`[API] Response from ${url}:`, data);
            
            // Backend already returns {success, data} or {success, error}
            // So we return the raw response
            return data;
        } catch (error) {
            console.error(`[API] Error from ${url}:`, error);
            return { success: false, error: error.message };
        }
    },
    
    showToast(message, type = 'info') {
        const container = document.getElementById('toast-container');
        if (!container) return;
        
        // Check if notifications are enabled
        const settings = JSON.parse(localStorage.getItem('pm_settings') || '{}');
        if (settings.showNotifications === false) return;
        
        const toastId = 'toast-' + Date.now();
        
        const icons = {
            success: 'bi-check-circle-fill',
            error: 'bi-x-circle-fill',
            warning: 'bi-exclamation-triangle-fill',
            info: 'bi-info-circle-fill'
        };
        
        const bgColors = {
            success: 'bg-success',
            error: 'bg-danger',
            warning: 'bg-warning text-dark',
            info: 'bg-info text-dark'
        };
        
        const toast = document.createElement('div');
        toast.className = `toast align-items-center ${bgColors[type]} border-0 fade-in`;
        toast.id = toastId;
        toast.setAttribute('role', 'alert');
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    <i class="bi ${icons[type]} me-2"></i>${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;
        
        container.appendChild(toast);
        
        const bsToast = new bootstrap.Toast(toast, { delay: 4000 });
        bsToast.show();
        
        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });
    },
    
    formatDuration(seconds) {
        if (seconds < 60) return `${Math.floor(seconds)}s`;
        if (seconds < 3600) {
            const m = Math.floor(seconds / 60);
            const s = Math.floor(seconds % 60);
            return `${m}m ${s}s`;
        }
        if (seconds < 86400) {
            const h = Math.floor(seconds / 3600);
            const m = Math.floor((seconds % 3600) / 60);
            return `${h}h ${m}m`;
        }
        const d = Math.floor(seconds / 86400);
        const h = Math.floor((seconds % 86400) / 3600);
        return `${d}d ${h}h`;
    },
    
    getStatusBadge(status) {
        const badges = {
            running: '<span class="badge bg-success"><i class="bi bi-play-fill me-1"></i>Running</span>',
            stopped: '<span class="badge bg-secondary"><i class="bi bi-pause-fill me-1"></i>Stopped</span>',
            crashed: '<span class="badge bg-warning text-dark"><i class="bi bi-exclamation-triangle-fill me-1"></i>Crashed</span>',
            partial: '<span class="badge bg-info"><i class="bi bi-collection-fill me-1"></i>Partial</span>',
            unknown: '<span class="badge bg-danger"><i class="bi bi-question-circle-fill me-1"></i>Unknown</span>'
        };
        return badges[status] || badges.unknown;
    },
    
    getModeBadge(mode, projectId = null) {
        const isAuto = mode === 'auto';
        const toggleAttr = projectId ? `onclick="toggleProjectMode('${projectId}')"` : '';
        const cursorClass = projectId ? 'badge-mode-toggle' : '';
        
        if (isAuto) {
            return `<span class="badge bg-info text-dark ${cursorClass}" ${toggleAttr} title="Click to toggle mode">
                <i class="bi bi-lightning-fill me-1"></i>Auto
            </span>`;
        } else {
            return `<span class="badge bg-dark border ${cursorClass}" ${toggleAttr} title="Click to toggle mode">
                <i class="bi bi-hand-index-thumb me-1"></i>Manual
            </span>`;
        }
    }
};

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    App.init();
});

// Helper function for showing toast globally
function showToast(message, type) {
    App.showToast(message, type);
}

// Helper function for API calls globally
async function api(url, options) {
    return App.api(url, options);
}

// Helper function for toggling project mode globally
async function toggleProjectMode(projectId) {
    const result = await api(`/api/projects/${projectId}/toggle-mode`, {
        method: 'POST'
    });
    
    if (result.success) {
        showToast(`Mode changed to ${result.data.mode}`, 'success');
        // Reload projects to update UI
        if (typeof loadProjects === 'function') {
            loadProjects();
        }
    } else {
        showToast(result.error || 'Failed to toggle mode', 'error');
    }
}
