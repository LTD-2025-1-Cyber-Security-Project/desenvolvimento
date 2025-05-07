/**
 * Script principal da aplicação EdTech IA & Cyber
 */

document.addEventListener('DOMContentLoaded', function() {
  // Inicializa os tooltips do Bootstrap
  const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
  tooltipTriggerList.map(function(tooltipTriggerEl) {
      return new bootstrap.Tooltip(tooltipTriggerEl);
  });

  // Inicializa os popovers do Bootstrap
  const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
  popoverTriggerList.map(function(popoverTriggerEl) {
      return new bootstrap.Popover(popoverTriggerEl);
  });

  // Auto-fecha alertas após 5 segundos
  setTimeout(function() {
      const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
      alerts.forEach(function(alert) {
          const bsAlert = new bootstrap.Alert(alert);
          bsAlert.close();
      });
  }, 5000);

  // Manipulador para modais de confirmação
  const confirmationModals = document.querySelectorAll('.modal-confirm');
  confirmationModals.forEach(function(modal) {
      const confirmBtn = modal.querySelector('.btn-confirm');
      const form = modal.getAttribute('data-form');
      
      if (confirmBtn && form) {
          confirmBtn.addEventListener('click', function() {
              document.getElementById(form).submit();
          });
      }
  });

  // Preview de imagem para uploads
  const imageInputs = document.querySelectorAll('.image-upload');
  imageInputs.forEach(function(input) {
      const preview = document.getElementById(input.getAttribute('data-preview'));
      
      if (preview) {
          input.addEventListener('change', function() {
              if (this.files && this.files[0]) {
                  const reader = new FileReader();
                  
                  reader.onload = function(e) {
                      preview.src = e.target.result;
                  }
                  
                  reader.readAsDataURL(this.files[0]);
              }
          });
      }
  });

  // Verifica força da senha
  const passwordInputs = document.querySelectorAll('.password-strength');
  passwordInputs.forEach(function(input) {
      const feedback = document.getElementById(input.getAttribute('data-feedback'));
      
      if (feedback) {
          input.addEventListener('input', function() {
              const password = this.value;
              let strength = 0;
              let message = '';
              
              // Comprimento mínimo
              if (password.length >= 8) {
                  strength += 1;
              }
              
              // Letras maiúsculas e minúsculas
              if (/[a-z]/.test(password) && /[A-Z]/.test(password)) {
                  strength += 1;
              }
              
              // Números
              if (/\d/.test(password)) {
                  strength += 1;
              }
              
              // Caracteres especiais
              if (/[^a-zA-Z0-9]/.test(password)) {
                  strength += 1;
              }
              
              // Feedback baseado na força
              switch(strength) {
                  case 0:
                  case 1:
                      message = 'Fraca';
                      feedback.className = 'text-danger';
                      break;
                  case 2:
                      message = 'Média';
                      feedback.className = 'text-warning';
                      break;
                  case 3:
                      message = 'Boa';
                      feedback.className = 'text-info';
                      break;
                  case 4:
                      message = 'Forte';
                      feedback.className = 'text-success';
                      break;
              }
              
              feedback.textContent = message;
          });
      }
  });

  // Confirmação de logout
  const logoutLinks = document.querySelectorAll('.logout-link');
  logoutLinks.forEach(function(link) {
      link.addEventListener('click', function(e) {
          if (!confirm('Tem certeza que deseja sair?')) {
              e.preventDefault();
          }
      });
  });
});

// Funções auxiliares

/**
* Formata um número com separador de milhares
* @param {number} num - Número a ser formatado
* @returns {string} Número formatado
*/
function formatNumber(num) {
  return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ".");
}

/**
* Formata uma data ISO em formato legível
* @param {string} isoDate - Data em formato ISO
* @returns {string} Data formatada
*/
function formatDate(isoDate) {
  const date = new Date(isoDate);
  return date.toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric'
  });
}

/**
* Trunca um texto para o comprimento máximo
* @param {string} text - Texto a ser truncado
* @param {number} maxLength - Comprimento máximo
* @returns {string} Texto truncado
*/
function truncateText(text, maxLength) {
  if (text.length <= maxLength) {
      return text;
  }
  return text.substr(0, maxLength) + '...';
}

/**
* Adiciona uma classe CSS a um elemento por um período de tempo
* @param {Element} element - Elemento DOM
* @param {string} className - Nome da classe CSS
* @param {number} duration - Duração em milissegundos
*/
function flashClass(element, className, duration = 1000) {
  element.classList.add(className);
  setTimeout(() => {
      element.classList.remove(className);
  }, duration);
}