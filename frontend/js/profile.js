/**
 * GallScan AI — User Profile & Security Controller
 */

document.addEventListener("DOMContentLoaded", () => {
  loadProfileData();
  initProfileEditForm();
  initPasswordChangeForm();
});

async function loadProfileData() {
  const nameEl = document.getElementById("profileNameDisplay");
  const emailEl = document.getElementById("profileEmailDisplay");
  const roleEl = document.getElementById("profileRoleBadge");
  const scansCountEl = document.getElementById("profileTotalScans");
  const latestScanEl = document.getElementById("profileLatestScanDate");
  const editNameInput = document.getElementById("editProfileName");
  const editEmailInput = document.getElementById("editProfileEmail");

  try {
    const data = await API.getProfile();
    const user = data.user;

    if (nameEl) nameEl.textContent = user.name;
    if (emailEl) emailEl.textContent = user.email;
    if (roleEl) roleEl.textContent = (user.role || "Clinician").toUpperCase();
    if (scansCountEl) scansCountEl.textContent = data.total_scans || 0;
    if (latestScanEl) {
      if (data.latest_scan_date) {
        const d = new Date(data.latest_scan_date);
        latestScanEl.textContent = d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
      } else {
        latestScanEl.textContent = "No scans yet";
      }
    }

    if (editNameInput) editNameInput.value = user.name;
    if (editEmailInput) editEmailInput.value = user.email;

    // Update stored user
    API.setUser(user);
  } catch (err) {
    console.error("Failed to load user profile:", err);
  }
}

function initProfileEditForm() {
  const form = document.getElementById("editProfileForm");
  if (!form) return;

  const alertBox = document.getElementById("profileAlert");
  const successBox = document.getElementById("profileSuccess");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const name = document.getElementById("editProfileName").value.trim();
    const email = document.getElementById("editProfileEmail").value.trim();
    const submitBtn = form.querySelector("button[type='submit']");

    if (alertBox) alertBox.style.display = "none";
    if (successBox) successBox.style.display = "none";
    submitBtn.disabled = true;
    submitBtn.textContent = "Saving...";

    try {
      const updated = await API.updateProfile(name, email);
      API.setUser(updated);
      if (successBox) {
        successBox.textContent = "Profile updated successfully.";
        successBox.style.display = "block";
      }
      loadProfileData();
    } catch (err) {
      if (alertBox) {
        alertBox.textContent = err.message || "Failed to update profile.";
        alertBox.style.display = "flex";
      }
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = "Save Changes";
    }
  });
}

function initPasswordChangeForm() {
  const form = document.getElementById("changePasswordForm");
  if (!form) return;

  const alertBox = document.getElementById("passwordAlert");
  const successBox = document.getElementById("passwordSuccess");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const currentPassword = document.getElementById("currentPassword").value;
    const newPassword = document.getElementById("newPassword").value;
    const confirmPassword = document.getElementById("confirmPassword").value;
    const submitBtn = form.querySelector("button[type='submit']");

    if (alertBox) alertBox.style.display = "none";
    if (successBox) successBox.style.display = "none";

    if (newPassword !== confirmPassword) {
      if (alertBox) {
        alertBox.textContent = "New passwords do not match.";
        alertBox.style.display = "flex";
      }
      return;
    }

    submitBtn.disabled = true;
    submitBtn.textContent = "Updating Password...";

    try {
      const res = await API.changePassword(currentPassword, newPassword);
      if (successBox) {
        successBox.textContent = res.message || "Password changed successfully.";
        successBox.style.display = "block";
      }
      form.reset();
    } catch (err) {
      if (alertBox) {
        alertBox.textContent = err.message || "Failed to change password.";
        alertBox.style.display = "flex";
      }
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = "Update Password";
    }
  });
}
