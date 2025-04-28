// api/download.js
// API para download de arquivos do GitHub
const https = require('https');

// Função para registrar downloads
function logDownload(filename, req, selectedOS) {
  const logEntry = {
    filename,
    ip: req.headers['x-forwarded-for'] || req.socket.remoteAddress,
    timestamp: new Date().toISOString(),
    userAgent: req.headers['user-agent'],
    detectedOS: detectOS(req.headers['user-agent'] || ''),
    selectedOS: selectedOS || 'not_specified'
  };
  
  console.log('Download registrado:', logEntry);
}

// Função para detectar o sistema operacional do usuário
function detectOS(userAgent) {
  if (userAgent.includes('Macintosh') || userAgent.includes('Mac OS X')) {
    return 'macos';
  } else if (userAgent.includes('Windows')) {
    return 'windows';
  } else if (userAgent.includes('Linux')) {
    return 'linux';
  } else {
    return 'unknown';
  }
}

// Mapeamento de IDs para os nomes de arquivo no GitHub
const githubFileMap = {
  'neuraai-assistant': 'neuraai-assistant',
  'analisador-malware': 'analisador-malware',
  // Outros aplicativos...
};

// Lista de arquivos disponíveis
const availableFiles = Object.keys(githubFileMap);

// Função para obter a URL correta do GitHub para o arquivo bruto
function getGithubRawUrl(appId) {
  const githubFileName = githubFileMap[appId] || appId;
  return `https://raw.githubusercontent.com/LTD-2025-1-Cyber-Security-Project/apps/main/${githubFileName}`;
}

module.exports = (req, res) => {
  // Para URLs como /api/download.js?file=neuraai-assistant&os=windows
  const file = req.query.file;
  const selectedOS = req.query.os; // Novo parâmetro para o sistema operacional selecionado pelo usuário
  
  // Verificar se o arquivo foi especificado
  if (!file) {
    return res.status(400).json({ error: 'Nome do arquivo não especificado' });
  }
  
  // Verificar se o arquivo existe na lista
  if (!availableFiles.includes(file)) {
    return res.status(404).json({ error: 'Arquivo não encontrado' });
  }
  
  try {
    // Registrar o download com o OS selecionado pelo usuário
    logDownload(file, req, selectedOS);
    
    // Determinar o nome do arquivo para o download baseado no sistema operacional selecionado
    let downloadFilename = file;
    let fileExtension = '';
    
    // Aplicar a extensão apropriada com base na seleção do usuário
    if (selectedOS === 'windows') {
      fileExtension = '.exe';
    } else if (selectedOS === 'macos') {
      fileExtension = '.dmg';
    } else if (selectedOS === 'linux') {
      fileExtension = '.AppImage'; // Formato comum para aplicativos Linux
    }
    
    downloadFilename = `${file}${fileExtension}`;
    
    // Definir headers para forçar download do arquivo
    res.setHeader('Content-Disposition', `attachment; filename=${downloadFilename}`);
    res.setHeader('Content-Type', 'application/octet-stream');
    res.setHeader('Cache-Control', 'no-cache');
    
    // Obter o URL do GitHub para o arquivo
    const githubUrl = getGithubRawUrl(file);
    
    // Fazer uma requisição HTTP para o GitHub e servir o arquivo como download
    https.get(githubUrl, (githubRes) => {
      // Verificar se o arquivo foi encontrado no GitHub
      if (githubRes.statusCode !== 200) {
        console.error(`Erro ao acessar arquivo no GitHub: Status ${githubRes.statusCode}`);
        return res.status(404).json({ error: 'Arquivo não encontrado no GitHub' });
      }
      
      // Repassar o Content-Length se estiver disponível
      if (githubRes.headers['content-length']) {
        res.setHeader('Content-Length', githubRes.headers['content-length']);
      }
      
      // Fazer o pipe da resposta do GitHub para a resposta da nossa API
      githubRes.pipe(res);
      
      githubRes.on('error', (err) => {
        console.error('Erro ao transmitir arquivo do GitHub:', err);
        if (!res.headersSent) {
          res.status(500).json({ error: 'Erro ao processar download do GitHub' });
        }
      });
    }).on('error', (err) => {
      console.error('Erro na requisição ao GitHub:', err);
      res.status(500).json({ error: 'Erro ao conectar ao GitHub' });
    });
  } catch (error) {
    console.error('Erro ao processar download:', error);
    res.status(500).json({ error: 'Erro interno ao processar download' });
  }
};