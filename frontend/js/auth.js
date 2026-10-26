/**
 * GallScan AI — Authentication & Navigation Controller
 */

document.addEventListener("DOMContentLoaded", () => {
  initAuthUI();
  initLoginForm();
  initSignupForm();
  initForgotPasswordForm();
  initResetPasswordForm();
});

function initAuthUI() {
  const user = API.getUser();
  const token = API.getToken();
  const path = window.location.pathname.toLowerCase();

  // 1. If authenticated user visits home page, redirect them directly to upload.html
  const isHome = path.endsWith("index.html") || path.endsWith("/") || path === "" || path.endsWith("/client") || path.endsWith("/client/");
  if (isHome && token && user) {
    window.location.href = "upload.html";
    return;
  }

  // 2. Check route protection for authenticated pages
  const isProtected = path.endsWith("upload.html") || 
                      path.endsWith("result.html") || 
                      path.endsWith("history.html") || 
                      path.endsWith("profile.html") || 
                      path.endsWith("notifications.html");

  if (isProtected && (!token || !user)) {
    window.location.href = `login.html?redirect=${encodeURIComponent(window.location.pathname + window.location.search)}`;
    return;
  }

  // 3. Update header user info if logged in
  const userNameEl = document.getElementById("headerUserName");
  const userAvatarEl = document.getElementById("headerUserAvatar");

  if (token && user) {
    if (userNameEl) userNameEl.textContent = user.name || user.email.split("@")[0];
    if (userAvatarEl) userAvatarEl.textContent = (user.name || user.email)[0].toUpperCase();
  }

  // 4. Attach logout handlers
  const logoutBtns = document.querySelectorAll(".btn-logout");
  logoutBtns.forEach(btn => {
    btn.addEventListener("click", (e) => {
      e.preventDefault();
      API.removeToken();
      window.location.href = "login.html?logged_out=1";
    });
  });
}

function initLoginForm() {
  const form = document.getElementById("loginForm");
  if (!form) return;

  const alertBox = document.getElementById("loginAlert");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const email = document.getElementById("loginEmail").value.trim();
    const password = document.getElementById("loginPassword").value;
    const submitBtn = form.querySelector("button[type='submit']");

    if (alertBox) alertBox.style.display = "none";
    submitBtn.disabled = true;
    submitBtn.textContent = "Authenticating...";

    try {
      const res = await API.login(email, password);
      API.setToken(res.access_token);
      API.setUser(res.user);

      // Check redirect param
      const urlParams = new URLSearchParams(window.location.search);
      const redirect = urlParams.get("redirect") || "upload.html";
      window.location.href = redirect;
    } catch (err) {
      if (alertBox) {
        alertBox.textContent = err.message || "Failed to sign in. Please check credentials.";
        alertBox.style.display = "flex";
      }
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = "Sign In to Console";
    }
  });
}

function initSignupForm() {
  const form = document.getElementById("signupForm");
  if (!form) return;

  const alertBox = document.getElementById("signupAlert");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const name = document.getElementById("signupName").value.trim();
    const email = document.getElementById("signupEmail").value.trim();
    const password = document.getElementById("signupPassword").value;
    const role = document.getElementById("signupRole") ? document.getElementById("signupRole").value : "clinician";
    const submitBtn = form.querySelector("button[type='submit']");

    if (alertBox) alertBox.style.display = "none";
    submitBtn.disabled = true;
    submitBtn.textContent = "Registering Account...";

    try {
      const res = await API.signup(name, email, password, role);
      API.setToken(res.access_token);
      API.setUser(res.user);
      window.location.href = "upload.html";
    } catch (err) {
      if (alertBox) {
        alertBox.textContent = err.message || "Registration failed.";
        alertBox.style.display = "flex";
      }
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = "Create Account";
    }
  });
}

function initForgotPasswordForm() {
  const form = document.getElementById("forgotPasswordForm");
  if (!form) return;

  const alertBox = document.getElementById("forgotAlert");
  const successBox = document.getElementById("forgotSuccess");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const email = document.getElementById("forgotEmail").value.trim();
    const submitBtn = form.querySelector("button[type='submit']");

    if (alertBox) alertBox.style.display = "none";
    if (successBox) successBox.style.display = "none";
    submitBtn.disabled = true;
    submitBtn.textContent = "Dispatching...";

    try {
      const res = await API.forgotPassword(email);
      if (successBox) {
        successBox.innerHTML = `<strong>Recovery request received.</strong><br>${res.message}`;
        if (res.demo_reset_token) {
          successBox.innerHTML += `<div style="margin-top:10px; font-family: monospace; font-size: 11px; background:#fff; padding:8px; border:1px solid #ccc; word-break: break-all;">
            <strong>Demo Token:</strong> ${res.demo_reset_token}<br>
            <a href="forgot-password.html?token=${encodeURIComponent(res.demo_reset_token)}" style="color:#006666; font-weight:bold; margin-top:4px; display:inline-block;">Click here to Reset Password</a>
          </div>`;
        }
        successBox.style.display = "block";
      }
    } catch (err) {
      if (alertBox) {
        alertBox.textContent = err.message;
        alertBox.style.display = "flex";
      }
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = "Send Reset Link";
    }
  });
}

function initResetPasswordForm() {
  const form = document.getElementById("resetPasswordForm");
  if (!form) return;

  // Pre-fill token from URL
  const urlParams = new URLSearchParams(window.location.search);
  const token = urlParams.get("token");
  if (token) {
    const tokenInput = document.getElementById("resetToken");
    if (tokenInput) tokenInput.value = token;
  }

  const alertBox = document.getElementById("resetAlert");
  const successBox = document.getElementById("resetSuccess");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const tokenVal = document.getElementById("resetToken").value.trim();
    const newPassword = document.getElementById("newPassword").value;
    const submitBtn = form.querySelector("button[type='submit']");

    if (alertBox) alertBox.style.display = "none";
    if (successBox) successBox.style.display = "none";
    submitBtn.disabled = true;
    submitBtn.textContent = "Updating...";

    try {
      const res = await API.resetPassword(tokenVal, newPassword);
      if (successBox) {
        successBox.textContent = res.message || "Password updated successfully. Redirecting to login...";
        successBox.style.display = "block";
        setTimeout(() => {
          window.location.href = "login.html";
        }, 2000);
      }
    } catch (err) {
      if (alertBox) {
        alertBox.textContent = err.message;
        alertBox.style.display = "flex";
      }
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = "Confirm New Password";
    }
  });
}
