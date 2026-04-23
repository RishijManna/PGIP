// FINAL Dark Mode Toggle

function toggleDarkMode() {
    const body = document.body;
    const toggleBtn = document.getElementById("dark-toggle");

    if (!toggleBtn) return;

    const icon = toggleBtn.querySelector("i");
    const text = toggleBtn.querySelector("span");

    // Toggle class
    body.classList.toggle("dark-mode");

    // Save preference
    if (body.classList.contains("dark-mode")) {
        localStorage.setItem("darkMode", "enabled");

        icon.classList.remove("fa-moon");
        icon.classList.add("fa-sun");
        text.textContent = "Light Mode";
    } else {
        localStorage.setItem("darkMode", "disabled");

        icon.classList.remove("fa-sun");
        icon.classList.add("fa-moon");
        text.textContent = "Dark Mode";
    }
}


// Load saved preference safely

document.addEventListener("DOMContentLoaded", function () {
    const saved = localStorage.getItem("darkMode");

    const toggleBtn = document.getElementById("dark-toggle");

    if (!toggleBtn) return;

    const icon = toggleBtn.querySelector("i");
    const text = toggleBtn.querySelector("span");

    if (saved === "enabled") {
        document.body.classList.add("dark-mode");

        icon.classList.remove("fa-moon");
        icon.classList.add("fa-sun");
        text.textContent = "Light Mode";
    }
});