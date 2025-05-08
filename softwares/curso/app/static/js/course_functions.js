/**
 * Funções JavaScript para gerenciamento de cursos
 * Este arquivo contém as funções necessárias para interagir com a API do sistema educacional,
 * incluindo matrícula em cursos e visualização de detalhes.
 */

// Inicializa o módulo quando o DOM estiver carregado
document.addEventListener('DOMContentLoaded', function() {
  // Inicializa todos os formulários de matrícula
  initEnrollmentForms();
  
  // Inicializa os botões de detalhes do curso
  initCourseDetailButtons();
  
  // Inicializa elementos da interface
  initUIElements();
});

/**
* Inicializa todos os formulários de matrícula em cursos
*/
function initEnrollmentForms() {
  const enrollmentForms = document.querySelectorAll('form[action*="enroll"]');
  
  enrollmentForms.forEach(form => {
      form.addEventListener('submit', function(e) {
          e.preventDefault();
          
          const submitButton = form.querySelector('button[type="submit"]');
          const originalButtonText = submitButton.innerHTML;
          
          // Altera o texto do botão para indicar carregamento
          submitButton.disabled = true;
          submitButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Processando...';
          
          // Prepara os dados do formulário
          const formData = new FormData(form);
          
          // Envia a solicitação de matrícula
          fetch(form.action, {
              method: 'POST',
              body: formData,
              headers: {
                  'X-Requested-With': 'XMLHttpRequest'
              },
              credentials: 'same-origin'
          })
          .then(response => {
              if (response.redirected) {
                  // Se a resposta for um redirecionamento, navega para a URL
                  window.location.href = response.url;
                  return;
              }
              
              if (!response.ok) {
                  throw new Error('Ocorreu um erro ao processar sua matrícula. Por favor, tente novamente.');
              }
              
              return response.json();
          })
          .then(data => {
              if (data) {
                  // Se recebemos dados JSON, exibimos uma mensagem de sucesso
                  showNotification('success', 'Matrícula realizada com sucesso!');
                  
                  // Recarrega a página após 1 segundo
                  setTimeout(() => {
                      window.location.reload();
                  }, 1000);
              }
          })
          .catch(error => {
              console.error('Erro ao matricular:', error);
              showNotification('danger', error.message || 'Ocorreu um erro ao processar sua matrícula.');
              
              // Restaura o botão
              submitButton.disabled = false;
              submitButton.innerHTML = originalButtonText;
          });
      });
  });
}

/**
* Inicializa os botões para visualização de detalhes do curso
*/
function initCourseDetailButtons() {
  const detailButtons = document.querySelectorAll('a[href*="course/"]');
  
  detailButtons.forEach(button => {
      // Apenas para links que não sejam de matrícula ou outros
      if (!button.href.includes('enroll') && button.getAttribute('role') !== 'tab') {
          button.addEventListener('click', function(e) {
              // Não previne a navegação padrão, apenas adiciona análise
              const courseSlug = button.href.split('/').pop();
              trackCourseView(courseSlug);
          });
      }
  });
}

/**
* Rastreia a visualização de um curso
* @param {string} courseSlug - O slug do curso visualizado
*/
function trackCourseView(courseSlug) {
  // Esta função pode ser expandida para registrar analytics ou outras métricas
  console.log(`Curso visualizado: ${courseSlug}`);
  
  // Você pode enviar dados para o servidor se necessário
  fetch(`/api/track-view/${courseSlug}`, {
      method: 'POST',
      headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest'
      },
      credentials: 'same-origin'
  }).catch(error => {
      // Ignora erros para não interromper a experiência do usuário
      console.error('Erro ao rastrear visualização:', error);
  });
}

/**
* Exibe uma notificação ao usuário
* @param {string} type - O tipo de notificação (success, danger, warning, info)
* @param {string} message - A mensagem a ser exibida
*/
function showNotification(type, message) {
  // Verifica se já existe um container de notificações
  let notificationsContainer = document.getElementById('notifications-container');
  
  if (!notificationsContainer) {
      // Cria o container de notificações se não existir
      notificationsContainer = document.createElement('div');
      notificationsContainer.id = 'notifications-container';
      notificationsContainer.style.position = 'fixed';
      notificationsContainer.style.top = '20px';
      notificationsContainer.style.right = '20px';
      notificationsContainer.style.zIndex = '9999';
      document.body.appendChild(notificationsContainer);
  }
  
  // Cria o elemento de alerta
  const alert = document.createElement('div');
  alert.className = `alert alert-${type} alert-dismissible fade show`;
  alert.role = 'alert';
  
  // Adiciona o ícone adequado
  let icon = '';
  if (type === 'success') icon = '<i class="fas fa-check-circle me-2"></i>';
  else if (type === 'danger') icon = '<i class="fas fa-exclamation-circle me-2"></i>';
  else if (type === 'warning') icon = '<i class="fas fa-exclamation-triangle me-2"></i>';
  else if (type === 'info') icon = '<i class="fas fa-info-circle me-2"></i>';
  
  // Define o conteúdo do alerta
  alert.innerHTML = `
      ${icon}${message}
      <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Fechar"></button>
  `;
  
  // Adiciona o alerta ao container
  notificationsContainer.appendChild(alert);
  
  // Remove o alerta após 5 segundos
  setTimeout(() => {
      if (alert && alert.parentNode) {
          alert.classList.remove('show');
          setTimeout(() => {
              alert.remove();
          }, 150);
      }
  }, 5000);
}

/**
* Inicializa elementos da interface do usuário
*/
function initUIElements() {
  // Inicializa tooltips do Bootstrap
  const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
  tooltipTriggerList.map(function(tooltipTriggerEl) {
      return new bootstrap.Tooltip(tooltipTriggerEl);
  });
  
  // Inicializa popovers do Bootstrap
  const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
  popoverTriggerList.map(function(popoverTriggerEl) {
      return new bootstrap.Popover(popoverTriggerEl);
  });
  
  // Animação suave de rolagem para links de âncora
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
      anchor.addEventListener('click', function(e) {
          const targetId = this.getAttribute('href');
          
          if (targetId !== '#' && document.querySelector(targetId)) {
              e.preventDefault();
              
              document.querySelector(targetId).scrollIntoView({
                  behavior: 'smooth'
              });
          }
      });
  });
}

/**
* Alterna entre modos de visualização de lista e grade
* @param {string} viewMode - O modo de visualização (grid ou list)
*/
function switchViewMode(viewMode) {
  const courseListContainer = document.querySelector('.course-list-container');
  
  if (!courseListContainer) return;
  
  if (viewMode === 'grid') {
      courseListContainer.classList.remove('list-view');
      courseListContainer.classList.add('grid-view');
      localStorage.setItem('courseViewMode', 'grid');
  } else {
      courseListContainer.classList.remove('grid-view');
      courseListContainer.classList.add('list-view');
      localStorage.setItem('courseViewMode', 'list');
  }
  
  // Atualiza os botões de modo de visualização
  document.querySelectorAll('.view-mode-btn').forEach(btn => {
      btn.classList.remove('active');
  });
  
  document.querySelector(`.view-mode-btn[data-view="${viewMode}"]`).classList.add('active');
}

/**
* Carrega o progresso do curso mais recente para o usuário
* @param {string} containerId - O ID do elemento onde o progresso será exibido
*/
function loadRecentProgress(containerId) {
  const container = document.getElementById(containerId);
  
  if (!container) return;
  
  fetch('/api/recent-progress', {
      method: 'GET',
      headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest'
      },
      credentials: 'same-origin'
  })
  .then(response => {
      if (!response.ok) {
          throw new Error('Não foi possível carregar o progresso recente');
      }
      return response.json();
  })
  .then(data => {
      // Atualiza o container com os dados recebidos
      if (data.courses && data.courses.length > 0) {
          let html = '<div class="row">';
          
          data.courses.forEach(course => {
              html += `
              <div class="col-md-6 col-lg-4 mb-4">
                  <div class="card h-100 shadow-sm">
                      <div class="card-body">
                          <h5 class="card-title">${course.title}</h5>
                          <div class="progress mb-3" style="height: 8px;">
                              <div class="progress-bar bg-success" role="progressbar" style="width: ${course.progress}%;" 
                                  aria-valuenow="${course.progress}" aria-valuemin="0" aria-valuemax="100">
                              </div>
                          </div>
                          <div class="d-flex justify-content-between align-items-center mb-3">
                              <small class="text-muted">${course.progress}% concluído</small>
                              <span class="badge bg-${course.category === 'IA' ? 'info' : 'danger'}">${course.category}</span>
                          </div>
                          <a href="/course/${course.slug}" class="btn btn-primary btn-sm w-100">Continuar</a>
                      </div>
                  </div>
              </div>
              `;
          });
          
          html += '</div>';
          container.innerHTML = html;
      } else {
          container.innerHTML = `
          <div class="alert alert-info">
              <i class="fas fa-info-circle me-2"></i>
              Você ainda não iniciou nenhum curso. 
              <a href="/courses" class="alert-link">Explore nossos cursos</a> para começar sua jornada de aprendizado.
          </div>
          `;
      }
  })
  .catch(error => {
      console.error('Erro ao carregar progresso:', error);
      container.innerHTML = `
      <div class="alert alert-danger">
          <i class="fas fa-exclamation-circle me-2"></i>
          Não foi possível carregar seu progresso recente. Por favor, recarregue a página.
      </div>
      `;
  });
}

// Exporta as funções para uso global
window.courseUtils = {
  switchViewMode,
  loadRecentProgress
};