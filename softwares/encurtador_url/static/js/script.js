// Script principal para o sistema de encurtador de URL
document.addEventListener('DOMContentLoaded', function() {
  // Elementos DOM
  const shortenerForm = document.getElementById('shortenerForm');
  const longUrlInput = document.getElementById('longUrl');
  const shortenButton = document.getElementById('shortenButton');
  const resultSection = document.getElementById('result');
  const shortUrlInput = document.getElementById('shortUrl');
  const copyButton = document.getElementById('copyButton');
  const loadingSection = document.getElementById('loading');
  const errorSection = document.getElementById('error');
  
  // Se estamos na página principal com o formulário
  if (shortenerForm) {
      // Manipulador de evento de envio do formulário
      shortenerForm.addEventListener('submit', function(event) {
          event.preventDefault();
          
          // Obter URL longa
          const longUrl = longUrlInput.value.trim();
          
          if (validateUrl(longUrl)) {
              // Mostrar carregamento
              showLoading();
              
              // Enviar solicitação para encurtar URL
              shortenUrl(longUrl)
                  .then(response => {
                      // Esconder carregamento
                      hideLoading();
                      
                      if (response.error) {
                          showError(response.error);
                      } else {
                          // Mostrar resultado
                          showResult(response.short_url);
                      }
                  })
                  .catch(error => {
                      hideLoading();
                      showError('Erro ao conectar com o servidor. Tente novamente.');
                      console.error('Erro:', error);
                  });
          } else {
              showError('Por favor, insira uma URL válida.');
          }
      });
      
      // Manipulador de evento de clique no botão de cópia
      if (copyButton) {
          copyButton.addEventListener('click', function() {
              copyToClipboard(shortUrlInput.value);
          });
      }
  }
  
  // Manipulador para botões de cópia na página de estatísticas
  const copyButtons = document.querySelectorAll('.copy-btn');
  copyButtons.forEach(button => {
      button.addEventListener('click', function() {
          const url = this.getAttribute('data-url');
          copyToClipboard(url);
      });
  });
  
  // Função para validar URL
  function validateUrl(url) {
      try {
          new URL(url);
          return true;
      } catch (e) {
          return false;
      }
  }
  
  // Função para encurtar URL usando a API
  async function shortenUrl(longUrl) {
      try {
          const response = await fetch('/shorten', {
              method: 'POST',
              headers: {
                  'Content-Type': 'application/json'
              },
              body: JSON.stringify({ url: longUrl })
          });
          
          return await response.json();
      } catch (error) {
          console.error('Erro ao encurtar URL:', error);
          throw error;
      }
  }
  
  // Função para copiar texto para a área de transferência
  function copyToClipboard(text) {
      navigator.clipboard.writeText(text)
          .then(() => {
              // Feedback visual temporário
              const button = document.activeElement;
              const originalText = button.textContent;
              
              button.textContent = 'Copiado!';
              button.style.backgroundColor = '#34a853';
              
              setTimeout(() => {
                  button.textContent = originalText;
                  button.style.backgroundColor = '';
              }, 2000);
          })
          .catch(err => {
              console.error('Erro ao copiar texto:', err);
              alert('Não foi possível copiar para a área de transferência.');
          });
  }
  
  // Função para mostrar a seção de resultado
  function showResult(shortUrl) {
      // Esconder outras seções
      hideError();
      hideLoading();
      
      // Preencher e mostrar resultado
      shortUrlInput.value = shortUrl;
      resultSection.classList.remove('hidden');
  }
  
  // Função para mostrar carregamento
  function showLoading() {
      hideError();
      resultSection.classList.add('hidden');
      loadingSection.classList.remove('hidden');
  }
  
  // Função para esconder carregamento
  function hideLoading() {
      loadingSection.classList.add('hidden');
  }
  
  // Função para mostrar erro
  function showError(message) {
      errorSection.textContent = message;
      errorSection.classList.remove('hidden');
  }
  
  // Função para esconder erro
  function hideError() {
      errorSection.classList.add('hidden');
  }
});