// Main JavaScript for Kindergarten Management System

// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Auto close flash messages after 5 seconds
    setTimeout(function() {
        let alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            let bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);

    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    });

    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'))
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl)
    });

    // Confirm deletion for any delete button
    document.querySelectorAll('.btn-delete').forEach(function(button) {
        button.addEventListener('click', function(e) {
            if (!confirm('Haqiqatan ham o\'chirishni xohlaysizmi?')) {
                e.preventDefault();
            }
        });
    });

    // Auto-scroll to bottom of message container if present
    const messageContainer = document.querySelector('.message-container');
    if (messageContainer) {
        messageContainer.scrollTop = messageContainer.scrollHeight;
    }

    // Toggle password visibility
    const togglePasswordButtons = document.querySelectorAll('.toggle-password');
    if (togglePasswordButtons) {
        togglePasswordButtons.forEach(function(button) {
            button.addEventListener('click', function() {
                const passwordField = document.querySelector(this.getAttribute('data-target'));
                const type = passwordField.getAttribute('type') === 'password' ? 'text' : 'password';
                passwordField.setAttribute('type', type);
                
                // Toggle icon
                this.querySelector('i').classList.toggle('fa-eye');
                this.querySelector('i').classList.toggle('fa-eye-slash');
            });
        });
    }

    // Handle date picker elements
    const dateInputs = document.querySelectorAll('input[type="date"]');
    if (dateInputs) {
        const today = new Date().toISOString().split('T')[0];
        
        dateInputs.forEach(function(input) {
            // If no value is set and it has a data-default-today attribute, set to today
            if (input.hasAttribute('data-default-today') && !input.value) {
                input.value = today;
            }
        });
    }

    // Handle file input display
    const fileInputs = document.querySelectorAll('input[type="file"]');
    if (fileInputs) {
        fileInputs.forEach(function(input) {
            input.addEventListener('change', function() {
                const fileName = this.files[0] ? this.files[0].name : 'Fayl tanlanmagan';
                const fileLabel = document.querySelector(`label[for="${this.id}"] .file-name`);
                
                if (fileLabel) {
                    fileLabel.textContent = fileName;
                }
            });
        });
    }

    // Handle attendance form submission
    const attendanceForm = document.getElementById('attendance-form');
    if (attendanceForm) {
        attendanceForm.addEventListener('submit', function(e) {
            const statuses = document.querySelectorAll('select[name^="status_"]');
            let hasSelection = false;
            
            statuses.forEach(function(select) {
                if (select.value) {
                    hasSelection = true;
                }
            });
            
            if (!hasSelection) {
                e.preventDefault();
                alert('Iltimos, kamida bitta bola uchun davomat holatini tanlang!');
            }
        });
    }

    // Auto-resize textareas
    const autoResizeTextareas = document.querySelectorAll('textarea[data-autoresize]');
    if (autoResizeTextareas) {
        autoResizeTextareas.forEach(function(textarea) {
            textarea.style.height = 'auto';
            textarea.style.height = textarea.scrollHeight + 'px';
            
            textarea.addEventListener('input', function() {
                this.style.height = 'auto';
                this.style.height = this.scrollHeight + 'px';
            });
        });
    }

    // Initialize any custom dropdowns
    const dropdownSelects = document.querySelectorAll('.dropdown-select');
    if (dropdownSelects) {
        dropdownSelects.forEach(function(dropdown) {
            dropdown.addEventListener('change', function() {
                if (this.value) {
                    window.location.href = this.value;
                }
            });
        });
    }
});

// Function to update real-time clock in dashboard
function updateClock() {
    const clockElement = document.getElementById('current-time');
    if (clockElement) {
        const now = new Date();
        const timeString = now.toLocaleTimeString('uz-UZ');
        clockElement.textContent = timeString;
        setTimeout(updateClock, 1000);
    }
}

// Start the clock if the element exists
if (document.getElementById('current-time')) {
    updateClock();
}