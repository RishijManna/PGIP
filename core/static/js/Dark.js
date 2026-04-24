(function () {
    const STORAGE_KEYS = ["darkMode", "dark-mode"];

    function readSavedTheme() {
        try {
            return (
                localStorage.getItem(STORAGE_KEYS[0]) ||
                localStorage.getItem(STORAGE_KEYS[1])
            );
        } catch (error) {
            return null;
        }
    }

    function saveTheme(isDarkMode) {
        try {
            const value = isDarkMode ? "enabled" : "disabled";
            STORAGE_KEYS.forEach((key) => localStorage.setItem(key, value));
        } catch (error) {
            // Theme should still toggle even when browser storage is blocked.
        }
    }

    function setButtonState(isDarkMode) {
        const button = document.getElementById("dark-toggle");
        if (!button) return;

        const icon = button.querySelector("i");
        const label = button.querySelector("span");

        if (icon) {
            icon.classList.remove(isDarkMode ? "fa-moon" : "fa-sun");
            icon.classList.add(isDarkMode ? "fa-sun" : "fa-moon");
        }

        if (label) {
            label.textContent = isDarkMode ? "Light Mode" : "Dark Mode";
        }

        button.setAttribute("aria-pressed", String(isDarkMode));
        button.setAttribute(
            "aria-label",
            isDarkMode ? "Switch to light mode" : "Switch to dark mode"
        );
    }

    function applyTheme(isDarkMode, persist) {
        document.body.classList.toggle("dark-mode", isDarkMode);
        document.documentElement.classList.toggle("dark-mode", isDarkMode);
        document.documentElement.setAttribute(
            "data-theme",
            isDarkMode ? "dark" : "light"
        );
        setButtonState(isDarkMode);

        if (persist) {
            saveTheme(isDarkMode);
        }
    }

    function toggleDarkMode(event) {
        if (event) {
            event.preventDefault();
            event.stopPropagation();
        }

        const isDarkMode = !document.body.classList.contains("dark-mode");
        applyTheme(isDarkMode, true);
    }

    function initializeDarkMode() {
        const savedTheme = readSavedTheme();
        applyTheme(savedTheme === "enabled", false);

        const button = document.getElementById("dark-toggle");
        if (!button) return;

        button.removeEventListener("click", toggleDarkMode);
        button.addEventListener("click", toggleDarkMode);
    }

    window.toggleDarkMode = toggleDarkMode;

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initializeDarkMode, {
            once: true,
        });
    } else {
        initializeDarkMode();
    }
})();
