document.addEventListener("DOMContentLoaded", function () {
    const toggleBtn = document.getElementById("dark-toggle");
    const body = document.body;

    // Load preference
    if (localStorage.getItem("dark-mode") === "enabled") {
        body.classList.add("dark-mode");
        toggleBtn.innerHTML = '<i class="fas fa-sun"></i>';
    }

    toggleBtn.addEventListener("click", function () {
        body.classList.toggle("dark-mode");

        if (body.classList.contains("dark-mode")) {
            localStorage.setItem("dark-mode", "enabled");
            toggleBtn.innerHTML = '<i class="fas fa-sun"></i>';
        } else {
            localStorage.setItem("dark-mode", "disabled");
            toggleBtn.innerHTML = '<i class="fas fa-moon"></i>';
        }
    });
});
// Dark Mode Toggle Functionality
function toggleDarkMode() {
    const body = document.body;
    const darkToggle = document.getElementById('dark-toggle');
    const icon = darkToggle.querySelector('i');
    const text = darkToggle.querySelector('span');
    
    body.classList.toggle('dark-mode');
    
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

// Check for saved dark mode preference
document.addEventListener('DOMContentLoaded', function() {
    const darkMode = localStorage.getItem('darkMode');
    const darkToggle = document.getElementById('dark-toggle');
    
    if (darkToggle) {
        const icon = darkToggle.querySelector('i');
        const text = darkToggle.querySelector('span');
        
        if (darkMode === 'enabled') {
            document.body.classList.add('dark-mode');
            icon.classList.remove('fa-moon');
            icon.classList.add('fa-sun');
            text.textContent = 'Light Mode';
        }
    }
});