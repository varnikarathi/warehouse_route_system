/* ROUTEFLOW Main UI JavaScript */

document.addEventListener('DOMContentLoaded', () => {
  // 1. Mobile Sidebar Toggle
  const sidebar = document.getElementById('appSidebar');
  const sidebarToggle = document.getElementById('sidebarToggle');

  if (sidebarToggle && sidebar) {
    sidebarToggle.addEventListener('click', (e) => {
      e.stopPropagation();
      sidebar.classList.toggle('open');
    });

    document.addEventListener('click', (e) => {
      if (window.innerWidth <= 900 && sidebar.classList.contains('open') && !sidebar.contains(e.target)) {
        sidebar.classList.remove('open');
      }
    });
  }

  // 2. Notification Popover
  const notifBtn = document.getElementById('notifBtn');
  const notifDropdown = document.getElementById('notifDropdown');

  if (notifBtn && notifDropdown) {
    notifBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      notifDropdown.classList.toggle('show');
      if (userDropdown) userDropdown.classList.remove('show');
    });
  }

  // 3. User Menu Dropdown
  const userMenuBtn = document.getElementById('userMenuBtn');
  const userDropdown = document.getElementById('userDropdown');

  if (userMenuBtn && userDropdown) {
    userMenuBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      userDropdown.classList.toggle('show');
      if (notifDropdown) notifDropdown.classList.remove('show');
    });
  }

  // Close dropdowns on outside click
  document.addEventListener('click', () => {
    if (notifDropdown) notifDropdown.classList.remove('show');
    if (userDropdown) userDropdown.classList.remove('show');
  });

  // 4. Global Search Modal (Ctrl/Cmd + K)
  const openSearchBtn = document.getElementById('openSearchBtn');
  const searchModal = document.getElementById('searchModal');
  const searchInput = document.getElementById('globalSearchInput');

  function openSearch() {
    if (searchModal) {
      searchModal.classList.add('show');
      if (searchInput) {
        searchInput.focus();
        searchInput.value = '';
      }
    }
  }

  function closeSearch() {
    if (searchModal) {
      searchModal.classList.remove('show');
    }
  }

  if (openSearchBtn) {
    openSearchBtn.addEventListener('click', openSearch);
  }

  if (searchModal) {
    searchModal.addEventListener('click', (e) => {
      if (e.target === searchModal) {
        closeSearch();
      }
    });
  }

  document.addEventListener('keydown', (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
      e.preventDefault();
      if (searchModal && searchModal.classList.contains('show')) {
        closeSearch();
      } else {
        openSearch();
      }
    } else if (e.key === 'Escape') {
      closeSearch();
    }
  });

  // Re-run Lucide icons creation if dynamic elements are inserted
  if (window.lucide) {
    window.lucide.createIcons();
  }
});
