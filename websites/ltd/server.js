// Servidor Express para o Portal da Prefeitura
const express = require('express');
const path = require('path');
const fs = require('fs');
const https = require('https');
const app = express();
const port = process.env.PORT || 3000;

// ========== CONFIGURAÇÃO DE PASTAS ESTÁTICAS ==========
// Configuração para servir arquivos estáticos
app.use('/css', express.static(path.join(__dirname, 'public', 'css')));
app.use('/js', express.static(path.join(__dirname, 'public', 'js')));
app.use('/images', express.static(path.join(__dirname, 'public', 'images')));
app.use('/dist', express.static(path.join(__dirname, 'dist')));
app.use(express.static(path.join(__dirname, 'public')));

// ========== CONFIGURAÇÃO DE DIRETÓRIOS ==========
// Pasta de logs
const logsDir = path.join(__dirname, 'logs');
if (!fs.existsSync(logsDir)) {
    fs.mkdirSync(logsDir, { recursive: true });
}

// Pasta de imagens
const imagesDir = path.join(__dirname, 'dist', 'images');
if (!fs.existsSync(imagesDir)) {
    fs.mkdirSync(imagesDir, { recursive: true });
}

// ========== UTILITÁRIOS ==========
// Função para detectar sistema operacional
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

// Atualize a função logDownload para registrar o sistema operacional selecionado
function logDownload(appName, ip, userAgent, selectedOS) {
    const logEntry = {
        appName,
        ip,
        timestamp: new Date().toISOString(),
        userAgent,
        detectedOS: detectOS(userAgent),
        selectedOS: selectedOS || 'not_specified'
    };
    
    const logFile = path.join(logsDir, 'downloads.log');
    try {
        fs.appendFileSync(logFile, JSON.stringify(logEntry) + '\n');
        console.log(`Download registrado: ${appName} por ${ip} [${detectOS(userAgent)}, selecionado: ${selectedOS}] em ${new Date().toLocaleString()}`);
    } catch (error) {
        console.error('Erro ao registrar download:', error);
    }
}


// ========== MAPEAMENTO GITHUB ==========
// Mapeamento de IDs para os nomes de arquivo no GitHub
const githubFileMap = {
    'neuraai-assistant': 'neuraai-assistant',
    'analisador-malware': 'analisador-malware',
    'curriculo-chatbot': 'curriculo-chatbot',
    'gerador-senhas': 'gerador-senhas',
    'iso-checklist': 'iso-checklist',
    'simulador-phishing': 'simulador-phishing',
    'templates-email': 'templates-email',
    // Os outros aplicativos podem seguir a mesma convenção do ID
    'analise-dados-dashboard': 'analise-dados-dashboard',
    'rpa-automacao': 'rpa-automacao',
    'oficios': 'oficios',
    'guia-ia-servidores': 'guia-ia-servidores',
    'treinamento-praticas-digitais': 'treinamento-praticas-digitais',
    'guia-tratamento-dados': 'guia-tratamento-dados'
};

// Função para obter a URL correta do GitHub para o arquivo bruto
function getGithubRawUrl(appId) {
    const githubFileName = githubFileMap[appId] || appId;
    return `https://raw.githubusercontent.com/LTD-2025-1-Cyber-Security-Project/apps/main/${githubFileName}`;
}

// ========== BANCO DE DADOS DE APLICATIVOS ==========
// Informações sobre os aplicativos disponíveis
const appDatabase = {
    "neuraai-assistant": {
        title: "neuraai-assistant",
        version: "v2.1.0",
        size: "45 MB",
        developer: "Equipe de IA - LTD Estácio",
        date: "15/03/2025",
        category: "Inteligência Artificial, Produtividade",
        requirements: "Windows 10/11, macOS, Linux, 4GB RAM, 100MB espaço livre",
        description: "Assistente virtual avançado baseado em inteligência artificial para atendimento automático ao cidadão e suporte aos servidores municipais."
    },
    // [Outros aplicativos estão aqui, omitidos por brevidade]
};

// ========== ROTAS API ==========
// Rota principal - servir a página inicial
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'index.html'));
});

// API para obter lista de aplicativos
app.get('/api/apps', (req, res) => {
    try {
        // Detectar sistema operacional do cliente
        const os = detectOS(req.headers['user-agent'] || '');
        
        // Criar lista de aplicativos com informações
        const appsWithInfo = Object.keys(appDatabase).map(appId => {
            const info = appDatabase[appId];
            
            // Determinar extensão baseada no sistema operacional
            let fileExtension = '';
            if (os === 'windows') {
                fileExtension = '.exe';
            }
            
            return {
                id: appId,
                title: info.title,
                version: info.version,
                size: info.size,
                category: info.category.toLowerCase().replace(', ', ' '),
                description: info.description,
                downloadName: appId + fileExtension,
                os: os
            };
        });
        
        res.json({ 
            success: true, 
            count: appsWithInfo.length,
            platform: os,
            apps: appsWithInfo 
        });
    } catch (error) {
        res.status(500).json({ success: false, error: error.message });
    }
});

// server.js - Rota para download de aplicativos
app.get('/apps/:appName', (req, res) => {
    const appName = req.params.appName;
    const selectedOS = req.query.os; // Adicionado para receber o sistema operacional selecionado
    
    // Verificar se o aplicativo existe no banco de dados
    if (!appDatabase[appName]) {
        return res.status(404).send('Aplicativo não encontrado');
    }
    
    // Determinar o OS e a extensão do arquivo
    let downloadFilename = appName;
    let fileExtension = '';
    
    // Aplicar a extensão apropriada com base na seleção do usuário
    if (selectedOS === 'windows') {
        fileExtension = '.exe';
    } else if (selectedOS === 'macos') {
        fileExtension = '.dmg';
    } else if (selectedOS === 'linux') {
        fileExtension = '.AppImage';
    }
    
    downloadFilename = `${appName}${fileExtension}`;
    
    // Registrar o download
    logDownload(appName, req.ip, req.headers['user-agent'], selectedOS);
    
    // Definir cabeçalhos para download
    res.setHeader('Content-Disposition', `attachment; filename=${downloadFilename}`);
    res.setHeader('Content-Type', 'application/octet-stream');
    
    // Obter o URL do GitHub para o arquivo
    const githubUrl = getGithubRawUrl(appName);
    
    // Fazer uma requisição HTTP para o GitHub e servir o arquivo como download
    https.get(githubUrl, (githubRes) => {
        // Verificar se o arquivo foi encontrado no GitHub
        if (githubRes.statusCode !== 200) {
            console.error(`Erro ao acessar arquivo no GitHub: Status ${githubRes.statusCode}`);
            return res.status(404).send('Arquivo não encontrado no GitHub');
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
                res.status(500).send('Erro ao processar download do GitHub');
            }
        });
    }).on('error', (err) => {
        console.error('Erro na requisição ao GitHub:', err);
        res.status(500).send('Erro ao conectar ao GitHub');
    });
});

// Iniciar o servidor
app.listen(port, () => {
    console.log(`Servidor rodando na porta ${port}`);
    console.log(`Acesse: http://localhost:${port}`);
    
    // Inicializar a imagem do laboratório
    const ltdImagePath = path.join(imagesDir, 'ltd.png');
    if (!fs.existsSync(ltdImagePath)) {
        try {
            // Podemos buscar a imagem do LTD do repositório também se estiver disponível
            console.log('Criando imagem de exemplo: dist/images/ltd.png');
            fs.writeFileSync(ltdImagePath, Buffer.alloc(1024 * 100));
            console.log('Imagem de exemplo criada: dist/images/ltd.png');
        } catch (error) {
            console.error('Erro ao criar imagem:', error);
        }
    }
});