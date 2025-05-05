// Global utilities
function showToast(message, type = 'info') {
  const toastContainer = document.getElementById('toastContainer') || createToastContainer();
  const toastId = 'toast-' + Date.now();
  
  const toastHTML = `
      <div id="${toastId}" class="toast align-items-center text-white bg-${type}" role="alert">
          <div class="d-flex">
              <div class="toast-body">${message}</div>
              <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
          </div>
      </div>
  `;
  
  toastContainer.insertAdjacentHTML('beforeend', toastHTML);
  const toastElement = document.getElementById(toastId);
  const toast = new bootstrap.Toast(toastElement);
  toast.show();
  
  toastElement.addEventListener('hidden.bs.toast', () => {
      toastElement.remove();
  });
}

function createToastContainer() {
  const container = document.createElement('div');
  container.id = 'toastContainer';
  container.className = 'toast-container position-fixed top-0 end-0 p-3';
  document.body.appendChild(container);
  return container;
}

// Theme management
function toggleTheme() {
  const html = document.documentElement;
  const currentTheme = html.getAttribute('data-theme');
  const newTheme = currentTheme === 'light' ? 'dark' : 'light';
  html.setAttribute('data-theme', newTheme);
  localStorage.setItem('theme', newTheme);
  
  // Update theme button icon
  const themeBtn = document.querySelector('[onclick="toggleTheme()"] i');
  themeBtn.className = newTheme === 'light' ? 'bi bi-moon-stars' : 'bi bi-sun';
}

function setTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  localStorage.setItem('theme', theme);
  document.getElementById('themeSelect').value = theme;
}

// File utilities
function formatFileSize(bytes) {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function getFileIcon(filename) {
  const ext = filename.split('.').pop().toLowerCase();
  const iconMap = {
      'pdf': 'bi-file-earmark-pdf',
      'doc': 'bi-file-earmark-word',
      'docx': 'bi-file-earmark-word',
      'xls': 'bi-file-earmark-excel',
      'xlsx': 'bi-file-earmark-excel',
      'ppt': 'bi-file-earmark-ppt',
      'pptx': 'bi-file-earmark-ppt',
      'jpg': 'bi-file-earmark-image',
      'jpeg': 'bi-file-earmark-image',
      'png': 'bi-file-earmark-image',
      'txt': 'bi-file-earmark-text',
      'csv': 'bi-file-earmark-spreadsheet'
  };
  return iconMap[ext] || 'bi-file-earmark';
}

// API utilities
async function apiRequest(url, method = 'GET', data = null) {
  const options = {
      method,
      headers: {}
  };
  
  if (data) {
      if (data instanceof FormData) {
          options.body = data;
      } else {
          options.headers['Content-Type'] = 'application/json';
          options.body = JSON.stringify(data);
      }
  }
  
  try {
      const response = await fetch(url, options);
      const result = await response.json();
      
      if (!response.ok) {
          throw new Error(result.error || 'Erro na requisição');
      }
      
      return result;
  } catch (error) {
      console.error('API Error:', error);
      throw error;
  }
}

// File upload progress
function createProgressBar(filename) {
  const progressHtml = `
      <div class="file-upload-progress mb-3">
          <div class="d-flex justify-content-between mb-1">
              <span>${filename}</span>
              <span class="progress-percent">0%</span>
          </div>
          <div class="progress">
              <div class="progress-bar progress-bar-striped progress-bar-animated" 
                   role="progressbar" style="width: 0%"></div>
          </div>
      </div>
  `;
  return progressHtml;
}

function updateProgress(progressElement, percent) {
  const progressBar = progressElement.querySelector('.progress-bar');
  const progressText = progressElement.querySelector('.progress-percent');
  
  progressBar.style.width = `${percent}%`;
  progressText.textContent = `${percent}%`;
}

// Drag and drop utilities
function setupDragAndDrop(element, onDrop) {
  element.addEventListener('dragenter', (e) => {
      e.preventDefault();
      e.stopPropagation();
      element.classList.add('dragover');
  });

  element.addEventListener('dragover', (e) => {
      e.preventDefault();
      e.stopPropagation();
      element.classList.add('dragover');
  });

  element.addEventListener('dragleave', (e) => {
      e.preventDefault();
      e.stopPropagation();
      element.classList.remove('dragover');
  });

  element.addEventListener('drop', (e) => {
      e.preventDefault();
      e.stopPropagation();
      element.classList.remove('dragover');
      
      const files = Array.from(e.dataTransfer.files);
      if (onDrop) onDrop(files);
  });
}

// Form validation
function validateForm(formElement) {
  const requiredFields = formElement.querySelectorAll('[required]');
  let isValid = true;
  
  requiredFields.forEach(field => {
      if (!field.value.trim()) {
          field.classList.add('is-invalid');
          isValid = false;
      } else {
          field.classList.remove('is-invalid');
      }
  });
  
  return isValid;
}

// Debounce function
function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
      const later = () => {
          clearTimeout(timeout);
          func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
  };
}

// Search functionality
function setupSearch(inputElement, searchFunction) {
  const debouncedSearch = debounce(searchFunction, 300);
  
  inputElement.addEventListener('input', (e) => {
      const query = e.target.value.trim();
      debouncedSearch(query);
  });
}

// Copy to clipboard
function copyToClipboard(text) {
  if (navigator.clipboard) {
      navigator.clipboard.writeText(text).then(() => {
          showToast('Copiado para a área de transferência!', 'success');
      }).catch(() => {
          fallbackCopyToClipboard(text);
      });
  } else {
      fallbackCopyToClipboard(text);
  }
}

function fallbackCopyToClipboard(text) {
  const textArea = document.createElement('textarea');
  textArea.value = text;
  textArea.style.position = 'fixed';
  textArea.style.left = '-999999px';
  document.body.appendChild(textArea);
  textArea.focus();
  textArea.select();
  
  try {
      document.execCommand('copy');
      showToast('Copiado para a área de transferência!', 'success');
  } catch (err) {
      showToast('Erro ao copiar', 'danger');
  }
  
  document.body.removeChild(textArea);
}

// Initialize tooltips
function initializeTooltips() {
  const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
  tooltipTriggerList.map(function (tooltipTriggerEl) {
      return new bootstrap.Tooltip(tooltipTriggerEl);
  });
}

// Settings management
function saveSettings() {
  const settings = {
      theme: document.getElementById('themeSelect').value,
      ocrLanguage: document.getElementById('ocrLanguage').value,
      conversionQuality: document.getElementById('conversionQuality').value
  };
  
  localStorage.setItem('settings', JSON.stringify(settings));
  showToast('Configurações salvas com sucesso!', 'success');
  
  const modal = bootstrap.Modal.getInstance(document.getElementById('settingsModal'));
  if (modal) modal.hide();
}

function loadSettings() {
  const savedSettings = JSON.parse(localStorage.getItem('settings') || '{}');
  
  if (savedSettings.theme) {
      setTheme(savedSettings.theme);
  }
  
  if (savedSettings.ocrLanguage) {
      document.getElementById('ocrLanguage').value = savedSettings.ocrLanguage;
  }
  
  if (savedSettings.conversionQuality) {
      document.getElementById('conversionQuality').value = savedSettings.conversionQuality;
  }
}

// Chart utilities
function createChart(canvasId, type, data, options = {}) {
  const ctx = document.getElementById(canvasId).getContext('2d');
  return new Chart(ctx, {
      type: type,
      data: data,
      options: {
          responsive: true,
          maintainAspectRatio: false,
          ...options
      }
  });
}

// Initialize app
document.addEventListener('DOMContentLoaded', function() {
  // Load saved theme
  const savedTheme = localStorage.getItem('theme') || 'light';
  setTheme(savedTheme);
  
  // Load other settings
  loadSettings();
  
  // Initialize tooltips
  initializeTooltips();
  
  // Setup global error handler
  window.addEventListener('error', function(e) {
      console.error('Global error:', e);
      showToast('Ocorreu um erro inesperado', 'danger');
  });
  
  // Handle unhandled promise rejections
  window.addEventListener('unhandledrejection', function(e) {
      console.error('Unhandled promise rejection:', e);
      showToast('Ocorreu um erro inesperado', 'danger');
  });
});

// Export utilities for use in other scripts
window.appUtils = {
  showToast,
  formatFileSize,
  getFileIcon,
  apiRequest,
  setupDragAndDrop,
  validateForm,
  debounce,
  copyToClipboard,
  createChart
};