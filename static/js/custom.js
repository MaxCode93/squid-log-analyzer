// Custom JavaScript for Squid Log Analyzer

// Wait for document to be ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('Squid Log Analyzer initialized');
    
    // Enable tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Enable popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            
            const targetId = this.getAttribute('href');
            const targetElement = document.querySelector(targetId);
            
            if (targetElement) {
                window.scrollTo({
                    top: targetElement.offsetTop - 70,
                    behavior: 'smooth'
                });
            }
        });
    });
    
    // Add dark mode toggle to navbar if it doesn't exist
    const navbar = document.querySelector('.navbar-nav');
    if (navbar && !document.getElementById('darkModeToggle')) {
        const darkModeItem = document.createElement('li');
        darkModeItem.className = 'nav-item';
        
        const darkModeLink = document.createElement('a');
        darkModeLink.className = 'nav-link';
        darkModeLink.href = '#';
        darkModeLink.id = 'darkModeToggle';
        
        const darkModeIcon = document.createElement('i');
        darkModeIcon.className = 'fas fa-moon';
        
        darkModeLink.appendChild(darkModeIcon);
        darkModeLink.appendChild(document.createTextNode(' Modo oscuro'));
        
        darkModeItem.appendChild(darkModeLink);
        navbar.appendChild(darkModeItem);
        
        // Add event listener to dark mode toggle
        document.getElementById('darkModeToggle').addEventListener('click', function(e) {
            e.preventDefault();
            document.body.classList.toggle('dark-mode');
            
            // Save preference
            const isDarkMode = document.body.classList.contains('dark-mode');
            localStorage.setItem('darkMode', isDarkMode);
            
            // Update icon
            const icon = this.querySelector('i');
            if (isDarkMode) {
                icon.classList.remove('fa-moon');
                icon.classList.add('fa-sun');
                this.innerHTML = this.innerHTML.replace('Modo oscuro', 'Modo claro');
            } else {
                icon.classList.remove('fa-sun');
                icon.classList.add('fa-moon');
                this.innerHTML = this.innerHTML.replace('Modo claro', 'Modo oscuro');
            }
        });
    }
    
    // Check for saved dark mode preference
    const savedDarkMode = localStorage.getItem('darkMode');
    if (savedDarkMode === 'true') {
        document.body.classList.add('dark-mode');
        const darkModeToggle = document.getElementById('darkModeToggle');
        if (darkModeToggle) {
            const icon = darkModeToggle.querySelector('i');
            icon.classList.remove('fa-moon');
            icon.classList.add('fa-sun');
            darkModeToggle.innerHTML = darkModeToggle.innerHTML.replace('Modo oscuro', 'Modo claro');
        }
    }
    
    // Add search functionality to all tables
    document.querySelectorAll('table').forEach(table => {
        if (!table.id) {
            table.id = 'table-' + Math.random().toString(36).substr(2, 9);
        }
        
        const tableId = table.id;
        const tableContainer = table.parentElement;
        
        // Create search input if it doesn't exist
        if (!tableContainer.querySelector('.table-search')) {
            const searchDiv = document.createElement('div');
            searchDiv.className = 'input-group mb-3 table-search';
            
            const searchIcon = document.createElement('span');
            searchIcon.className = 'input-group-text';
            searchIcon.innerHTML = '<i class="fas fa-search"></i>';
            
            const searchInput = document.createElement('input');
            searchInput.type = 'text';
            searchInput.className = 'form-control';
            searchInput.placeholder = 'Buscar...';
            searchInput.setAttribute('data-table', tableId);
            
            searchDiv.appendChild(searchIcon);
            searchDiv.appendChild(searchInput);
            
            tableContainer.insertBefore(searchDiv, table);
            
            // Add event listener
            searchInput.addEventListener('keyup', function() {
                const searchTerm = this.value.toLowerCase();
                const tableId = this.getAttribute('data-table');
                const table = document.getElementById(tableId);
                
                if (table) {
                    const rows = table.querySelectorAll('tbody tr');
                    
                    rows.forEach(row => {
                        const text = row.textContent.toLowerCase();
                        if (text.includes(searchTerm)) {
                            row.style.display = '';
                        } else {
                            row.style.display = 'none';
                        }
                    });
                }
            });
        }
    });
    
    // Add sorting functionality to tables
    document.querySelectorAll('table thead th').forEach(th => {
        th.style.cursor = 'pointer';
        th.addEventListener('click', function() {
            const table = this.closest('table');
            const index = Array.from(this.parentElement.children).indexOf(this);
            const rows = Array.from(table.querySelectorAll('tbody tr'));
            const direction = this.classList.contains('sort-asc') ? -1 : 1;
            
            // Clear sort classes
            table.querySelectorAll('thead th').forEach(el => {
                el.classList.remove('sort-asc', 'sort-desc');
            });
            
            // Add sort class
            this.classList.add(direction === 1 ? 'sort-asc' : 'sort-desc');
            
            // Sort rows
            rows.sort((a, b) => {
                const aValue = a.children[index].textContent.trim();
                const bValue = b.children[index].textContent.trim();
                
                // Check if values are numbers
                const aNum = parseFloat(aValue.replace(/[^\d.-]/g, ''));
                const bNum = parseFloat(bValue.replace(/[^\d.-]/g, ''));
                
                if (!isNaN(aNum) && !isNaN(bNum)) {
                    return direction * (aNum - bNum);
                }
                
                return direction * aValue.localeCompare(bValue);
            });
            
            // Reorder rows
            const tbody = table.querySelector('tbody');
            rows.forEach(row => tbody.appendChild(row));
        });
    });
    
    // Add export to CSV functionality
    document.querySelectorAll('table').forEach(table => {
        const tableContainer = table.parentElement;
        
        // Create export button if it doesn't exist
        if (!tableContainer.querySelector('.export-csv')) {
            const exportButton = document.createElement('button');
            exportButton.className = 'btn btn-sm btn-outline-secondary mb-3 export-csv';
            exportButton.innerHTML = '<i class="fas fa-download"></i> Exportar CSV';
            exportButton.setAttribute('data-table', table.id);
            
            tableContainer.insertBefore(exportButton, table);
            
            // Add event listener
            exportButton.addEventListener('click', function() {
                const tableId = this.getAttribute('data-table');
                const table = document.getElementById(tableId);
                
                if (table) {
                    exportTableToCSV(table, 'tabla_exportada.csv');
                }
            });
        }
    });
    
    // Function to export table to CSV
    function exportTableToCSV(table, filename) {
        const rows = table.querySelectorAll('tr');
        const csv = [];
        
        for (let i = 0; i < rows.length; i++) {
            const row = [], cols = rows[i].querySelectorAll('td, th');
            
            for (let j = 0; j < cols.length; j++) {
                // Get text content and escape quotes
                let data = cols[j].textContent.trim().replace(/"/g, '""');
                // Wrap with quotes if contains comma, newline or quotes
                if (data.includes(',') || data.includes('\n') || data.includes('"')) {
                    data = `"${data}"`;
                }
                row.push(data);
            }
            
            csv.push(row.join(','));
        }
        
        // Download CSV file
        const csvContent = csv.join('\n');
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        
        if (navigator.msSaveBlob) { // IE 10+
            navigator.msSaveBlob(blob, filename);
        } else {
            const link = document.createElement('a');
            if (link.download !== undefined) {
                const url = URL.createObjectURL(blob);
                link.setAttribute('href', url);
                link.setAttribute('download', filename);
                link.style.visibility = 'hidden';
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
            }
        }
    }
    
    // Add animation to cards when they come into view
    if ('IntersectionObserver' in window) {
        const observerOptions = {
            root: null,
            rootMargin: '0px',
            threshold: 0.1
        };
        
        const observer = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('fade-in');
                    observer.unobserve(entry.target);
                }
            });
        }, observerOptions);
        
        document.querySelectorAll('.card').forEach(card => {
            card.style.opacity = '0';
            card.style.transform = 'translateY(20px)';
            card.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
            observer.observe(card);
        });
    }
    
    // Add fade-in class to make elements visible
    document.addEventListener('animationend', function(e) {
        if (e.target.classList.contains('fade-in')) {
            e.target.style.opacity = '1';
            e.target.style.transform = 'translateY(0)';
        }
    });
    
    // Add print button to report
    const reportHeader = document.querySelector('.card-body');
    if (reportHeader && !document.getElementById('printReport')) {
        const printButton = document.createElement('button');
        printButton.className = 'btn btn-outline-secondary ms-2';
        printButton.id = 'printReport';
        printButton.innerHTML = '<i class="fas fa-print"></i> Imprimir';
        
        // Find the right place to insert the button
        const headerButtons = reportHeader.querySelector('.btn');
        if (headerButtons) {
            headerButtons.parentNode.appendChild(printButton);
        } else {
            reportHeader.appendChild(printButton);
        }
        
        // Add event listener
        printButton.addEventListener('click', function() {
            window.print();
        });
    }
});

