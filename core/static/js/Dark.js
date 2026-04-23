// Dark Mode Toggle Functionality

function toggleDarkMode() {
    const body = document.body;
    const darkToggle = document.getElementById('dark-toggle');

    if (!darkToggle) return;

    const icon = darkToggle.querySelector('i');
    const text = darkToggle.querySelector('span');

    // Toggle class
    body.classList.toggle('dark-mode');

    // Update UI + save preference
    if (body.classList.contains('dark-mode')) {
        icon.classList.remove('fa-moon');
        icon.classList.add('fa-sun');
        text.textContent = 'Light Mode';
        localStorage.setItem('darkMode', 'enabled');
    } else {
        icon.classList.remove('fa-sun');
        icon.classList.add('fa-moon');
        text.textContent = 'Dark Mode';
        localStorage.setItem('darkMode', 'disabled');
    }
}


// Load saved preference on page load

document.addEventListener('DOMContentLoaded', function () {

    const darkMode = localStorage.getItem('darkMode');
    const darkToggle = document.getElementById('dark-toggle');

    if (!darkToggle) return;

    const icon = darkToggle.querySelector('i');
    const text = darkToggle.querySelector('span');

    if (darkMode === 'enabled') {
        document.body.classList.add('dark-mode');

        icon.classList.remove('fa-moon');
        icon.classList.add('fa-sun');
        text.textContent = 'Light Mode';
    }

});