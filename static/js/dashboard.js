/**
 * Dashboard Page JavaScript
 * Handles system monitoring charts and metrics
 */

let projectsChart = null;
let modeChart = null;
let overviewChart = null;
let cpuChart = null;
let memoryChart = null;

// Chart colors for both themes
const chartColors = {
    dark: {
        text: '#e9ecef',
        grid: '#373b3e',
        cpu: '#0d6efd',
        memory: '#198754',
        running: '#198754',
        stopped: '#6c757d',
        crashed: '#ffc107',
        auto: '#0dcaf0',
        manual: '#6c757d'
    },
    light: {
        text: '#212529',
        grid: '#dee2e6',
        cpu: '#0d6efd',
        memory: '#198754',
        running: '#198754',
        stopped: '#6c757d',
        crashed: '#ffc107',
        auto: '#0dcaf0',
        manual: '#6c757d'
    }
};

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initCharts();
    loadDashboardData();
    startAutoRefresh();
});

function getThemeColors() {
    const theme = document.documentElement.getAttribute('data-theme') || 'dark';
    return chartColors[theme];
}

function initCharts() {
    const colors = getThemeColors();
    
    // Projects Status Doughnut Chart
    const projectsCtx = document.getElementById('projectsChart');
    if (projectsCtx) {
        projectsChart = new Chart(projectsCtx, {
            type: 'doughnut',
            data: {
                labels: ['Running', 'Stopped', 'Crashed'],
                datasets: [{
                    data: [0, 0, 0],
                    backgroundColor: [colors.running, colors.stopped, colors.crashed],
                    borderWidth: 0,
                    hoverOffset: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '65%',
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: colors.text,
                            padding: 15,
                            font: { size: 11 },
                            usePointStyle: true
                        }
                    }
                }
            }
        });
    }
    
    // Mode Distribution Pie Chart
    const modeCtx = document.getElementById('modeChart');
    if (modeCtx) {
        modeChart = new Chart(modeCtx, {
            type: 'pie',
            data: {
                labels: ['Auto Mode', 'Manual Mode'],
                datasets: [{
                    data: [0, 0],
                    backgroundColor: [colors.auto, colors.manual],
                    borderWidth: 2,
                    borderColor: document.documentElement.getAttribute('data-theme') === 'light' ? '#fff' : '#212529'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: colors.text,
                            padding: 15,
                            font: { size: 11 },
                            usePointStyle: true
                        }
                    }
                }
            }
        });
    }
    
    // Overview Bar Chart
    const overviewCtx = document.getElementById('overviewChart');
    if (overviewCtx) {
        overviewChart = new Chart(overviewCtx, {
            type: 'bar',
            data: {
                labels: ['Total', 'Running', 'Stopped', 'Crashed', 'Auto', 'Manual'],
                datasets: [{
                    label: 'Projects',
                    data: [0, 0, 0, 0, 0, 0],
                    backgroundColor: [
                        '#0d6efd',  // Total - primary
                        colors.running,
                        colors.stopped,
                        colors.crashed,
                        colors.auto,
                        colors.manual
                    ],
                    borderRadius: 4,
                    borderSkipped: false
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            color: colors.text,
                            stepSize: 1
                        },
                        grid: {
                            color: colors.grid,
                            drawBorder: false
                        }
                    },
                    x: {
                        ticks: {
                            color: colors.text,
                            font: { size: 10 }
                        },
                        grid: {
                            display: false
                        }
                    }
                }
            }
        });
    }
    
    // CPU History Line Chart
    const cpuCtx = document.getElementById('cpuChart');
    if (cpuCtx) {
        cpuChart = new Chart(cpuCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'CPU %',
                    data: [],
                    borderColor: colors.cpu,
                    backgroundColor: colors.cpu + '20',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 0,
                    pointHoverRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    intersect: false,
                    mode: 'index'
                },
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        ticks: {
                            color: colors.text,
                            callback: function(value) {
                                return value + '%';
                            }
                        },
                        grid: {
                            color: colors.grid,
                            drawBorder: false
                        }
                    },
                    x: {
                        ticks: {
                            color: colors.text,
                            maxTicksLimit: 8,
                            font: { size: 10 }
                        },
                        grid: {
                            display: false
                        }
                    }
                }
            }
        });
    }
    
    // Memory History Line Chart
    const memoryCtx = document.getElementById('memoryChart');
    if (memoryCtx) {
        memoryChart = new Chart(memoryCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Memory %',
                    data: [],
                    borderColor: colors.memory,
                    backgroundColor: colors.memory + '20',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 0,
                    pointHoverRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    intersect: false,
                    mode: 'index'
                },
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        ticks: {
                            color: colors.text,
                            callback: function(value) {
                                return value + '%';
                            }
                        },
                        grid: {
                            color: colors.grid,
                            drawBorder: false
                        }
                    },
                    x: {
                        ticks: {
                            color: colors.text,
                            maxTicksLimit: 8,
                            font: { size: 10 }
                        },
                        grid: {
                            display: false
                        }
                    }
                }
            }
        });
    }
}

function updateChartColors() {
    const colors = getThemeColors();
    
    // Update all charts with new colors
    if (projectsChart) {
        projectsChart.options.plugins.legend.labels.color = colors.text;
        projectsChart.update();
    }
    
    if (modeChart) {
        modeChart.options.plugins.legend.labels.color = colors.text;
        modeChart.data.datasets[0].borderColor = document.documentElement.getAttribute('data-theme') === 'light' ? '#fff' : '#212529';
        modeChart.update();
    }
    
    if (overviewChart) {
        overviewChart.options.scales.x.ticks.color = colors.text;
        overviewChart.options.scales.y.ticks.color = colors.text;
        overviewChart.options.scales.y.grid.color = colors.grid;
        overviewChart.update();
    }
    
    if (cpuChart) {
        cpuChart.options.scales.x.ticks.color = colors.text;
        cpuChart.options.scales.y.ticks.color = colors.text;
        cpuChart.options.scales.y.grid.color = colors.grid;
        cpuChart.update();
    }
    
    if (memoryChart) {
        memoryChart.options.scales.x.ticks.color = colors.text;
        memoryChart.options.scales.y.ticks.color = colors.text;
        memoryChart.options.scales.y.grid.color = colors.grid;
        memoryChart.update();
    }
}

async function loadDashboardData() {
    try {
        // Load system summary
        const summaryResult = await api('/api/system/summary');
        if (summaryResult.success) {
            updateDashboard(summaryResult.data);
        }
    } catch (err) {
        console.error('Error loading dashboard data:', err);
    }
}

function updateDashboard(data) {
    const colors = getThemeColors();
    
    // Update project counts
    const projects = data.projects || {};
    document.getElementById('dash-total').textContent = projects.total || 0;
    document.getElementById('dash-running').textContent = projects.running || 0;
    document.getElementById('dash-stopped').textContent = projects.stopped || 0;
    document.getElementById('dash-crashed').textContent = projects.crashed || 0;
    document.getElementById('dash-auto').textContent = projects.auto || 0;
    document.getElementById('dash-manual').textContent = projects.manual || 0;
    
    // Update projects chart
    if (projectsChart) {
        projectsChart.data.datasets[0].data = [
            projects.running || 0,
            projects.stopped || 0,
            projects.crashed || 0
        ];
        projectsChart.update();
    }
    
    // Update mode chart
    if (modeChart) {
        modeChart.data.datasets[0].data = [
            projects.auto || 0,
            projects.manual || 0
        ];
        modeChart.update();
    }
    
    // Update overview chart
    if (overviewChart) {
        overviewChart.data.datasets[0].data = [
            projects.total || 0,
            projects.running || 0,
            projects.stopped || 0,
            projects.crashed || 0,
            projects.auto || 0,
            projects.manual || 0
        ];
        overviewChart.update();
    }
    
    // Update system metrics
    const sys = data.system || {};
    
    // CPU
    const cpuPercent = Math.round(sys.cpu_percent || 0);
    document.getElementById('cpu-value').textContent = `${cpuPercent}%`;
    document.getElementById('cpu-progress').style.width = `${cpuPercent}%`;
    document.getElementById('cpu-progress').className = `progress-bar ${getCpuColor(cpuPercent)}`;
    
    // Memory
    const memPercent = Math.round(sys.memory_percent || 0);
    document.getElementById('memory-value').textContent = `${memPercent}%`;
    document.getElementById('memory-detail').textContent = 
        `${sys.memory_used_gb || 0} / ${sys.memory_total_gb || 0} GB`;
    document.getElementById('memory-progress').style.width = `${memPercent}%`;
    
    // Disk
    const diskPercent = Math.round(sys.disk_percent || 0);
    document.getElementById('disk-value').textContent = `${diskPercent}%`;
    document.getElementById('disk-detail').textContent = 
        `${sys.disk_used_gb || 0} / ${sys.disk_total_gb || 0} GB`;
    document.getElementById('disk-progress').style.width = `${diskPercent}%`;
    
    // Uptime
    document.getElementById('uptime-value').textContent = sys.uptime_formatted || '--';
    
    // System info
    document.getElementById('sys-platform').textContent = sys.platform || '--';
    document.getElementById('sys-memory').textContent = 
        sys.memory_total_gb ? `${sys.memory_total_gb} GB` : '--';
    document.getElementById('sys-disk').textContent = 
        sys.disk_total_gb ? `${sys.disk_total_gb} GB` : '--';
    
    // Update history charts
    const history = data.history || {};
    if (cpuChart && history.timestamps) {
        cpuChart.data.labels = history.timestamps;
        cpuChart.data.datasets[0].data = history.cpu || [];
        cpuChart.update('none'); // Update without animation
    }
    
    if (memoryChart && history.timestamps) {
        memoryChart.data.labels = history.timestamps;
        memoryChart.data.datasets[0].data = history.memory || [];
        memoryChart.update('none');
    }
    
    // Load running processes
    loadRunningProcesses();
}

function getCpuColor(percent) {
    if (percent < 50) return 'bg-success';
    if (percent < 80) return 'bg-warning';
    return 'bg-danger';
}

async function loadRunningProcesses() {
    const tbody = document.getElementById('processes-table-body');
    if (!tbody) return;
    
    try {
        const result = await api('/api/projects');
        if (!result.success) return;
        
        // Flatten all running services
        const runningServices = [];
        result.data.forEach(project => {
            if (project.services) {
                project.services.forEach(service => {
                    if (service.status === 'running') {
                        runningServices.push({
                            projectName: project.name,
                            serviceName: service.name,
                            pid: service.pid,
                            status: service.status,
                            uptime: service.uptime
                        });
                    }
                });
            }
        });
        
        document.getElementById('process-count').textContent = 
            `${runningServices.length} service${runningServices.length !== 1 ? 's' : ''}`;
        
        if (runningServices.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="7" class="text-center text-muted py-4">
                        <i class="bi bi-inbox fs-4 d-block mb-2"></i>
                        No running services
                    </td>
                </tr>
            `;
            return;
        }
        
        tbody.innerHTML = runningServices.map(service => `
            <tr>
                <td>
                    <strong>${escapeHtml(service.projectName)}</strong>
                </td>
                <td>${escapeHtml(service.serviceName)}</td>
                <td><code>${service.pid || '--'}</code></td>
                <td>${App.getStatusBadge(service.status)}</td>
                <td>${service.uptime || '--'}</td>
                <td>--</td>
                <td>--</td>
            </tr>
        `).join('');
        
        // Load detailed process info for each
        for (const service of runningServices) {
            if (service.pid) {
                loadProcessDetails(service.pid);
            }
        }
    } catch (err) {
        console.error('Error loading processes:', err);
    }
}

async function loadProcessDetails(pid) {
    try {
        // Find all rows with this PID and update them
        const rows = document.querySelectorAll('#processes-table-body tr');
        rows.forEach(row => {
            const pidCell = row.querySelector('td:nth-child(3) code');
            if (pidCell && pidCell.textContent === String(pid)) {
                // In a real implementation, you'd fetch process details
                // For now, we'll leave the CPU/Memory as --
            }
        });
    } catch (err) {
        // Silently fail
    }
}

function startAutoRefresh() {
    const settings = JSON.parse(localStorage.getItem('pm_settings') || '{}');
    const interval = (settings.refreshInterval || 5) * 1000;
    
    setInterval(() => {
        loadDashboardData();
    }, interval);
}

// Utility functions
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

// Export for theme updates
window.updateChartColors = updateChartColors;
