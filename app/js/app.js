/**
 * Application Entry & Navigation Router
 */
document.addEventListener('DOMContentLoaded', async () => {
  Theme.init();

  // Tab switching
  const tabButtons = document.querySelectorAll('.tab-btn');
  const tabPanes = document.querySelectorAll('.tab-pane');

  tabButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const targetId = btn.getAttribute('data-tab');
      
      tabButtons.forEach(b => b.classList.remove('active'));
      tabPanes.forEach(p => p.classList.remove('active'));

      btn.classList.add('active');
      const targetPane = document.getElementById(targetId);
      if (targetPane) targetPane.classList.add('active');
    });
  });

  // Top header action buttons
  document.getElementById('btn-theme-toggle')?.addEventListener('click', () => Theme.toggle());

  document.getElementById('btn-import-excel')?.addEventListener('click', async () => {
    Toast.show('Selecting Excel workbook...', 'info');
    const res = await Bridge.call('import_excel_workbook');
    if (res && res.success) {
      Toast.show(res.message || 'Workbook imported successfully!', 'success');
      await AppState.loadInitialData();
    } else if (res) {
      Toast.show(res.message || 'Excel import failed or cancelled.', 'warning');
    }
  });

  document.getElementById('btn-export-backup')?.addEventListener('click', async () => {
    const res = await Bridge.call('export_backup_dialog');
    if (res && res.success) {
      Toast.show(res.message || 'Backup exported successfully!', 'success');
    } else if (res) {
      Toast.show(res.message || 'Export cancelled.', 'info');
    }
  });

  document.getElementById('btn-open-folder')?.addEventListener('click', async () => {
    await Bridge.call('open_data_folder');
  });

  // Close modals on backdrop click or close button
  document.querySelectorAll('.modal-close, .modal-backdrop').forEach(el => {
    el.addEventListener('click', (e) => {
      if (e.target === el || el.classList.contains('modal-close')) {
        Modal.closeAll();
      }
    });
  });

  // Native drag & drop excel file onto window
  window.addEventListener('dragover', (e) => e.preventDefault());
  window.addEventListener('drop', async (e) => {
    e.preventDefault();
    if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const file = e.dataTransfer.files[0];
      if (file.name.endsWith('.xlsx') || file.name.endsWith('.xls')) {
        Toast.show(`Importing dropped workbook: ${file.name}`, 'info');
        // If file.path is available (Electron/webview on desktop)
        const path = file.path || file.name;
        const res = await Bridge.call('import_excel_workbook', { file_path: path });
        if (res && res.success) {
          Toast.show('Dropped workbook imported!', 'success');
          await AppState.loadInitialData();
        }
      }
    }
  });

  // Initialize View Controllers
  SalaryView.init();
  ScheduleView.init();
  BillsView.init();
  SettlementsView.init();
  DashboardView.init();

  // Load state and trigger initial calculations
  await AppState.loadInitialData();

  console.log('Budgeting & Salary Suite loaded successfully.');
});
