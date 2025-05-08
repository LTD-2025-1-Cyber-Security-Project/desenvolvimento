/**
 * Sistema de IA da Prefeitura
 * main.js - Funções JavaScript globais do sistema
 */

document.addEventListener('DOMContentLoaded', function() {
  // Inicialização de elementos Bootstrap
  initializeBootstrapComponents();
  
  // Verificação de formulários
  setupFormValidation();
  
  // Configuração de eventos globais
  setupGlobalEvents();
  
  // Verificar URLs de parâmetros (para templates)
  processUrlParameters();
  
  // Configurar comportamento responsivo
  setupResponsiveBehavior();
  
  console.log('Sistema de IA da Prefeitura inicializado!');
});

/**
* Inicializa componentes do Bootstrap
*/
function initializeBootstrapComponents() {
  // Inicializar todos os tooltips
  const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
  [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
  
  // Inicializar todos os popovers
  const popoverTriggerList = document.querySelectorAll('[data-bs-toggle="popover"]');
  [...popoverTriggerList].map(popoverTriggerEl => new bootstrap.Popover(popoverTriggerEl));
  
  // Configurar comportamento de alertas
  document.querySelectorAll('.alert').forEach(alert => {
      if (!alert.classList.contains('alert-persistent')) {
          setTimeout(() => {
              const bsAlert = new bootstrap.Alert(alert);
              bsAlert.close();
          }, 5000);
      }
  });
}

/**
* Configura validação de formulários
*/
function setupFormValidation() {
  const forms = document.querySelectorAll('.needs-validation');
  
  forms.forEach(form => {
      form.addEventListener('submit', event => {
          if (!form.checkValidity()) {
              event.preventDefault();
              event.stopPropagation();
          }
          
          form.classList.add('was-validated');
      }, false);
  });
}

/**
* Configuração de eventos globais
*/
function setupGlobalEvents() {
  // Confirmação antes de ações destrutivas
  document.querySelectorAll('.confirm-action').forEach(element => {
      element.addEventListener('click', function(e) {
          if (!confirm('Tem certeza que deseja realizar esta ação?')) {
              e.preventDefault();
          }
      });
  });
  
  // Botão de voltar ao topo
  const backToTopButton = document.getElementById('backToTop');
  if (backToTopButton) {
      window.addEventListener('scroll', () => {
          if (window.scrollY > 300) {
              backToTopButton.classList.remove('d-none');
          } else {
              backToTopButton.classList.add('d-none');
          }
      });
      
      backToTopButton.addEventListener('click', () => {
          window.scrollTo({
              top: 0,
              behavior: 'smooth'
          });
      });
  }
}

/**
* Processa parâmetros de URL (usado para templates)
*/
function processUrlParameters() {
  const urlParams = new URLSearchParams(window.location.search);
  
  // Preencher campos de formulário com base em parâmetros da URL
  const formFields = [
      'document_type',
      'context',
      'legal_restrictions',
      'deadline',
      'detail_level'
  ];
  
  formFields.forEach(field => {
      const value = urlParams.get(field);
      const element = document.getElementById(field);
      
      if (value && element) {
          if (element.tagName === 'SELECT') {
              // Para elementos select, verificar se a opção existe
              const option = Array.from(element.options).find(opt => opt.value === value);
              if (option) {
                  element.value = value;
              }
          } else {
              // Para inputs e textareas
              element.value = value;
          }
      }
  });
}

/**
* Configuração de comportamento responsivo
*/
function setupResponsiveBehavior() {
  const isMobile = window.innerWidth < 768;
  
  // Ajustes específicos para dispositivos móveis
  if (isMobile) {
      // Reduzir tamanho de alguns elementos em telas pequenas
      document.querySelectorAll('.mobile-sm').forEach(el => {
          el.classList.add('btn-sm');
      });
      
      // Converter dropdowns para botões completos em telas pequenas
      document.querySelectorAll('.mobile-full-dropdown').forEach(dropdown => {
          dropdown.classList.add('dropdown-fullwidth');
      });
  }
}

/**
* Funções de utilidade
*/
const utils = {
  /**
   * Formata uma data ISO para formato local
   */
  formatDate: function(dateString) {
      const date = new Date(dateString);
      return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
  },
  
  /**
   * Copia texto para a área de transferência
   */
  copyToClipboard: function(text) {
      const textarea = document.createElement('textarea');
      textarea.value = text;
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand('copy');
      document.body.removeChild(textarea);
      return true;
  },
  
  /**
   * Formata texto para exibição
   */
  formatText: function(text, format) {
      switch(format) {
          case 'uppercase':
              return text.toUpperCase();
          case 'lowercase':
              return text.toLowerCase();
          case 'capitalize':
              return text.split(' ').map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase()).join(' ');
          default:
              return text;
      }
  },
  
  /**
   * Mostra um toast de notificação
   */
  showToast: function(message, type = 'info') {
      const toastContainer = document.querySelector('.toast-container');
      if (!toastContainer) return;
      
      const toast = document.createElement('div');
      toast.className = `toast align-items-center text-white bg-${type} border-0`;
      toast.setAttribute('role', 'alert');
      toast.setAttribute('aria-live', 'assertive');
      toast.setAttribute('aria-atomic', 'true');
      
      toast.innerHTML = `
          <div class="d-flex">
              <div class="toast-body">
                  ${message}
              </div>
              <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Fechar"></button>
          </div>
      `;
      
      toastContainer.appendChild(toast);
      const bsToast = new bootstrap.Toast(toast);
      bsToast.show();
      
      // Remover após fechado
      toast.addEventListener('hidden.bs.toast', function() {
          toast.remove();
      });
  }
};

// Deixar utils acessível globalmente
window.utils = utils;