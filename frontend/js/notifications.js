/**
 * GallScan AI — Notifications & Activity Stream Handler
 */

document.addEventListener("DOMContentLoaded", () => {
  initHeaderNotifications();
  initNotificationCenterPage();
});

// Top bar popover
function initHeaderNotifications() {
  const notifBtn = document.getElementById("headerNotifBtn");
  const popover = document.getElementById("headerNotifPopover");
  const badgeDot = document.getElementById("headerNotifBadge");
  const notifList = document.getElementById("headerNotifList");

  if (!notifBtn || !popover) return;

  notifBtn.addEventListener("click", async (e) => {
    e.stopPropagation();
    const isOpen = popover.classList.contains("open");
    if (!isOpen) {
      popover.classList.add("open");
      await loadHeaderNotifications();
    } else {
      popover.classList.remove("open");
    }
  });

  document.addEventListener("click", (e) => {
    if (!popover.contains(e.target) && e.target !== notifBtn) {
      popover.classList.remove("open");
    }
  });

  // Initial poll for unread badge
  if (API.isAuthenticated()) {
    checkUnreadBadge();
  }
}

async function checkUnreadBadge() {
  const badgeDot = document.getElementById("headerNotifBadge");
  if (!badgeDot) return;

  try {
    const res = await API.getNotifications(10);
    if (res.unread_count > 0) {
      badgeDot.style.display = "block";
    } else {
      badgeDot.style.display = "none";
    }
  } catch {}
}

async function loadHeaderNotifications() {
  const notifList = document.getElementById("headerNotifList");
  const badgeDot = document.getElementById("headerNotifBadge");
  if (!notifList) return;

  notifList.innerHTML = `<li style="padding: 16px; text-align: center; color: var(--text-light);"><span class="material-symbols-outlined" style="animation: spin 1s linear infinite;">sync</span> Loading...</li>`;

  try {
    const res = await API.getNotifications(10);
    if (badgeDot) badgeDot.style.display = res.unread_count > 0 ? "block" : "none";

    if (res.items.length === 0) {
      notifList.innerHTML = `<li style="padding: 20px; text-align: center; color: var(--text-muted); font-size: 13px;">No notifications found.</li>`;
      return;
    }

    notifList.innerHTML = res.items.slice(0, 5).map(n => `
      <li class="notif-item ${n.is_read ? '' : 'unread'}" data-id="${n.id}">
        <div style="font-weight: 600; font-size: 12px; color: var(--primary-navy); margin-bottom: 2px;">${n.title || 'System Alert'}</div>
        <div class="notif-text">${n.message}</div>
        <div class="notif-time">${new Date(n.created_at).toLocaleString()}</div>
      </li>
    `).join("");

    // Mark single as read on click
    notifList.querySelectorAll(".notif-item").forEach(item => {
      item.addEventListener("click", async () => {
        const id = item.getAttribute("data-id");
        await API.markNotificationRead(id);
        item.classList.remove("unread");
        checkUnreadBadge();
      });
    });

  } catch (err) {
    notifList.innerHTML = `<li style="padding: 16px; color: var(--error); font-size: 12px;">Failed to load alerts.</li>`;
  }
}

// Full Notification Center page
async function initNotificationCenterPage() {
  const container = document.getElementById("notificationCenterList");
  const markAllBtn = document.getElementById("markAllReadBtn");
  const emptyState = document.getElementById("notifEmptyState");

  if (!container) return;

  if (markAllBtn) {
    markAllBtn.addEventListener("click", async () => {
      try {
        await API.markAllNotificationsRead();
        await loadFullNotifications();
        checkUnreadBadge();
      } catch (err) {
        alert("Error marking all as read: " + err.message);
      }
    });
  }

  await loadFullNotifications();
}

async function loadFullNotifications() {
  const container = document.getElementById("notificationCenterList");
  const emptyState = document.getElementById("notifEmptyState");
  const unreadCountEl = document.getElementById("notifUnreadBadgeCount");

  if (!container) return;

  container.innerHTML = `<div style="text-align:center; padding: 40px;"><span class="material-symbols-outlined" style="animation: spin 1s linear infinite;">sync</span> Loading notification archives...</div>`;

  try {
    const res = await API.getNotifications(100);

    if (unreadCountEl) {
      unreadCountEl.textContent = `${res.unread_count} Unread`;
      unreadCountEl.className = res.unread_count > 0 ? "badge badge-teal" : "badge badge-navy";
    }

    if (res.items.length === 0) {
      container.innerHTML = "";
      if (emptyState) emptyState.style.display = "block";
      return;
    }

    if (emptyState) emptyState.style.display = "none";

    // Group notifications by date
    const groups = {
      Today: [],
      Yesterday: [],
      Earlier: []
    };

    const todayStr = new Date().toDateString();
    const yesterday = new Date();
    yesterday.setDate(yesterday.getDate() - 1);
    const yesterdayStr = yesterday.toDateString();

    res.items.forEach(n => {
      const dStr = new Date(n.created_at).toDateString();
      if (dStr === todayStr) {
        groups.Today.push(n);
      } else if (dStr === yesterdayStr) {
        groups.Yesterday.push(n);
      } else {
        groups.Earlier.push(n);
      }
    });

    let html = "";
    Object.entries(groups).forEach(([groupName, items]) => {
      if (items.length === 0) return;

      html += `
        <div style="margin-bottom: 24px;">
          <div class="label-caps" style="margin-bottom: 12px; color: var(--secondary-teal);">${groupName} (${items.length})</div>
          <div class="card" style="padding: 0; overflow: hidden;">
      `;

      items.forEach(n => {
        const timeStr = new Date(n.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        html += `
          <div class="notif-item ${n.is_read ? '' : 'unread'}" style="padding: 16px 20px; display: flex; align-items: flex-start; justify-content: space-between; gap: 16px;" data-id="${n.id}">
            <div style="display: flex; gap: 12px; align-items: flex-start;">
              <span class="material-symbols-outlined" style="color: ${n.is_read ? 'var(--text-light)' : 'var(--secondary-teal)'}; margin-top: 2px;">
                ${n.type === 'analysis_complete' ? 'biotech' : 'info'}
              </span>
              <div>
                <div style="font-weight: 700; font-size: 14px; color: var(--primary-navy); margin-bottom: 4px;">${n.title || 'Diagnostic Notification'}</div>
                <div style="font-size: 13px; color: var(--text-main); margin-bottom: 6px; line-height: 1.4;">${n.message}</div>
                <div class="notif-time mono-text" style="font-size: 11px; color: var(--text-light);">${timeStr}</div>
              </div>
            </div>
            <div style="display: flex; gap: 6px;">
              ${!n.is_read ? `
                <button class="btn btn-outline btn-sm btn-mark-read" data-id="${n.id}" title="Mark Read">
                  <span class="material-symbols-outlined" style="font-size: 16px;">done</span>
                </button>
              ` : ''}
              <button class="btn btn-danger btn-sm btn-delete-notif" data-id="${n.id}" title="Delete">
                <span class="material-symbols-outlined" style="font-size: 16px;">delete</span>
              </button>
            </div>
          </div>
        `;
      });

      html += `</div></div>`;
    });

    container.innerHTML = html;

    // Attach actions
    container.querySelectorAll(".btn-mark-read").forEach(b => {
      b.addEventListener("click", async (e) => {
        e.stopPropagation();
        const id = b.getAttribute("data-id");
        await API.markNotificationRead(id);
        await loadFullNotifications();
        checkUnreadBadge();
      });
    });

    container.querySelectorAll(".btn-delete-notif").forEach(b => {
      b.addEventListener("click", async (e) => {
        e.stopPropagation();
        const id = b.getAttribute("data-id");
        await API.deleteNotification(id);
        await loadFullNotifications();
        checkUnreadBadge();
      });
    });

  } catch (err) {
    container.innerHTML = `<div class="alert alert-error">Failed to load notifications: ${err.message}</div>`;
  }
}
