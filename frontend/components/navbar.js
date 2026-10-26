/**
 * GallScan AI — Shared Navbar & Disclaimer Component
 * Adapts dynamically based on authentication state:
 * - Unauthenticated: Clean landing header (Brand logo + Sign In / Get Started only, NO nav links).
 * - Authenticated: Console navigation (Upload Scan, Archives, Alerts, Profile, Logout, NO Home button).
 */

(function () {
  function getActiveRoute() {
    const path = window.location.pathname.toLowerCase();
    if (path.endsWith("upload.html")) return "upload";
    if (path.endsWith("history.html")) return "history";
    if (path.endsWith("notifications.html")) return "notifications";
    if (path.endsWith("profile.html")) return "profile";
    if (path.endsWith("result.html")) return "result";
    if (path.endsWith("login.html") || path.endsWith("signup.html") || path.endsWith("forgot-password.html")) return "auth";
    return "home";
  }

  function isAuthenticated() {
    try {
      const token = localStorage.getItem("gallscan_token");
      const user = localStorage.getItem("gallscan_user");
      return !!(token && user);
    } catch {
      return false;
    }
  }

  function renderSharedHeader() {
    const activeRoute = getActiveRoute();
    const authenticated = isAuthenticated();

    // 1. Mandatory Clinical Disclaimer Banner
    const disclaimerRoot = document.getElementById("disclaimer-root");
    if (disclaimerRoot) {
      disclaimerRoot.innerHTML = `
        <div class="disclaimer-banner">
          <div class="disclaimer-inner">
            <span class="disclaimer-badge">Research & Academic Use Only</span>
            <span><strong>Important Medical Disclaimer:</strong> GallScan AI is an investigational deep learning platform for educational and research exploration. It is not an FDA/CE-cleared diagnostic device and must not replace professional radiological evaluation.</span>
          </div>
        </div>
      `;
    }

    // 2. Main Application Header
    const navbarRoot = document.getElementById("navbar-root");
    if (navbarRoot) {
      const brandHref = authenticated ? "upload.html" : "index.html";

      if (authenticated) {
        // AUTHENTICATED USER HEADER: Upload, Archives, Alerts (No Home button)
        navbarRoot.innerHTML = `
          <header class="app-header">
            <div class="header-inner">
              <a href="${brandHref}" class="brand-group">
                <div class="brand-icon">
                  <span class="material-symbols-outlined">radiology</span>
                </div>
                <div class="brand-text">
                  <span class="brand-title">GallScan AI</span>
                  <span class="brand-badge">CLINICAL CONSOLE</span>
                </div>
              </a>

              <nav class="desktop-nav">
                <ul class="nav-links">
                  <li><a href="upload.html" class="nav-link ${activeRoute === 'upload' || activeRoute === 'result' ? 'active' : ''}"><span class="material-symbols-outlined">upload_file</span> Upload Scan</a></li>
                  <li><a href="history.html" class="nav-link ${activeRoute === 'history' ? 'active' : ''}"><span class="material-symbols-outlined">history</span> Archives</a></li>
                  <li><a href="notifications.html" class="nav-link ${activeRoute === 'notifications' ? 'active' : ''}"><span class="material-symbols-outlined">notifications</span> Alerts</a></li>
                </ul>
              </nav>

              <div class="header-actions">
                <!-- Mobile Hamburger Toggle -->
                <button class="icon-btn mobile-menu-btn" id="mobileMenuToggle" aria-label="Toggle Navigation Menu">
                  <span class="material-symbols-outlined" id="mobileMenuIcon">menu</span>
                </button>

                <!-- Notifications Popover -->
                <div class="notif-wrapper">
                  <button class="icon-btn" id="headerNotifBtn" title="Notifications" aria-label="View notifications">
                    <span class="material-symbols-outlined">notifications</span>
                    <span class="badge-dot" id="headerNotifBadge" style="display: none;"></span>
                  </button>
                  <div class="notif-popover" id="headerNotifPopover">
                    <div class="notif-header">
                      <span class="notif-title">Recent Activity</span>
                      <a href="notifications.html" style="font-size: 11px; color: var(--secondary-teal); font-weight: 600; text-decoration: none;">View All</a>
                    </div>
                    <ul class="notif-list" id="headerNotifList">
                      <li style="padding: 16px; text-align: center; color: var(--text-light); font-size: 12px;">Loading alerts...</li>
                    </ul>
                    <div class="notif-footer">
                      <a href="notifications.html">Open Notification Center &rarr;</a>
                    </div>
                  </div>
                </div>

                <!-- Authenticated Profile Menu -->
                <div id="headerUserSection" style="display: flex; align-items: center; gap: 8px;">
                  <a href="profile.html" class="user-menu-btn ${activeRoute === 'profile' ? 'active' : ''}">
                    <div class="user-avatar-initial" id="headerUserAvatar">C</div>
                    <span id="headerUserName">Clinician</span>
                  </a>
                  <button class="btn btn-outline btn-sm btn-logout" title="Sign Out" aria-label="Sign out">
                    <span class="material-symbols-outlined">logout</span>
                  </button>
                </div>
              </div>
            </div>

            <!-- Mobile Dropdown Drawer for Authenticated Users -->
            <div class="mobile-drawer" id="mobileDrawer" style="display: none;">
              <div class="mobile-drawer-inner">
                <a href="upload.html" class="mobile-nav-link ${activeRoute === 'upload' || activeRoute === 'result' ? 'active' : ''}">
                  <span class="material-symbols-outlined">upload_file</span> Upload Scan
                </a>
                <a href="history.html" class="mobile-nav-link ${activeRoute === 'history' ? 'active' : ''}">
                  <span class="material-symbols-outlined">history</span> Scan Archives
                </a>
                <a href="notifications.html" class="mobile-nav-link ${activeRoute === 'notifications' ? 'active' : ''}">
                  <span class="material-symbols-outlined">notifications</span> Alerts & Notifications
                </a>
                <a href="profile.html" class="mobile-nav-link ${activeRoute === 'profile' ? 'active' : ''}">
                  <span class="material-symbols-outlined">account_circle</span> Clinician Profile
                </a>
                <div style="padding-top: 12px; border-top: 1px solid var(--border-light);">
                  <button class="btn btn-outline btn-sm btn-logout" style="width: 100%; display: flex; align-items: center; justify-content: center; gap: 6px;">
                    <span class="material-symbols-outlined">logout</span> Sign Out
                  </button>
                </div>
              </div>
            </div>
          </header>
        `;
      } else {
        // UNAUTHENTICATED USER HEADER: Brand Logo + Sign In / Get Started ONLY (No Nav Links)
        navbarRoot.innerHTML = `
          <header class="app-header">
            <div class="header-inner">
              <a href="index.html" class="brand-group">
                <div class="brand-icon">
                  <span class="material-symbols-outlined">radiology</span>
                </div>
                <div class="brand-text">
                  <span class="brand-title">GallScan AI</span>
                  <span class="brand-badge">CLINICAL PRECISION NARRATIVE</span>
                </div>
              </a>

              <!-- No nav links rendered for unauthenticated users -->

              <div class="header-actions">
                <div id="headerAuthSection" style="display: flex; align-items: center; gap: 8px;">
                  <a href="login.html" class="btn btn-outline btn-sm">Sign In</a>
                  <a href="signup.html" class="btn btn-primary btn-sm">Get Started</a>
                </div>
              </div>
            </div>
          </header>
        `;
      }
    }

    initMobileMenuToggle();
  }

  function initMobileMenuToggle() {
    const toggleBtn = document.getElementById("mobileMenuToggle");
    const drawer = document.getElementById("mobileDrawer");
    const icon = document.getElementById("mobileMenuIcon");

    if (!toggleBtn || !drawer) return;

    toggleBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      const isOpen = drawer.style.display === "block";
      if (isOpen) {
        drawer.style.display = "none";
        if (icon) icon.textContent = "menu";
      } else {
        drawer.style.display = "block";
        if (icon) icon.textContent = "close";
      }
    });

    document.addEventListener("click", (e) => {
      if (drawer.style.display === "block" && !drawer.contains(e.target) && e.target !== toggleBtn) {
        drawer.style.display = "none";
        if (icon) icon.textContent = "menu";
      }
    });
  }

  // Execute synchronously before DOM render paints
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", renderSharedHeader);
  } else {
    renderSharedHeader();
  }
})();
