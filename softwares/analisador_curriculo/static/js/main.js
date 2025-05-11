// Funções auxiliares para a aplicação

// Animação de entrada de elementos
function animateEntrance() {
    const elements = document.querySelectorAll('.animate-entrance');
    elements.forEach((element, index) => {
        setTimeout(() => {
            element.classList.add('show');
        }, 100 * index);
    });
}

// Mostrar preview do arquivo selecionado
function showFilePreview() {
    const input = document.getElementById('resume');
    const previewContainer = document.getElementById('file-preview');
    
    if (input && previewContainer) {
        input.addEventListener('change', function() {
            previewContainer.innerHTML = '';
            
            if (this.files && this.files[0]) {
                const file = this.files[0];
                const fileInfo = document.createElement('div');
                fileInfo.classList.add('alert', 'alert-info', 'mt-2');
                
                const icon = document.createElement('i');
                icon.classList.add('fas', 'fa-file-pdf', 'me-2');
                
                fileInfo.appendChild(icon);
                fileInfo.appendChild(document.createTextNode(`${file.name} (${formatFileSize(file.size)})`));
                
                previewContainer.appendChild(fileInfo);
            }
        });
    }
}

// Formatar tamanho do arquivo
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Inicializar tooltips do Bootstrap
function initTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Função para animação da pontuação
function animateScore() {
    const scoreElement = document.querySelector('.score-circle');
    
    if (scoreElement) {
        const score = parseInt(scoreElement.textContent);
        let currentScore = 0;
        
        const interval = setInterval(() => {
            if (currentScore < score) {
                currentScore++;
                scoreElement.textContent = currentScore;
            } else {
                clearInterval(interval);
            }
        }, 20);
    }
}

// Função para destacar o nível atual na barra de progresso
function highlightCurrentLevel() {
    const nivelAtual = document.querySelector('.nivel-atual');
    if (!nivelAtual) return;
    
    const nivel = nivelAtual.textContent.trim().toLowerCase();
    const progressBar = document.querySelector('.progress-stacked');
    if (!progressBar) return;
    
    let position = 0;
    
    switch(nivel) {
        case 'estagiário':
            position = 12.5;
            break;
        case 'júnior':
            position = 37.5;
            break;
        case 'pleno':
            position = 62.5;
            break;
        case 'sênior':
            position = 87.5;
            break;
        default:
            return;
    }
    
    const indicator = document.createElement('div');
    indicator.className = 'nivel-indicator';
    indicator.style.left = `${position}%`;
    indicator.textContent = 'Você está aqui';
    progressBar.appendChild(indicator);
}

// Inicializar funções quando o DOM estiver pronto
document.addEventListener('DOMContentLoaded', function() {
    animateEntrance();
    showFilePreview();
    initTooltips();
    
    // Animação de pontuação na página de resultados
    if (document.querySelector('.score-circle')) {
        animateScore();
    }
    
    // Destacar nível atual na página de resultados
    if (document.querySelector('.nivel-atual')) {
        highlightCurrentLevel();
    }
});