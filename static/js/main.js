// Main JavaScript file for Football Statistics App

document.addEventListener('DOMContentLoaded', function() {
    // Initialize components
    initYearSelector();
    initTableSorting();
    initPlayerSearch();
    initTooltips();
    initLoadingStates();
});

/**
 * Initialize year selector functionality
 */
function initYearSelector() {
    const yearSelect = document.getElementById('yearSelect');
    if (yearSelect) {
        yearSelect.addEventListener('change', function() {
            this.disabled = true;
            const main = document.querySelector('main');
            if (main) main.classList.add('loading');
            const currentUrl = new URL(window.location.href);
            currentUrl.searchParams.set('year', this.value);
            window.location.href = currentUrl.toString();
        });
    }
}

/**
 * Initialize table sorting functionality
 */
function initTableSorting() {
    const tableHeaders = document.querySelectorAll('th[data-sortable]');
    
    tableHeaders.forEach(header => {
        header.style.cursor = 'pointer';
        header.addEventListener('click', function() {
            const table = this.closest('table');
            const tbody = table.querySelector('tbody');
            const rows = Array.from(tbody.querySelectorAll('tr'));
            const columnIndex = Array.from(this.parentNode.children).indexOf(this);
            const isNumeric = this.dataset.type === 'number';
            const currentOrder = this.dataset.order || 'asc';
            const newOrder = currentOrder === 'asc' ? 'desc' : 'asc';
            
            // Clear other headers' sort indicators
            tableHeaders.forEach(h => {
                h.classList.remove('sorted-asc', 'sorted-desc');
                delete h.dataset.order;
            });
            
            // Set current header's sort indicator
            this.classList.add(`sorted-${newOrder}`);
            this.dataset.order = newOrder;
            
            // Sort rows
            rows.sort((a, b) => {
                const aValue = a.children[columnIndex].textContent.trim();
                const bValue = b.children[columnIndex].textContent.trim();
                
                let comparison = 0;
                if (isNumeric) {
                    const aNum = parseFloat(aValue) || 0;
                    const bNum = parseFloat(bValue) || 0;
                    comparison = aNum - bNum;
                } else {
                    comparison = aValue.localeCompare(bValue);
                }
                
                return newOrder === 'asc' ? comparison : -comparison;
            });
            
            // Reorder rows in DOM
            rows.forEach(row => tbody.appendChild(row));
        });
    });
}

/**
 * Initialize player search functionality
 */
function initPlayerSearch() {
    const playerInputs = document.querySelectorAll('input[name="player1"], input[name="player2"]');
    
    playerInputs.forEach(input => {
        // Add autocomplete functionality (basic implementation)
        input.addEventListener('input', debounce(function() {
            const query = this.value.trim();
            if (query.length > 2) {
                // In a real implementation, this would fetch suggestions from the API
                console.log(`Searching for player: ${query}`);
            }
        }, 300));
    });
    
    // Initialize year comparison shortcuts
    initYearComparisonShortcuts();
}

/**
 * Initialize year comparison shortcuts
 */
function initYearComparisonShortcuts() {
    const yearButtons = document.querySelectorAll('.btn[href*="compare_players"]');
    
    yearButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            // Add loading state to the clicked button
            showLoading(this);
            
            // Remove loading state after navigation
            setTimeout(() => {
                hideLoading(this);
            }, 1000);
        });
    });
    
    // Auto-focus on first empty player input
    const firstEmptyInput = document.querySelector('input[name="player1"][value=""], input[name="player2"][value=""]');
    if (firstEmptyInput) {
        firstEmptyInput.focus();
    }
}

/**
 * Initialize Bootstrap tooltips
 */
function initTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    const tooltipList = tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * Initialize loading states for buttons and forms
 */
function initLoadingStates() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        form.addEventListener('submit', function() {
            const submitBtn = this.querySelector('button[type="submit"]');
            if (submitBtn) {
                if (!submitBtn.dataset.originalHtml) {
                    submitBtn.dataset.originalHtml = submitBtn.innerHTML;
                }
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Loading...';
                
                setTimeout(() => {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = submitBtn.dataset.originalHtml || 'Submit';
                }, 5000);
            }
        });
    });
}

/**
 * Utility function to debounce function calls
 */
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

/**
 * Show loading spinner
 */
function showLoading(element) {
    if (element) {
        element.classList.add('loading');
        const spinner = document.createElement('div');
        spinner.className = 'spinner-border spinner-border-sm me-2';
        spinner.setAttribute('role', 'status');
        element.prepend(spinner);
    }
}

/**
 * Hide loading spinner
 */
function hideLoading(element) {
    if (element) {
        element.classList.remove('loading');
        const spinner = element.querySelector('.spinner-border');
        if (spinner) {
            spinner.remove();
        }
    }
}

/**
 * Format large numbers with commas
 */
function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

/**
 * Calculate percentage and format it
 */
function calculatePercentage(part, total) {
    if (total === 0) return '0.0';
    return ((part / total) * 100).toFixed(1);
}

/**
 * Update URL parameters without page reload
 */
function updateUrlParam(param, value) {
    const url = new URL(window.location);
    url.searchParams.set(param, value);
    window.history.replaceState({}, '', url);
}

/**
 * Handle API errors gracefully
 */
function handleApiError(error) {
    console.error('API Error:', error);
    
    // Show user-friendly error message
    const errorAlert = document.createElement('div');
    errorAlert.className = 'alert alert-danger alert-dismissible fade show';
    errorAlert.innerHTML = `
        <i class="fas fa-exclamation-triangle me-2"></i>
        <strong>Error:</strong> Failed to load data. Please try again later.
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // Insert error alert at the top of main content
    const mainContent = document.querySelector('main');
    if (mainContent) {
        mainContent.insertBefore(errorAlert, mainContent.firstChild);
    }
}

/**
 * Animate number counting up
 */
function animateValue(element, start, end, duration) {
    let startTimestamp = null;
    const step = (timestamp) => {
        if (!startTimestamp) startTimestamp = timestamp;
        const progress = Math.min((timestamp - startTimestamp) / duration, 1);
        element.textContent = Math.floor(progress * (end - start) + start);
        if (progress < 1) {
            window.requestAnimationFrame(step);
        }
    };
    window.requestAnimationFrame(step);
}

/**
 * Initialize smooth scrolling for anchor links
 */
function initSmoothScrolling() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

// Initialize smooth scrolling
initSmoothScrolling();

// Export functions for use in other scripts
window.FootballStats = {
    showLoading,
    hideLoading,
    formatNumber,
    calculatePercentage,
    updateUrlParam,
    handleApiError,
    animateValue
};
