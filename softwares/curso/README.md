# EdTech IA & Cyber - Sistema Educacional

Sistema web educacional completo focado em Inteligência Artificial e Cybersegurança para funcionários das prefeituras de Florianópolis e São José, desenvolvido com Python e Flask.

## Visão Geral

EdTech IA & Cyber é uma plataforma de educação online que visa capacitar funcionários municipais nas áreas de Inteligência Artificial e Cybersegurança. O sistema oferece:

- Trilhas de aprendizado progressivas com diferentes níveis de complexidade
- Sistema de gamificação com níveis de progresso e medalhas
- Quizzes interativos gerados com IA
- Recursos multimídia integrados com YouTube
- Certificação por módulo concluído
- Assistente virtual inteligente para dúvidas

## Arquitetura e Tecnologias

- **Framework**: Flask com arquitetura MVC
- **Frontend**: HTML5, CSS3 (com SASS/SCSS), JavaScript (com Vue.js)
- **Backend**: Python 3.10+
- **Banco de Dados**: PostgreSQL com SQLAlchemy ORM
- **Autenticação**: JWT com níveis de permissão
- **APIs Externas**: Google Gemini (IA), YouTube (vídeos educacionais)

## Requisitos do Sistema

- Python 3.10 ou superior
- PostgreSQL 13 ou superior
- Node.js 16.x ou superior (para compilação de assets)
- Conexão à internet (para APIs externas)
- Chaves de API para Google Gemini e YouTube

## Instalação

### 1. Clone o repositório

```bash
git clone https://github.com/seu-usuario/edtech-ia-cyber.git
cd edtech-ia-cyber
```

### 2. Configure o ambiente virtual

```bash
# Crie um ambiente virtual
python -m venv venv

# Ative o ambiente virtual
## No Windows
venv\Scripts\activate
## No Linux/Mac
source venv/bin/activate

# Instale as dependências
pip install -r requirements.txt
```

### 3. Configure as variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto com as seguintes variáveis:

```
# Configurações gerais
FLASK_APP=app
FLASK_ENV=development
SECRET_KEY=sua-chave-secreta
JWT_SECRET_KEY=sua-chave-jwt-secreta

# Banco de dados
DATABASE_URL=postgresql://usuario:senha@localhost/edtech
DEV_DATABASE_URL=postgresql://usuario:senha@localhost/edtech_dev
TEST_DATABASE_URL=postgresql://usuario:senha@localhost/edtech_test

# APIs externas
GOOGLE_GEMINI_API_KEY=sua-chave-api-gemini
YOUTUBE_API_KEY=sua-chave-api-youtube

# Email
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=seu-email@gmail.com
MAIL_PASSWORD=sua-senha-de-app
MAIL_DEFAULT_SENDER=noreply@edtech-ia-cyber.gov.br

# Base URL
BASE_URL=http://localhost:5000
```

### 4. Configure o banco de dados

```bash
# Crie os bancos de dados
createdb edtech_dev
createdb edtech_test

# Execute as migrações
flask db init
flask db migrate
flask db upgrade
```

### 5. Inicialize o banco de dados com dados de demonstração

```bash
# Inicializa o banco com administrador padrão
flask initialize-db

# Gera dados de demonstração (opcional)
flask generate-demo-data
```

### 6. Execute o servidor de desenvolvimento

```bash
# Inicie o servidor Flask
flask run

# Ou com host e porta específicos
flask run --host=0.0.0.0 --port=5000
```

Acesse a aplicação em [http://localhost:5000](http://localhost:5000)

## Estrutura do Projeto

```
edtech_ia_cyber/
│
├── app/                     # Pacote principal da aplicação
│   ├── __init__.py          # Inicialização da aplicação Flask
│   ├── config.py            # Configurações para diferentes ambientes
│   ├── models/              # Modelos de dados (SQLAlchemy)
│   ├── controllers/         # Controladores de rotas
│   ├── services/            # Serviços externos (APIs)
│   ├── views/               # Templates e assets
│   └── utils/               # Funções utilitárias
│
├── migrations/              # Migrações de banco de dados
├── tests/                   # Testes automatizados
├── .env                     # Variáveis de ambiente (não versionado)
├── .env.example             # Exemplo de arquivo .env
├── requirements.txt         # Dependências Python
└── app.py                   # Ponto de entrada da aplicação
```

## Comandos CLI

O sistema fornece vários comandos para gerenciamento através da interface de linha de comando do Flask:

```bash
# Inicializa o banco de dados com dados básicos
flask initialize-db

# Criar um administrador
flask create-admin EMAIL PASSWORD FIRST_NAME LAST_NAME

# Importar usuários a partir de um CSV
flask import-users ARQUIVO_CSV

# Gerar dados de demonstração
flask generate-demo-data --users=20 --courses=4

# Excluir usuários inativos
flask delete-inactive-users --days=365

# Fazer backup do banco de dados
flask backup-db backup.json

# Restaurar backup do banco de dados
flask restore-db backup.json

# Resetar banco de dados (cuidado!)
flask reset-db
```

## Níveis de Acesso

O sistema possui três níveis de acesso:

1. **Administrador**
   - Acesso completo ao sistema
   - Gerenciamento de usuários e cursos
   - Acesso a relatórios administrativos

2. **Instrutor**
   - Criação e gerenciamento de cursos
   - Criação de quizzes e avaliações
   - Visualização de progresso dos alunos

3. **Aluno**
   - Acesso aos cursos matriculados
   - Realização de avaliações
   - Visualização de progresso pessoal
   - Obtenção de certificados

## Recursos Principais

### Sistema de Autenticação

- Registro e login de usuários
- Autenticação JWT para API
- Recuperação de senha segura
- Perfis de usuário com dados profissionais

### Módulo Educacional

- Trilhas de aprendizado progressivas
- Conteúdo estruturado em módulos e lições
- Sistema de progresso e gamificação
- Recursos multimídia complementares

### Sistema de Avaliação

- Quizzes interativos gerados com IA
- Avaliações de conhecimento dinâmicas
- Análise de desempenho individual
- Recomendações personalizadas de estudo

### Administração

- Dashboard administrativo
- Relatórios de uso e progresso
- Gerenciamento de usuários e cursos
- Configuração de trilhas de aprendizado

## Integrações com IA

O sistema utiliza a API do Google Gemini para implementar vários recursos de IA:

1. **Geração de conteúdo personalizado**
   - Quizzes adaptados ao nível do usuário
   - Exercícios práticos personalizados

2. **Assistente virtual**
   - Resposta a dúvidas sobre o conteúdo
   - Sugestões de recursos adicionais

3. **Recomendações inteligentes**
   - Análise de desempenho e áreas de dificuldade
   - Sugestões de novos cursos baseadas no perfil

4. **Análise de progresso**
   - Identificação de áreas de melhoria
   - Recomendações de estudo personalizadas

## Implantação em Produção

### Requisitos para produção

- Servidor Linux (Ubuntu 20.04+ recomendado)
- Nginx como proxy reverso
- Gunicorn como servidor WSGI
- PostgreSQL para banco de dados
- Redis para cache (opcional, mas recomendado)

### Passos para implantação

1. **Configurar servidor**

```bash
# Instalar dependências do sistema
sudo apt update
sudo apt install python3-pip python3-venv postgresql nginx redis-server
```

2. **Configurar banco de dados PostgreSQL**

```bash
sudo -u postgres createuser -P edtech_user
sudo -u postgres createdb -O edtech_user edtech_prod
```

3. **Clonar e configurar o projeto**

```bash
# Clonar o repositório
git clone https://github.com/seu-usuario/edtech-ia-cyber.git
cd edtech-ia-cyber

# Configurar ambiente virtual
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn  # Servidor WSGI para produção
```

4. **Configurar variáveis de ambiente para produção**

Crie um arquivo `.env` com as configurações de produção.

5. **Configurar Gunicorn**

Crie um arquivo de serviço systemd `/etc/systemd/system/edtech.service`:

```
[Unit]
Description=EdTech IA & Cyber Gunicorn
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/caminho/para/edtech-ia-cyber
Environment="PATH=/caminho/para/edtech-ia-cyber/venv/bin"
EnvironmentFile=/caminho/para/edtech-ia-cyber/.env
ExecStart=/caminho/para/edtech-ia-cyber/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:8000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

6. **Configurar Nginx**

Crie um arquivo de configuração `/etc/nginx/sites-available/edtech`:

```
server {
    listen 80;
    server_name edtech-ia-cyber.gov.br;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /static {
        alias /caminho/para/edtech-ia-cyber/app/static;
    }
}
```

7. **Ativar o site**

```bash
sudo ln -s /etc/nginx/sites-available/edtech /etc/nginx/sites-enabled
sudo systemctl restart nginx
sudo systemctl enable edtech
sudo systemctl start edtech
```

8. **Configurar HTTPS**

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d edtech-ia-cyber.gov.br
```

## Manutenção e Backup

### Backups regulares

```bash
# Fazer backup do banco de dados
flask backup-db backups/backup-$(date +%Y%m%d).json

# Script para backup automático
0 2 * * * cd /caminho/para/edtech-ia-cyber && source venv/bin/activate && flask backup-db backups/backup-$(date +%Y%m%d).json
```

### Atualizações

```bash
# Atualizar o código
git pull

# Atualizar dependências
pip install -r requirements.txt

# Aplicar migrações
flask db upgrade

# Reiniciar serviço
sudo systemctl restart edtech
```

## Problemas Comuns e Soluções

| Problema | Solução |
|----------|---------|
| Erro de conexão com banco de dados | Verifique as credenciais no arquivo .env e se o PostgreSQL está em execução |
| Erro de API do Google Gemini | Verifique se a chave de API é válida e se o limite de requisições não foi atingido |
| Erro de API do YouTube | Verifique a chave de API e o limite de requisições diárias |
| Problemas de envio de email | Verifique as configurações de SMTP e se as credenciais estão corretas |
| Servidor lento | Aumente o número de workers do Gunicorn e verifique recursos do servidor |

## Contribuição

Para contribuir com o projeto:

1. Faça um fork do repositório
2. Crie uma branch para sua feature (`git checkout -b feature/nova-funcionalidade`)
3. Implemente suas mudanças
4. Execute os testes (`pytest`)
5. Faça commit das mudanças (`git commit -am 'Adiciona nova funcionalidade'`)
6. Envie para o GitHub (`git push origin feature/nova-funcionalidade`)
7. Crie um Pull Request

## Licença

Este projeto é licenciado sob a [Licença MIT](LICENSE).

## Contato

Para dúvidas ou sugestões, entre em contato pelo email: contato@ltdestacio.com.br