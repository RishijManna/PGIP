document.addEventListener('DOMContentLoaded', function () {
    const defaultCalendarEl = document.getElementById('defaultCalendar');
    const userCalendarEl = document.getElementById('userCalendar');
    const calendarWrapper = document.getElementById('calendarWrapper');
    const navButtons = document.querySelectorAll('.calendar-nav-btn');
    
    if (!defaultCalendarEl || !userCalendarEl) {
        console.error('Calendar elements not found');
        return;
    }
    
    let currentEvent = null;
    let currentView = 'default'; // 'default' or 'user'
    let touchStartX = 0;
    let touchEndX = 0;
    let mouseStartX = 0;
    let mouseEndX = 0;
    let isDragging = false;

    // --- helper to avoid triggering swipe on toolbar/buttons ---
    function isInteractiveTarget(el) {
        return el.closest('.fc-toolbar, .fc-button, .fc-button-group, .btn, button, a, input, select, textarea, .fc-event');
    }

    // Swipe detection for mobile
    calendarWrapper.addEventListener('touchstart', function(e) {
        if (isInteractiveTarget(e.target)) return;
        touchStartX = e.changedTouches[0].screenX;
    }, false);

    calendarWrapper.addEventListener('touchend', function(e) {
        if (isInteractiveTarget(e.target)) return;
        touchEndX = e.changedTouches[0].screenX;
        handleSwipe();
    }, false);

    // Mouse drag detection for desktop
    calendarWrapper.addEventListener('mousedown', function(e) {
        if (isInteractiveTarget(e.target)) return;
        isDragging = true;
        mouseStartX = e.clientX;
        mouseEndX = mouseStartX; // important fix
        calendarWrapper.classList.add('swiping');
    });

    calendarWrapper.addEventListener('mousemove', function(e) {
        if (!isDragging) return;
        mouseEndX = e.clientX;
    });

    calendarWrapper.addEventListener('mouseup', function(e) {
        if (!isDragging) return;
        calendarWrapper.classList.remove('swiping');
        isDragging = false;
        handleMouseSwipe();
    });

    calendarWrapper.addEventListener('mouseleave', function() {
        if (!isDragging) return;
        calendarWrapper.classList.remove('swiping');
        isDragging = false;
        handleMouseSwipe();
    });

    function handleSwipe() {
        const swipeThreshold = 50;
        const delta = touchEndX - touchStartX;

        if (Math.abs(delta) < swipeThreshold) return;

        if (delta < 0 && currentView === 'default') {
            switchCalendar('user');
        }
        if (delta > 0 && currentView === 'user') {
            switchCalendar('default');
        }
    }
    
    function handleMouseSwipe() {
        const swipeThreshold = 100;
        const delta = mouseEndX - mouseStartX;

        if (Math.abs(delta) < swipeThreshold) {
            mouseStartX = 0;
            mouseEndX = 0;
            return;
        }

        if (delta < 0 && currentView === 'default') {
            switchCalendar('user');
        } else if (delta > 0 && currentView === 'user') {
            switchCalendar('default');
        }

        mouseStartX = 0;
        mouseEndX = 0;
    }

    // Navigation button click handlers
    navButtons.forEach(button => {
        button.addEventListener('click', function() {
            const target = this.getAttribute('data-target');
            switchCalendar(target);
        });
    });

    function switchCalendar(target) {
        if (target === currentView) return;
        
        navButtons.forEach(btn => {
            if (btn.getAttribute('data-target') === target) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        });
        
        if (target === 'default') {
            calendarWrapper.style.transform = 'translateX(0)';
        } else {
            calendarWrapper.style.transform = 'translateX(-50%)';
        }
        
        currentView = target;
        
        if (target === 'default') {
            defaultCalendar.render();
        } else {
            userCalendar.render();
        }
    }

    // Function to format event details for display
    function formatEventDetails(event) {
        let details = `<p><strong>Title:</strong> ${event.title}</p>`;
        
        if (event.extendedProps) {
            if (event.extendedProps.exam_type) {
                details += `<p><strong>Type:</strong> ${event.extendedProps.exam_type}</p>`;
            }
            if (event.extendedProps.category) {
                details += `<p><strong>Category:</strong> ${event.extendedProps.category}</p>`;
            }
            if (event.extendedProps.location) {
                details += `<p><strong>Location:</strong> ${event.extendedProps.location}</p>`;
            }
            if (event.extendedProps.mode) {
                details += `<p><strong>Mode:</strong> ${event.extendedProps.mode}</p>`;
            }
            if (event.extendedProps.e_eligibility || event.extendedProps.s_eligibility) {
                const eligibility = event.extendedProps.e_eligibility || event.extendedProps.s_eligibility;
                details += `<p><strong>Eligibility:</strong> ${eligibility}</p>`;
            }
            if (event.extendedProps.description) {
                details += `<p><strong>Description:</strong> ${event.extendedProps.description}</p>`;
            }
            if (event.extendedProps.benefits) {
                details += `<p><strong>Benefits:</strong> ${event.extendedProps.benefits}</p>`;
            }
            if (event.extendedProps.benefit_amount) {
                details += `<p><strong>Benefit amount:</strong> ${event.extendedProps.benefit_amount}</p>`;
            }
            if (event.extendedProps.application_fee) {
                details += `<p><strong>Registration fee:</strong> ${event.extendedProps.application_fee}</p>`;
            }
            if (event.extendedProps.salary_package) {
                details += `<p><strong>Salary / package:</strong> ${event.extendedProps.salary_package}</p>`;
            }
            if (event.extendedProps.required_documents) {
                details += `<p><strong>Required documents:</strong> ${event.extendedProps.required_documents}</p>`;
            }
            if (event.extendedProps.compensation) {
                details += `<p><strong>Compensation:</strong> ${event.extendedProps.compensation}</p>`;
            }
            if (event.extendedProps.registration_window) {
                details += `<p><strong>Registration:</strong> ${event.extendedProps.registration_window}</p>`;
            }
            if (event.extendedProps.source_name) {
                details += `<p><strong>Source:</strong> ${event.extendedProps.source_name}</p>`;
            }
        }
        
        details += `<p><strong>Date:</strong> ${event.startStr}</p>`;
        
        return details;
    }

    // Default Calendar (Exams & Schemes)
   var defaultCalendar = new FullCalendar.Calendar(document.getElementById('defaultCalendar'), {
    initialView: 'dayGridMonth',
    headerToolbar: {
        left: 'prev,next today',
        center: 'title',
        right: 'dayGridMonth'
    },
        events: function(fetchInfo, successCallback, failureCallback) {
            fetch('/api/events/')
                .then(response => {
                    if (!response.ok) throw new Error('Network response was not ok');
                    return response.json();
                })
                .then(data => {
                    const defaultEvents = data.filter(event => !event.id.startsWith('task-'));
                    defaultEvents.forEach(event => {
                        if (event.id && event.id.startsWith('exam-')) {
                            event.className = 'exam-event';
                        } else if (event.id && event.id.startsWith('scheme-')) {
                            event.className = 'scheme-event';
                        } else if (event.id && event.id.startsWith('job-')) {
                            event.className = 'job-event';
                        }
                    });
                    successCallback(defaultEvents);
                })
                .catch(error => {
                    console.error('Error fetching events:', error);
                    const mockExamData = [
                        { 
                            id: 'exam-1', 
                            title: 'JEE Main', 
                            start: '2025-01-06',
                            extendedProps: {
                                exam_type: 'Government',
                                category: 'Engineering',
                                location: 'All India',
                                mode: 'Online',
                                e_eligibility: '12th Pass'
                            }
                        },
                        { 
                            id: 'exam-2', 
                            title: 'NEET', 
                            start: '2025-05-07',
                            extendedProps: {
                                exam_type: 'Government',
                                category: 'Medical',
                                location: 'All India',
                                mode: 'Offline',
                                e_eligibility: '12th Pass'
                            }
                        },
                        { 
                            id: 'scheme-1', 
                            title: 'Central Scholarship Scheme', 
                            start: '2025-04-05',
                            extendedProps: {
                                category: 'Education',
                                scheme_type: 'Scholarship',
                                location: 'All India',
                                s_eligibility: '12th Pass',
                                description: 'Scholarship for meritorious students.',
                                benefits: 'Covers tuition fees and stipend.'
                            }
                        }
                    ];
                    mockExamData.forEach(event => {
                        if (event.id.startsWith('exam-')) {
                            event.className = 'exam-event';
                        } else if (event.id.startsWith('scheme-')) {
                            event.className = 'scheme-event';
                        }
                    });
                    successCallback(mockExamData);
                });
        },
        eventClick: function (info) {
            info.jsEvent.preventDefault();
            const event = info.event;
            document.getElementById('eventModalTitle').textContent = event.title;
            document.getElementById('eventModalBody').innerHTML = formatEventDetails(event);
            const modalElement = document.getElementById('eventDetailsModal');
            if (modalElement) {
                const modal = new bootstrap.Modal(modalElement);
                modal.show();
            }
        }
    });

    // User Calendar (Reminders)
   var userCalendar = new FullCalendar.Calendar(document.getElementById('userCalendar'), {
    initialView: 'dayGridMonth',
    headerToolbar: {
        left: 'prev,next today',
        center: 'title',
        right: 'dayGridMonth'
    },
        events: function(fetchInfo, successCallback, failureCallback) {
            fetch('/api/events/')
                .then(response => {
                    if (!response.ok) throw new Error('Network response was not ok');
                    return response.json();
                })
                .then(data => {
                    const userEvents = data.filter(event => event.id.startsWith('task-'));
                    userEvents.forEach(event => {
                        event.className = 'reminder-event';
                    });
                    successCallback(userEvents);
                })
                .catch(error => {
                    console.error('Error fetching events:', error);
                    const mockReminderData = [
                        { 
                            id: 'task-1', 
                            title: 'Study for Math', 
                            start: new Date().toISOString().split('T')[0],
                            className: 'reminder-event'
                        },
                        { 
                            id: 'task-2', 
                            title: 'Submit Application', 
                            start: '2025-02-15',
                            className: 'reminder-event'
                        }
                    ];
                    successCallback(mockReminderData);
                });
        },
        dateClick: function (info) {
            const dateInput = document.getElementById('reminderDate');
            const titleInput = document.getElementById('reminderTitle');
            if (dateInput && titleInput) {
                dateInput.value = info.dateStr;
                titleInput.value = '';
                const modalElement = document.getElementById('reminderModal');
                if (modalElement) {
                    const modal = new bootstrap.Modal(modalElement);
                    modal.show();
                }
            }
        },
        eventClick: function (info) {
            info.jsEvent.preventDefault();
            const event = info.event;
            currentEvent = event;
            if (event.id && event.id.startsWith('task-')) {
                const detailsElement = document.getElementById('reminderDetails');
                const idInput = document.getElementById('deleteReminderId');
                if (detailsElement && idInput) {
                    detailsElement.innerHTML = 
                        `<strong>Title:</strong> ${event.title}<br>
                         <strong>Date:</strong> ${event.startStr}`;
                    idInput.value = event.id;
                    const modalElement = document.getElementById('viewReminderModal');
                    if (modalElement) {
                        const modal = new bootstrap.Modal(modalElement);
                        modal.show();
                    }
                }
            }
        }
    });

    defaultCalendar.render();
    userCalendar.render();

    // Add reminder form
    const reminderForm = document.getElementById('reminderForm');
    if (reminderForm) {
        reminderForm.addEventListener('submit', function (e) {
            e.preventDefault();
            const titleInput = document.getElementById('reminderTitle');
            const dateInput = document.getElementById('reminderDate');
            if (!titleInput || !dateInput) return;
            const title = titleInput.value;
            const date = dateInput.value;
            if (!title.trim()) {
                alert('Please enter a title for your reminder');
                return;
            }
            fetch('/add-reminder/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({ title, date })
            })
            .then(res => {
                if (!res.ok) throw new Error('Network response was not ok');
                return res.json();
            })
            .then(data => {
                if (data.status === 'success') {
                    userCalendar.refetchEvents();
                    const modalElement = document.getElementById('reminderModal');
                    if (modalElement) {
                        const modal = bootstrap.Modal.getInstance(modalElement);
                        if (modal) modal.hide();
                    }
                    showToast('Reminder added successfully!', 'success');
                } else if (data.status === 'duplicate') {
                    alert('This reminder already exists!');
                } else {
                    alert('Error: ' + (data.message || 'Unknown error occurred'));
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error adding reminder. Please try again.');
            });
        });
    }

    // Delete reminder
    const deleteButton = document.getElementById('confirmDeleteBtn');
    if (deleteButton) {
        deleteButton.addEventListener('click', function() {
            deleteCurrentReminder();
        });
    }

    function deleteCurrentReminder() {
        if (!currentEvent) {
            alert('No reminder selected');
            return;
        }
        const reminderId = currentEvent.id;
        if (!reminderId || !reminderId.startsWith('task-')) {
            alert('Cannot delete this event type');
            return;
        }
        const actualId = reminderId.replace('task-', '');
        fetch(`/delete-reminder/${actualId}/`, {
            method: 'DELETE',
            headers: { 'X-CSRFToken': getCookie('csrftoken') }
        })
        .then(res => {
            if (res.status === 401) throw new Error('Unauthorized');
            if (res.status === 404) throw new Error('Reminder not found');
            if (!res.ok) throw new Error('Network response was not ok');
            return res.json();
        })
        .then(data => {
            if (data.status === 'success' || data.success) {
                userCalendar.refetchEvents();
                const modalElement = document.getElementById('viewReminderModal');
                if (modalElement) {
                    const modal = bootstrap.Modal.getInstance(modalElement);
                    if (modal) modal.hide();
                }
                showToast('Reminder deleted successfully!', 'success');
                currentEvent = null;
            } else {
                throw new Error(data.message || 'Unknown error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error deleting reminder: ' + error.message);
        });
    }

    // Helpers
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.startsWith(name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    function showToast(message, type = 'info') {
        let toastContainer = document.getElementById('toastContainer');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.id = 'toastContainer';
            toastContainer.style.position = 'fixed';
            toastContainer.style.top = '20px';
            toastContainer.style.right = '20px';
            toastContainer.style.zIndex = '9999';
            document.body.appendChild(toastContainer);
        }
        const toast = document.createElement('div');
        toast.className = `alert alert-${type} alert-dismissible fade show`;
        toast.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        toastContainer.appendChild(toast);
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 3000);
    }
});
