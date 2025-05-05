# DocMaster Pro - Sistema Inteligente de Processamento de Documentos

![DocMaster Pro](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.9+-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Build Status](https://img.shields.io/badge/build-passing-green.svg)

<p align="center">
  <img src="static/images/logo.png" alt="DocMaster Pro Logo" width="200"/>
</p>

## 📋 Sobre o Projeto

DocMaster Pro é uma solução completa e profissional para manipulação, conversão e análise inteligente de documentos. Utilizando tecnologias de ponta como Flask, Google Gemini AI e processamento avançado de PDFs, o sistema oferece uma experiência poderosa e intuitiva para profissionais que trabalham com documentos.

### ✨ Principais Características

- 🤖 **Análise Inteligente com IA**: Integração com Google Gemini para extração de insights, resumos automáticos e análise de sentimento
- 🔄 **Conversor Universal**: Suporte a mais de 100 formatos de arquivo com conversão de alta fidelidade
- 👁️ **OCR Avançado**: Extração de texto de imagens e PDFs escaneados com precisão superior a 99%
- 🛠️ **Ferramentas PDF Completas**: Merge, split, compressão, rotação e edição avançada
- 🔒 **Segurança Empresarial**: Criptografia, marca d'água, assinatura digital e controle de acesso
- 📊 **Dashboard Analítico**: Visualização de dados e estatísticas de uso em tempo real
- 🚀 **Alto Desempenho**: Processamento paralelo e otimização para grandes volumes

## 🚀 Início Rápido

### Pré-requisitos

- Python 3.9 ou superior
- pip (gerenciador de pacotes Python)
- Tesseract OCR
- Redis (opcional, para processamento assíncrono)

### Instalação

1. **Clone o repositório**
```bash
git clone https://github.com/seu-usuario/docmaster-pro.git
cd docmaster-pro
```

2. **Execute o instalador automático**
```bash
python run.py
```

O instalador irá:
- Criar um ambiente virtual
- Instalar todas as dependências
- Configurar o banco de dados
- Iniciar o servidor
- Abrir o navegador automaticamente

### Instalação Manual

1. **Crie um ambiente virtual**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

2. **Instale as dependências**
```bash
pip install -r requirements.txt
```

3. **Configure as variáveis de ambiente**
```bash
cp .env.example .env
# Edite o arquivo .env com suas configurações
```

4. **Inicialize o banco de dados**
```bash
flask init-db
```

5. **Execute a aplicação**
```bash
flask run
```

## 🔧 Configuração

### Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto:

```env
# Configurações Flask
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=sua-chave-secreta-aqui

# Banco de Dados
DATABASE_URL=sqlite:///app.db

# Google AI
GOOGLE_AI_API_KEY=sua-chave-api-gemini

# Configurações de Upload
MAX_CONTENT_LENGTH=104857600  # 100MB
UPLOAD_FOLDER=uploads
PROCESSED_FOLDER=processed

# Redis (opcional)
REDIS_URL=redis://localhost:6379/0
```

### Configuração do Google Gemini

1. Acesse [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Crie uma nova API key
3. Adicione a chave no arquivo `.env`

### Instalação do Tesseract OCR

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr tesseract-ocr-por
```

**Windows:**
1. Baixe o instalador: [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki)
2. Execute o instalador
3. Adicione ao PATH do sistema

**macOS:**
```bash
brew install tesseract
brew install tesseract-lang
```

## 📦 Estrutura do Projeto

```
docmaster-pro/
├── app.py                 # Aplicação principal
├── config.py              # Configurações
├── run.py                 # Instalador automático
├── requirements.txt       # Dependências
├── README.md              # Documentação
├── .env.example           # Exemplo de configuração
├── static/                # Arquivos estáticos
│   ├── css/               # Estilos CSS
│   ├── js/                # Scripts JavaScript
│   └── images/            # Imagens e ícones
├── templates/             # Templates HTML
│   ├── base.html          # Template base
│   ├── index.html         # Página inicial
│   ├── upload.html        # Upload de arquivos
│   ├── converter.html     # Conversor
│   ├── analyzer.html      # Analisador
│   └── ...                # Outros templates
├── utils/                 # Utilitários
│   ├── security.py        # Funções de segurança
│   ├── file_converter.py  # Conversão de arquivos
│   ├── pdf_analyzer.py    # Análise de PDFs
│   └── ai_integration.py  # Integração com IA
├── uploads/               # Arquivos enviados
├── processed/             # Arquivos processados
└── tests/                 # Testes automatizados
```

## 🔌 API REST

### Endpoints Principais

#### Upload de Arquivos
```http
POST /api/upload
Content-Type: multipart/form-data

Response:
{
    "success": true,
    "files": [
        {
            "id": 1,
            "filename": "document.pdf",
            "size": 1048576
        }
    ]
}
```

#### Análise com IA
```http
POST /api/analyze
Content-Type: application/json

{
    "file_id": 1,
    "options": {
        "summarize": true,
        "sentiment": true,
        "keywords": true
    }
}

Response:
{
    "success": true,
    "analysis": {
        "summary": "...",
        "sentiment": {
            "score": 0.8,
            "label": "positive"
        },
        "keywords": ["..."]
    }
}
```

#### Conversão de Arquivos
```http
POST /api/convert
Content-Type: application/json

{
    "file_id": 1,
    "output_format": "docx"
}

Response:
{
    "success": true,
    "download_url": "/download/2"
}
```

### Documentação Completa da API

Para documentação completa da API, acesse `/api/docs` após iniciar o servidor.

## 🛡️ Segurança

- **Validação de Arquivos**: Verificação rigorosa de tipos e tamanhos
- **Sanitização**: Prevenção de ataques de directory traversal e XSS
- **Rate Limiting**: Proteção contra abuso de API
- **CORS**: Configuração segura de cross-origin requests
- **Criptografia**: Suporte a arquivos protegidos por senha
- **Auditoria**: Logs completos de todas as operações

## 🚀 Deploy

### Docker

```bash
# Build
docker build -t docmaster-pro .

# Run
docker run -p 8000:8000 docmaster-pro
```

### Docker Compose

```bash
docker-compose up -d
```

### Heroku

```bash
heroku create docmaster-pro
heroku config:set GOOGLE_AI_API_KEY=sua-chave
git push heroku main
```

### Gunicorn (Produção)

```bash
gunicorn --workers 4 --bind 0.0.0.0:8000 app:app
```

## 🧪 Testes

### Executar Testes

```bash
# Todos os testes
pytest

# Com cobertura
pytest --cov=app

# Testes específicos
pytest tests/test_security.py
```

### Testes de Integração

```bash
pytest tests/integration/
```

## 📊 Monitoramento

### Métricas

O sistema inclui métricas de:
- Uso de CPU e memória
- Tempo de resposta das APIs
- Taxa de conversão de arquivos
- Erros e exceções

### Logs

```bash
# Visualizar logs
tail -f app.log

# Logs de erro
grep ERROR app.log
```

## 🔄 Atualizações

### Atualizar Dependências

```bash
pip install --upgrade -r requirements.txt
```

### Migração de Banco de Dados

```bash
flask db upgrade
```

## 🤝 Contribuindo

1. Fork o projeto
2. Crie sua branch (`git checkout -b feature/NovaFuncionalidade`)
3. Commit suas mudanças (`git commit -m 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/NovaFuncionalidade`)
5. Abra um Pull Request

### Diretrizes de Contribuição

- Siga o estilo de código PEP 8
- Adicione testes para novas funcionalidades
- Atualize a documentação conforme necessário
- Mantenha mensagens de commit claras e descritivas

## 📝 Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 👥 Autores

- **Seu Nome** - *Desenvolvimento inicial* - [seu-github](https://github.com/seu-usuario)

## 🙏 Agradecimentos

- Google pela API Gemini
- Comunidade Flask
- Contribuidores do projeto
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract)
- [PyPDF2](https://github.com/py-pdf/pypdf)

## 📞 Suporte

- **Email**: suporte@docmaster.com
- **Issues**: [GitHub Issues](https://github.com/seu-usuario/docmaster-pro/issues)
- **Documentação**: [Wiki](https://github.com/seu-usuario/docmaster-pro/wiki)

## 🗺️ Roadmap

- [ ] Suporte a mais idiomas no OCR
- [ ] Integração com serviços de nuvem
- [ ] App mobile
- [ ] API para terceiros
- [ ] Machine Learning personalizado
- [ ] Suporte a assinatura eletrônica avançada

---

<p align="center">
  Feito com ❤️ pela equipe LTD
</p>