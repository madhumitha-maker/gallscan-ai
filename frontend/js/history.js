/**
 * GallScan AI — Scan History & Record Management
 */

let currentPage = 1;
const pageSize = 10;
let currentFilter = "";
let currentSearch = "";

document.addEventListener("DOMContentLoaded", () => {
  loadHistoryData();
  initHistoryControls();
  initModal();
});

function initHistoryControls() {
  const filterSelect = document.getElementById("historyClassFilter");
  const searchInput = document.getElementById("historySearchInput");
  const prevBtn = document.getElementById("prevPageBtn");
  const nextBtn = document.getElementById("nextPageBtn");

  if (filterSelect) {
    filterSelect.addEventListener("change", (e) => {
      currentFilter = e.target.value;
      currentPage = 1;
      loadHistoryData();
    });
  }

  if (searchInput) {
    let debounceTimer;
    searchInput.addEventListener("input", (e) => {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => {
        currentSearch = e.target.value.trim();
        currentPage = 1;
        loadHistoryData();
      }, 300);
    });
  }

  if (prevBtn) {
    prevBtn.addEventListener("click", () => {
      if (currentPage > 1) {
        currentPage--;
        loadHistoryData();
      }
    });
  }

  if (nextBtn) {
    nextBtn.addEventListener("click", () => {
      currentPage++;
      loadHistoryData();
    });
  }
}

async function loadHistoryData() {
  const tableBody = document.getElementById("historyTableBody");
  const emptyState = document.getElementById("historyEmptyState");
  const tableContainer = document.getElementById("historyTableContainer");
  const totalCountEl = document.getElementById("historyTotalCount");
  const pageNumEl = document.getElementById("historyPageNum");
  const prevBtn = document.getElementById("prevPageBtn");
  const nextBtn = document.getElementById("nextPageBtn");

  if (!tableBody) return;

  tableBody.innerHTML = `<tr><td colspan="6" style="text-align:center; padding: 32px;"><span class="material-symbols-outlined" style="animation: spin 1s linear infinite;">sync</span> Loading scan archives...</td></tr>`;

  try {
    const res = await API.getHistory(currentPage, pageSize, currentFilter, currentSearch);

    if (totalCountEl) totalCountEl.textContent = `${res.total} Scans`;
    if (pageNumEl) pageNumEl.textContent = `Page ${res.page} of ${res.total_pages || 1}`;

    if (prevBtn) prevBtn.disabled = res.page <= 1;
    if (nextBtn) nextBtn.disabled = res.page >= res.total_pages;

    if (res.items.length === 0) {
      if (tableContainer) tableContainer.style.display = "none";
      if (emptyState) emptyState.style.display = "block";
      return;
    }

    if (tableContainer) tableContainer.style.display = "block";
    if (emptyState) emptyState.style.display = "none";

    tableBody.innerHTML = res.items.map(item => {
      const origUrl = item.original_image_url ? `${API_BASE}${item.original_image_url}` : "";
      const camUrl = item.gradcam_image_url ? `${API_BASE}${item.gradcam_image_url}` : "";
      const dateStr = new Date(item.created_at).toLocaleDateString("en-US", {
        month: "short", day: "numeric", year: "numeric", hour: "2-digit", minute: "2-digit"
      });
      const confPct = (item.confidence * 100).toFixed(1);
      const badgeClass = item.confidence > 0.8 ? "badge-teal" : (item.confidence > 0.5 ? "badge-warning" : "badge-danger");

      return `
        <tr>
          <td style="width: 60px;">
            <img src="${origUrl}" alt="Scan" style="width: 44px; height: 44px; object-fit: cover; border-radius: var(--radius-xs); border: 1px solid var(--border-light);" onerror="this.src='data:image/svg+xml;utf8,<svg xmlns=\\'http://www.w3.org/2000/svg\\' width=\\'44\\' height=\\'44\\' fill=\\'%23ccc\\'><rect width=\\'44\\' height=\\'44\\'/></svg>'">
          </td>
          <td>
            <strong style="color: var(--primary-navy);">${item.filename}</strong>
            <div style="font-size: 11px; color: var(--text-light); font-family: var(--font-mono);">ID: #${item.id}</div>
          </td>
          <td>
            <div style="font-weight: 600; color: var(--primary-navy);">${item.predicted_display_name}</div>
          </td>
          <td>
            <span class="badge ${badgeClass}">${confPct}%</span>
          </td>
          <td class="mono-text" style="font-size: 12px; color: var(--text-muted);">${dateStr}</td>
          <td style="text-align: right; white-space: nowrap;">
            <a href="result.html?id=${item.id}" class="btn btn-outline btn-sm" title="View Full Report">
              <span class="material-symbols-outlined" style="font-size: 16px;">visibility</span> Report
            </a>
            <button class="btn btn-danger btn-sm btn-delete-scan" data-id="${item.id}" style="margin-left: 6px;" title="Delete Record">
              <span class="material-symbols-outlined" style="font-size: 16px;">delete</span>
            </button>
          </td>
        </tr>
      `;
    }).join("");

    // Attach delete events
    document.querySelectorAll(".btn-delete-scan").forEach(btn => {
      btn.addEventListener("click", async (e) => {
        const id = e.currentTarget.getAttribute("data-id");
        if (confirm(`Are you sure you want to delete scan #${id}? This action cannot be undone.`)) {
          try {
            await API.deletePrediction(id);
            loadHistoryData();
          } catch (err) {
            alert("Error deleting record: " + err.message);
          }
        }
      });
    });

  } catch (err) {
    tableBody.innerHTML = `<tr><td colspan="6" style="text-align:center; padding: 24px; color: var(--error);">Error loading history: ${err.message}</td></tr>`;
  }
}

function initModal() {
  const modal = document.getElementById("historyModal");
  const closeBtn = document.getElementById("closeModalBtn");
  if (!modal || !closeBtn) return;

  closeBtn.addEventListener("click", () => {
    modal.classList.remove("open");
  });

  window.addEventListener("click", (e) => {
    if (e.target === modal) modal.classList.remove("open");
  });
}
