# DocMaster Pro - Sistema Inteligente de Processamento de Documentos

![DocMaster Pro](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.9+-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Build Status](https://img.shields.io/badge/build-passing-green.svg)
![Flask](https://img.shields.io/badge/flask-3.0.0-blue.svg)
![Google AI](https://img.shields.io/badge/Google%20Gemini-API-orange.svg)

<p align="center">
  <img src="static/images/logo.png" alt="DocMaster Pro Logo" width="200"/>
</p>

## 📋 Sobre o Projeto

![alt text](images/sistema.png)

DocMaster Pro é uma solução completa e profissional para manipulação, conversão e análise inteligente de documentos. Desenvolvido com Flask e integrado com a API Google Gemini, o sistema oferece uma experiência poderosa para processamento avançado de PDFs, OCR, análise de texto com IA e ferramentas de segurança de documentos.

Ideal para profissionais que trabalham com grande volume de documentos, escritórios de advocacia, departamentos administrativos, e qualquer pessoa que precise extrair informações, converter formatos ou proteger arquivos.

### ✨ Principais Características

- 🤖 **Análise Inteligente com IA**: Resumos automáticos, extração de pontos-chave, análise de sentimento e tópicos principais usando Google Gemini
- 🔄 **Conversor Universal**: Conversão perfeita entre PDF, Word, Excel, imagens e mais de 100 formatos
- 👁️ **OCR Avançado**: Extração de texto de imagens e documentos escaneados com alta precisão
- 🛠️ **Ferramentas PDF Completas**: Merge, split, compressão, rotação, extração de páginas e muito mais
- 🔒 **Segurança Empresarial**: Proteção com senha, marca d'água personalizada e assinatura digital
- 📊 **Interface Responsiva**: Design moderno e adaptável a qualquer dispositivo
- ⚡ **Processamento Otimizado**: Manipulação eficiente de arquivos grandes e processamento em lote

## 🚀 Início Rápido

### Pré-requisitos

- Python 3.9 ou superior
- pip (gerenciador de pacotes Python)
- Tesseract OCR (para reconhecimento óptico de caracteres)
- Poppler Utils (para manipulação avançada de PDFs)
- Redis (opcional, para processamento assíncrono)

### Instalação Automática

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
- Criar um ambiente virtual Python
- Instalar todas as dependências necessárias
- Instalar Tesseract OCR e outras dependências do sistema (se possível)
- Configurar as variáveis de ambiente
- Criar diretórios necessários para uploads e processamento
- Inicializar o banco de dados SQLite (ou PostgreSQL se configurado)
- Abrir o navegador automaticamente na aplicação

### Instalação Manual

Se preferir instalar manualmente, siga estes passos:

1. **Crie um ambiente virtual**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

2. **Instale as dependências Python**
```bash
pip install -r requirements.txt
```

3. **Instale as dependências do sistema**

Para **Ubuntu/Debian**:
```bash
sudo apt-get update
sudo apt-get install -y tesseract-ocr tesseract-ocr-por tesseract-ocr-eng poppler-utils
```

Para **macOS** (usando Homebrew):
```bash
brew install tesseract
brew install tesseract-lang  # Para idiomas adicionais
brew install poppler
```

Para **Windows**:
- Tesseract OCR: [Baixe o instalador](https://github.com/UB-Mannheim/tesseract/wiki)
- Poppler: [Download do binário Windows](https://github.com/oschwartz10612/poppler-windows/releases)

4. **Configure o ambiente**
```bash
cp .env.example .env
# Edite o arquivo .env com suas configurações
```

5. **Inicialize o banco de dados**
```bash
export FLASK_APP=app.py  # Linux/Mac
set FLASK_APP=app.py     # Windows
flask init-db
```

6. **Execute o servidor de desenvolvimento**
```bash
flask run
```

O sistema estará disponível em `http://127.0.0.1:5000/`

## 📦 Distribuição e Deployment

### Criação de Executável

Para criar uma versão executável standalone do DocMaster Pro:

```bash
python run.py --create-exe
```

Este comando:
- Instala o PyInstaller automaticamente (se necessário)
- Cria um único arquivo executável com todas as dependências
- Inclui todos os arquivos estáticos, templates e recursos necessários
- Gera um executável em `dist/DocMaster` pronto para distribuição

O executável pode ser distribuído para usuários finais sem necessidade de instalar Python ou outras dependências. Basta clicar duas vezes no arquivo para iniciar a aplicação.

#### Vantagens do Executável

- **Facilidade de uso**: Não requer conhecimentos técnicos
- **Portabilidade**: Funciona em qualquer máquina compatível com o sistema operacional
- **Tudo incluso**: Contém todas as dependências e arquivos necessários
- **Sem instalação**: Não requer permissões de administrador

### Criação de Pacote Distribuível

Para criar um pacote completo do DocMaster Pro:

```bash
python run.py --package
```

O pacote distribuível é criado como um arquivo ZIP (`DocMaster_Package.zip`) contendo:

- Todo o código-fonte organizado na estrutura de diretórios original
- Scripts de instalação para diferentes sistemas operacionais
- Documentação completa e instruções de uso
- Arquivo `.env.example` para configuração
- Scripts auxiliares para facilitar a execução

#### Como Usar o Pacote Distribuível

1. **Extraia o arquivo ZIP**:
```bash
unzip DocMaster_Package.zip -d DocMaster
cd DocMaster
```

2. **Execute o script de instalação**:
```bash
python run.py
```

#### Casos de Uso do Pacote Distribuível

- **Desenvolvimento personalizado**: Para equipes que desejam modificar o código
- **Instalação em servidores**: Para implantação em ambientes de produção
- **Integração com sistemas existentes**: Permite adaptações e personalizações
- **Distribuição para desenvolvedores**: Facilita o compartilhamento de código

### Deployment em Produção

#### Docker

O projeto inclui arquivos Docker para fácil deployment:

```bash
# Construir a imagem
docker build -t docmaster-pro .

# Executar o contêiner
docker run -d -p 8000:8000 --name docmaster docmaster-pro
```

#### Docker Compose (Recomendado)

Para uma configuração completa com PostgreSQL e Redis:

```bash
docker-compose up -d
```

Isso iniciará:
- Servidor web DocMaster
- Banco de dados PostgreSQL
- Redis para cache e tarefas assíncronas
- Nginx como proxy reverso (opcional)

#### Gunicorn (Servidor de Produção)

Para ambientes de produção sem Docker:

```bash
pip install gunicorn
gunicorn --workers 4 --bind 0.0.0.0:8000 app:app
```

Considerações para produção:
- Use um servidor de produção como Gunicorn ou uWSGI
- Configure um proxy reverso (Nginx ou Apache)
- Use HTTPS para comunicações seguras
- Configure backups regulares do banco de dados
- Ajuste o número de workers com base no hardware disponível

## 🔧 Configuração Avançada

### Variáveis de Ambiente

O arquivo `.env` controla todas as configurações principais:

```env
# Configurações Básicas
FLASK_APP=app.py
FLASK_ENV=production  # development para debugging
SECRET_KEY=sua-chave-super-secreta-aqui

# Banco de Dados
DATABASE_URL=sqlite:///app.db  # PostgreSQL: postgresql://usuario:senha@localhost:5432/docmaster

# Google Gemini API
GOOGLE_AI_API_KEY=sua-chave-api-gemini

# Configurações de Upload
MAX_CONTENT_LENGTH=104857600  # 100MB em bytes
UPLOAD_FOLDER=uploads
PROCESSED_FOLDER=processed

# OCR
TESSERACT_CMD=/usr/bin/tesseract  # Caminho para o executável do Tesseract
OCR_LANGUAGE=por+eng  # Idiomas suportados pelo OCR

# Segurança
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
PERMANENT_SESSION_LIFETIME=86400  # 24 horas em segundos

# Processamento Assíncrono (opcional)
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### Configuração do Banco de Dados

#### SQLite (padrão, para desenvolvimento)
```env
DATABASE_URL=sqlite:///app.db
```

#### PostgreSQL (recomendado para produção)
```env
DATABASE_URL=postgresql://usuario:senha@localhost:5432/docmaster
```

Criação do banco PostgreSQL:
```bash
sudo -u postgres psql
postgres=# CREATE DATABASE docmaster;
postgres=# CREATE USER docmaster WITH PASSWORD 'senha';
postgres=# GRANT ALL PRIVILEGES ON DATABASE docmaster TO docmaster;
```

#### MySQL
```env
DATABASE_URL=mysql+pymysql://usuario:senha@localhost/docmaster
```

### Configuração do OCR

Para otimizar o reconhecimento óptico de caracteres:

1. **Idiomas adicionais**:
```env
OCR_LANGUAGE=por+eng+spa+fra  # Português, Inglês, Espanhol, Francês
```

2. **Ajuste de precisão**:
```env
OCR_DPI=300  # Resolução em DPI para a conversão
OCR_PSM=6    # Page Segmentation Mode (3 para texto completo, 6 para bloco uniforme)
```

3. **Pré-processamento de imagem**:
```env
OCR_ENHANCE_IMAGE=True  # Melhorar contraste e nitidez
OCR_THRESHOLD=True      # Aplicar threshold para melhor detecção
```

### Configuração Avançada da API Gemini

Para controlar o comportamento da IA:

```env
GEMINI_MODEL=gemini-pro          # Modelo a ser usado
GEMINI_TEMPERATURE=0.2           # Controle de criatividade (0.0-1.0)
GEMINI_MAX_OUTPUT_TOKENS=1024    # Limite de tokens na resposta
GEMINI_TOP_K=40                  # Filtro top-k para sampling
GEMINI_TOP_P=0.95                # Filtro top-p (nucleus sampling)
```

### Agendamento de Tarefas

Configure tarefas automáticas usando Celery:

```python
# Em app.py ou em um arquivo celery_tasks.py
@celery.task
def cleanup_old_files():
    """Remove arquivos temporários com mais de 24 horas"""
    SecurityManager.cleanup_old_files(app.config['UPLOAD_FOLDER'], 24)
    SecurityManager.cleanup_old_files(app.config['PROCESSED_FOLDER'], 24)

# Agendamento
celery.conf.beat_schedule = {
    'cleanup-every-hour': {
        'task': 'app.cleanup_old_files',
        'schedule': 3600.0,  # segundos
    }
}
```

## 📚 Funcionalidades Detalhadas

### 1. Upload e Gerenciamento de Arquivos

- **Upload multi-arquivo**: Arraste e solte múltiplos arquivos simultaneamente
- **Validação de segurança**: Verificação de extensões, tamanho e tipo de arquivo
- **Categorização**: Organize seus documentos em categorias
- **Tags**: Adicione tags para facilitar a pesquisa
- **Histórico de uploads**: Visualize seus uploads recentes
- **Controle de armazenamento**: Monitore o espaço usado

### 2. Conversão Universal de Arquivos

Conversões suportadas:
- PDF ↔ Word/DOCX (com preservação de formatação)
- PDF ↔ TXT (extração de texto)
- Imagens → PDF (JPG, PNG, TIFF)
- Excel/CSV → PDF (com formatação de tabelas)
- PowerPoint → PDF
- Combinações de múltiplos arquivos

Características:
- Preservação precisa de formatação
- Opções de qualidade ajustáveis
- Conversão em lote de múltiplos arquivos
- Compressão inteligente para reduzir tamanho

### 3. Análise com IA (Google Gemini)

Recursos analíticos:
- **Resumo executivo**: Sintetiza documentos longos
- **Pontos-chave**: Identifica informações cruciais
- **Análise de sentimento**: Detecta o tom emocional do texto
- **Tópicos principais**: Extrai os temas abordados
- **Palavras-chave**: Identifica termos importantes
- **Entidades nomeadas**: Reconhece pessoas, locais, organizações
- **Itens de ação**: Identifica tarefas mencionadas

Visualizações:
- Gráficos de sentimento
- Nuvem de palavras-chave
- Lista organizada de pontos-chave
- Relatórios exportáveis em PDF, DOCX e JSON

### 4. OCR Avançado

Capacidades:
- Extração de texto de imagens escaneadas
- Reconhecimento de PDFs digitalizados
- Suporte a múltiplos idiomas
- Detecção de orientação automática
- Melhoria de qualidade de imagem
- Correção de perspectiva
- Preservação de layout em tabelas

Tecnologias:
- Tesseract OCR para reconhecimento de caracteres
- Algoritmos de pré-processamento de imagem
- Correção ortográfica pós-processamento

### 5. Ferramentas PDF

#### Edição Básica
- Mesclar múltiplos PDFs
- Dividir PDFs por página
- Extrair páginas específicas
- Rotação de páginas
- Reordenação de páginas

#### Compressão
- Compressão de PDFs com níveis ajustáveis
- Otimização de imagens embutidas
- Redimensionamento inteligente
- Remoção de elementos desnecessários

#### Anotação
- Adição de marcadores
- Destaque de texto
- Comentários e notas
- Desenho a mão livre

### 6. Segurança de Documentos

- **Proteção com senha**: Criptografia AES-256
- **Marca d'água**: Personalização de texto, posição e transparência
- **Assinatura digital**: Certificados e verificação
- **Restrições**: Controle de impressão, cópia e edição
- **Redação**: Ocultar informações sensíveis

## 🧪 Testes e Garantia de Qualidade

### Executando Testes

```bash
# Instale as dependências de teste
pip install pytest pytest-cov

# Execute todos os testes
pytest

# Testes com cobertura
pytest --cov=app tests/
```

### Relatório de Cobertura

Para gerar um relatório de cobertura HTML:

```bash
pytest --cov=app --cov-report=html tests/
# Acesse htmlcov/index.html
```

### Testes de Integração

```bash
# Testes específicos
pytest tests/test_pdf_analyzer.py
```

## 📱 API REST

O DocMaster Pro fornece uma API REST completa:

### Autenticação

```bash
# Obter token (quando a autenticação estiver habilitada)
curl -X POST -H "Content-Type: application/json" \
     -d '{"username":"admin","password":"senha"}' \
     http://localhost:5000/api/auth/token
```

### Upload de Arquivos

```bash
curl -X POST -F "files=@documento.pdf" \
     -F "category=legal" \
     http://localhost:5000/api/upload
```

### Conversão de Arquivos

```bash
curl -X POST -H "Content-Type: application/json" \
     -d '{"file_id":1,"output_format":"docx"}' \
     http://localhost:5000/api/convert
```

### Análise com IA

```bash
curl -X POST -H "Content-Type: application/json" \
     -d '{"file_id":1,"options":{"summarize":true,"sentiment":true}}' \
     http://localhost:5000/api/analyze
```

### OCR

```bash
curl -X POST -H "Content-Type: application/json" \
     -d '{"file_id":1,"language":"por+eng"}' \
     http://localhost:5000/api/ocr
```

### Ferramentas PDF

```bash
# Mesclar PDFs
curl -X POST -H "Content-Type: application/json" \
     -d '{"file_ids":[1,2,3]}' \
     http://localhost:5000/api/merge-pdfs
```

## 📄 Documentação Técnica - run.py

### Visão Geral

O script `run.py` é o componente central do DocMaster Pro, funcionando como um instalador automatizado, configurador e executor da aplicação. Ele simplifica drasticamente o processo de instalação, configuração e distribuição do sistema, proporcionando uma experiência otimizada para usuários finais e desenvolvedores.

### Principais Recursos

1. **Instalação Automatizada Completa**
   - Verificação e validação do ambiente
   - Criação e configuração de ambiente virtual Python
   - Instalação inteligente de dependências
   - Configuração de variáveis de ambiente
   - Inicialização do banco de dados

2. **Suporte Multi-plataforma**
   - Adaptação automática a Windows, macOS e Linux
   - Detecção e instalação de dependências específicas do sistema
   - Geração de atalhos apropriados para cada sistema
   - Paths compatíveis com o sistema operacional

3. **Geração de Executáveis Standalone**
   - Criação de aplicações distribuíveis com PyInstaller
   - Empacotamento automático de recursos estáticos
   - Resolução de dependências para compilação
   - Configuração adaptativa de spec files

4. **Ferramentas de Distribuição**
   - Criação de pacotes completos para distribuição
   - Backup de arquivos críticos
   - Estruturação de diretórios para deployment
   - Geração de documentação integrada

5. **Infraestrutura de Logging**
   - Sistema de log detalhado para troubleshooting
   - Rastreamento do progresso de instalação
   - Captura e tratamento de erros
   - Relatórios formatados para fácil leitura

### Arquitetura

O script é estruturado em torno da classe `DocMasterInstaller`, que encapsula toda a lógica necessária para configurar, instalar e executar o sistema. Esta abordagem orientada a objetos facilita a manutenção, extensão e teste do código.

```
DocMasterInstaller
├── Métodos de Configuração
│   ├── setup_environment()
│   ├── create_directories()
│   └── ensure_icon_exists()
├── Métodos de Instalação
│   ├── create_virtual_environment()
│   ├── install_dependencies()
│   └── install_system_dependencies()
├── Métodos de Inicialização
│   ├── initialize_database()
│   └── create_shortcuts()
├── Métodos de Execução
│   ├── run_application()
│   ├── find_available_port()
│   └── check_port_availability()
└── Métodos de Distribuição
    ├── create_executable()
    └── create_package()
```

### Fluxo de Execução

#### Iniciação
1. Verificação da versão do Python
2. Detecção do sistema operacional
3. Configuração de logging
4. Exibição do banner inicial

#### Processo de Instalação
1. Criação do ambiente virtual
2. Instalação de dependências Python via pip
3. Instalação de dependências do sistema (Tesseract OCR, Poppler)
4. Configuração do arquivo .env
5. Criação dos diretórios necessários
6. Inicialização do banco de dados
7. Criação de atalhos para execução fácil

#### Execução da Aplicação
1. Identificação de uma porta disponível
2. Configuração das variáveis de ambiente
3. Abertura do navegador
4. Inicialização do servidor Flask

#### Criação de Executável
1. Instalação do PyInstaller
2. Verificação e criação de recursos necessários (ícones)
3. Geração dinâmica do spec file
4. Compilação do executável standalone

#### Empacotamento
1. Criação de diretório temporário
2. Cópia dos arquivos do projeto
3. Geração do arquivo ZIP
4. Documentação do pacote distribuível

### Parâmetros da Linha de Comando

O script aceita os seguintes parâmetros:

- **Sem parâmetros**: Instala e executa o sistema
- **--create-exe**: Cria executável standalone
- **--package**: Cria pacote distribuível
- **--help**: Exibe ajuda sobre opções disponíveis

### Exemplos de Uso

#### Instalação e Execução Básica
```bash
python run.py
```

#### Criação de Executável
```bash
python run.py --create-exe
```

#### Criação de Pacote Distribuível
```bash
python run.py --package
```

### Considerações Técnicas

#### Compatibilidade
- **Python**: Versão 3.9+ requerida
- **Sistemas Operacionais**: Windows, macOS, Linux
- **Navegadores**: Chrome, Firefox, Safari, Edge

#### Dependências Principais
- **venv**: Criação de ambientes virtuais
- **subprocess**: Execução de comandos externos
- **webbrowser**: Abertura automática do navegador
- **PIL** (opcional): Para criação de ícones

## 💡 Dicas e Troubleshooting

### Dicas de Desempenho

1. **Otimização de upload**:
   - Recomende aos usuários compactar arquivos grandes antes do upload
   - Use PDFs compactados quando possível
   - Para grandes volumes, divida em lotes menores

2. **Configuração de Redis**:
   - Ative Redis para melhorar performance e permitir processamento assíncrono
   - Configure para persistir dados em disco: `appendonly yes`

3. **Ajustes de PostgreSQL**:
   - Para grandes volumes: `max_connections = 200`
   - Aumente `shared_buffers` para aprox. 25% da RAM disponível
   - Ajuste `work_mem` para operações complexas

### Solução de Problemas Comuns

1. **Erro de OCR**:
   ```
   tesseract not found
   ```
   Solução: Verifique se o Tesseract está instalado e configure o caminho em `.env`:
   ```
   TESSERACT_CMD=/caminho/completo/para/tesseract
   ```

2. **Falha na conversão PDF → DOCX**:
   - Verifique se todas as dependências estão instaladas
   - Para PDFs complexos, use a opção de OCR antes da conversão
   - Aumente o timeout para arquivos grandes

3. **Erros de memória em arquivos grandes**:
   - Ajuste `MAX_CONTENT_LENGTH` para permitir arquivos maiores
   - Configure processamento em lote para PDFs grandes
   - Use Celery para processamento assíncrono

4. **API Gemini não responde**:
   - Verifique a chave API em `.env`
   - Confirme que a API não está em rate limit
   - Use o analisador offline como fallback

5. **Executável não inicia**:
   - Verifique se todas as DLLs necessárias estão presentes
   - Execute em modo de compatibilidade
   - Verifique logs de erro em `logs/app.log`

## 🚀 Road Map

### Próximas Versões

#### v1.1.0
- Autenticação de usuários e controle de acesso
- Dashboard administrativo avançado
- Integração com Microsoft Office 365
- Extensão para Chrome/Firefox

#### v1.2.0
- API REST completa com documentação Swagger
- SDK Python para desenvolvedores
- Aplicativo mobile para iOS e Android
- Integrações com mais serviços de nuvem

#### v2.0.0
- Reconhecimento facial em documentos
- Assinatura eletrônica avançada
- Blockchain para verificação de autenticidade
- Machine Learning personalizado para classificação de documentos

## 📝 Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 👥 Contribuições

Contribuições são bem-vindas! Veja [CONTRIBUTING.md](CONTRIBUTING.md) para detalhes sobre como contribuir.

1. Fork o projeto
2. Crie sua branch de feature (`git checkout -b feature/NovaFuncionalidade`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/NovaFuncionalidade`)
5. Abra um Pull Request

## 🙏 Agradecimentos

- Google pela API Gemini
- Comunidade Flask
- Contribuidores do Tesseract OCR
- Todos os usuários e colaboradores

---

<p align="center">
  Feito com ❤️ pela equipe LTD
</p>