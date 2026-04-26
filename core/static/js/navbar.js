document.addEventListener("DOMContentLoaded", function () {
    const navbar = document.getElementById("siteNavbar");
    const toggle = document.getElementById("navMenuToggle");
    const drawer = document.getElementById("navDrawer");
    const navLinks = document.querySelectorAll("[data-nav-link]");

    if (!navbar || !toggle || !drawer) {
        return;
    }

    function closeNav() {
        navbar.classList.remove("nav-open");
        toggle.setAttribute("aria-expanded", "false");
    }

    function openNav() {
        navbar.classList.add("nav-open");
        toggle.setAttribute("aria-expanded", "true");
    }

    function isCompactLayout() {
        return window.innerWidth < 1024;
    }

    toggle.addEventListener("click", function () {
        if (navbar.classList.contains("nav-open")) {
            closeNav();
            return;
        }

        openNav();
    });

    // Close the drawer after navigation on tablet/mobile.
    navLinks.forEach(function (link) {
        link.addEventListener("click", function () {
            if (isCompactLayout()) {
                closeNav();
            }
        });
    });

    document.addEventListener("keydown", function (event) {
        if (event.key === "Escape") {
            closeNav();
        }
    });

    document.addEventListener("click", function (event) {
        if (!isCompactLayout()) {
            return;
        }

        if (!navbar.contains(event.target)) {
            closeNav();
        }
    });

    window.addEventListener("resize", function () {
        if (!isCompactLayout()) {
            closeNav();
        }
    });
});
