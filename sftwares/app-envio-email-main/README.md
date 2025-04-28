# Sistema de Envio de E-mails para Prefeituras

![Versão](https://img.shields.io/badge/versão-1.0.0-blue)
![Licença](https://img.shields.io/badge/licença-Proprietária-red)
![Python](https://img.shields.io/badge/Python-3.7+-yellow)

<p align="center">
  <img src="resources/logo_app.png" alt="Logo do Sistema" width="200"/>
</p>

## 📋 Sumário
- [Visão Geral](#-visão-geral)
- [Funcionalidades](#-funcionalidades)
- [Requisitos do Sistema](#-requisitos-do-sistema)
- [Instalação](#-instalação)
  - [Para Usuários Finais](#para-usuários-finais)
  - [Para Desenvolvedores](#para-desenvolvedores)
- [Configuração](#-configuração)
- [Uso do Sistema](#-uso-do-sistema)
- [Organização do Código](#-organização-do-código)
- [Módulos e Componentes](#-módulos-e-componentes)
- [Segurança](#-segurança)
- [Backup e Recuperação](#-backup-e-recuperação)
- [Solução de Problemas](#-solução-de-problemas)
- [Suporte](#-suporte)
- [Licença](#-licença)

## 🌐 Visão Geral

O **Sistema de Envio de E-mails para Prefeituras** é uma aplicação desktop desenvolvida para otimizar e gerenciar a comunicação institucional via e-mail nas prefeituras de São José e Florianópolis. O sistema oferece uma interface intuitiva, robusta e profissional que atende às necessidades específicas de comunicação interna e externa das administrações municipais.

Desenvolvido com Python e Tkinter, o sistema oferece uma solução completa para o gerenciamento de e-mails, incluindo envio individual, em massa, agendamento, templates personalizáveis e relatórios detalhados de entrega.

## ✨ Funcionalidades

### Interface Gráfica
- Design elegante e profissional usando cores institucionais das prefeituras
- Sistema de navegação por abas para separar diferentes funcionalidades
- Responsividade adequada para diferentes tamanhos de tela
- Logos oficiais e identidade visual condizente com órgãos públicos

### Funcionalidades Principais
- **Envio de E-mails Individuais**
  - Formatação avançada com suporte a HTML
  - Anexo de arquivos diversos
  - Histórico completo de envios

- **Envio em Massa**
  - Destinatários por grupos, departamentos ou listas importadas
  - Personalização de mensagens com variáveis como nome, cargo, etc.
  - Controle de taxa de envio para evitar bloqueios de servidor

- **Agendamento de E-mails**
  - Programação de data e hora específicas
  - Suporte a recorrência diária, semanal e mensal
  - Cancelamento e edição de agendamentos

- **Templates Personalizáveis**
  - Criação e gerenciamento de modelos de e-mail
  - Organização por departamento
  - Variáveis de substituição para personalização

- **Gerenciamento de Contatos**
  - Cadastro completo de funcionários
  - Organização por departamentos e grupos
  - Importação e exportação via CSV e Excel

### Configurações Avançadas
- Configurações SMTP para diferentes servidores
- Assinaturas personalizadas por departamento
- Sistema de backup automático
- Múltiplos níveis de permissão de usuários

## 💻 Requisitos do Sistema

### Requisitos de Hardware
- Processador: 1.5 GHz ou superior
- Memória RAM: 4 GB ou superior
- Espaço em disco: 100 MB para a aplicação + espaço para armazenamento de dados
- Resolução de tela recomendada: 1366x768 ou superior

### Requisitos de Software
Para usuários do executável compilado:
- Sistema Operacional: Windows 7/8/10/11
- Conexão com internet (para envio de e-mails)

Para desenvolvedores:
- Python 3.7 ou superior
- Bibliotecas listadas em `requirements.txt`
- Acesso a servidores SMTP para envio de e-mails

## 🔧 Instalação

### Para Usuários Finais

1. Faça o download do arquivo executável do sistema
2. Execute o instalador e siga as instruções na tela
3. Após a instalação, inicie o sistema pelo atalho criado no desktop ou menu iniciar

Ou, alternativamente, para versão portátil:

1. Descompacte o arquivo ZIP em uma pasta de sua escolha
2. Execute o arquivo `Sistema_Email_Prefeituras.exe`
3. Na primeira execução, configure os dados de SMTP e demais informações necessárias

### Para Desenvolvedores

1. Clone o repositório ou baixe o código-fonte
```bash
git clone https://github.com/prefeituras/sistema-email.git
cd sistema-email
```

2. (Opcional) Crie e ative um ambiente virtual:
```bash
python -m venv venv
# No Windows
venv\Scripts\activate
# No Linux/Mac
source venv/bin/activate
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

4. Execute o script de configuração:
```bash
# No Windows
setup.bat
# Ou usando Python
python setup.py
```

5. Para executar o sistema diretamente:
```bash
python run.py
```

6. Para criar um executável:
```bash
pyinstaller --name "Sistema_Email_Prefeituras" --onefile --windowed --icon=resources/icon.ico --add-data "resources;resources" --add-data "templates;templates" --add-data "config;config" run.py
```

## ⚙️ Configuração

### Configurações SMTP

O sistema requer a configuração de servidores SMTP para envio de e-mails. Para cada prefeitura, configure:

1. Endereço do servidor SMTP
2. Porta (geralmente 587 para TLS ou 465 para SSL)
3. Usuário e senha
4. Opções de segurança (TLS/SSL)

Estas configurações são acessíveis pela aba **Configurações** > **SMTP** e são salvas automaticamente.

### Assinaturas

É possível configurar assinaturas padrão para cada prefeitura:

1. Acesse a aba **Configurações** > **Assinaturas**
2. Selecione a prefeitura desejada
3. Edite o modelo HTML da assinatura
4. As variáveis como `{nome}`, `{cargo}`, `{departamento}` serão substituídas pelos dados do usuário

### Backup Automático

O sistema oferece opções de backup automático:

1. Acesse a aba **Configurações** > **Geral**
2. Configure a frequência (diária, semanal, mensal)
3. Defina o horário para execução do backup
4. Especifique o diretório onde os backups serão armazenados

### Configuração de Grupos

Para facilitar o envio de e-mails para equipes específicas:

1. Acesse a aba **Configurações** > **Grupos**
2. Crie novos grupos especificando nome, descrição e prefeitura
3. Adicione membros aos grupos a partir do cadastro de funcionários

## 📝 Uso do Sistema

### Login

Após a instalação, você precisará fazer login com suas credenciais:

1. Selecione a prefeitura (São José ou Florianópolis)
2. Digite seu e-mail e senha
3. Clique em "Entrar"

Para o primeiro acesso, utilize as credenciais de administrador fornecidas pela equipe de TI.

### Envio de E-mail Individual

1. Acesse a aba **E-mail Individual**
2. Selecione ou digite o e-mail do destinatário
3. Preencha o assunto e o conteúdo da mensagem
4. Utilize as ferramentas de formatação para melhorar a aparência
5. Adicione anexos se necessário
6. Clique em "Enviar E-mail"

### Envio em Massa

1. Acesse a aba **E-mail em Massa**
2. Selecione os destinatários por grupo, departamento ou importação
3. Preencha o assunto e conteúdo ou selecione um template
4. Configure opções de envio (limite de e-mails por hora, intervalo entre envios)
5. Clique em "Enviar E-mails"

### Agendamento de E-mails

1. Acesse a aba **Agendamento**
2. Configure os destinatários, assunto e conteúdo
3. Defina a data e hora para o envio
4. Selecione a recorrência se desejado
5. Clique em "Agendar E-mail"

### Gerenciamento de Templates

1. Acesse a aba **Templates**
2. Para criar um novo template, preencha os campos de nome, assunto e conteúdo
3. Insira variáveis como `{nome}` e `{cargo}` para personalização
4. Para editar um template existente, selecione-o na lista e clique em "Editar"

### Gerenciamento de Funcionários

1. Acesse a aba **Funcionários**
2. Para adicionar um novo funcionário, preencha seus dados na parte inferior da tela
3. Para importar funcionários, clique em "Importar CSV/Excel"
4. Para gerenciar grupos, selecione um funcionário e clique em "Adicionar a Grupo"

## 🧱 Organização do Código

O sistema está estruturado da seguinte forma:

```
sistema-email/
│
├── run.py                  # Ponto de entrada do aplicativo
├── sistema_email.py        # Classe principal do sistema
├── setup.py                # Script de instalação
├── setup.bat               # Script de instalação para Windows
├── requirements.txt        # Dependências do projeto
│
├── resources/              # Recursos visuais (logos, ícones)
│   ├── logo_sj.png         # Logo da Prefeitura de São José
│   ├── logo_floripa.png    # Logo da Prefeitura de Florianópolis
│   └── icon.ico            # Ícone do aplicativo
│
├── config/                 # Arquivos de configuração
│   └── config.json         # Configurações do sistema
│
├── templates/              # Templates de e-mail salvos
│
└── backups/                # Diretório de backups
```

## 📦 Módulos e Componentes

O sistema está dividido em várias classes e módulos funcionais:

### Classe Principal (SistemaEmail)
- Responsável pela inicialização do sistema e gerenciamento da interface

### Componentes da Interface
- **InterfaceUtilitários**: Gerencia a criação e interação da interface gráfica
- **GerenciadorAbas**: Responsável pela navegação entre funcionalidades

### Módulos Funcionais
- **GerenciadorEnvio**: Implementa lógica de envio de e-mails
- **GerenciadorAgendamento**: Gerencia e-mails agendados
- **GerenciadorBancoDados**: Controla o acesso ao banco de dados SQLite
- **GerenciadorTemplates**: Administra templates de e-mail
- **GerenciadorFuncionarios**: Controla cadastro e grupos de funcionários
- **GerenciadorBackup**: Implementa backup e restauração de dados

## 🔒 Segurança

O sistema implementa várias medidas de segurança:

- Senhas armazenadas com hash SHA-256
- Conexão segura com servidores SMTP (suporte a TLS/SSL)
- Níveis de permissão para controle de acesso
- Registro de atividades (logs) para auditoria
- Proteção contra injeção SQL

## 💾 Backup e Recuperação

### Backup Automático
O sistema realiza backups automáticos conforme configurado. Os backups incluem:
- Banco de dados completo (cadastros e configurações)
- Arquivos de configuração
- Templates personalizados

### Backup Manual
Para realizar um backup manual:
1. Acesse a aba **Configurações**
2. Clique em "Fazer Backup Agora"
3. O arquivo de backup será salvo no diretório configurado

### Restauração
Para restaurar a partir de um backup:
1. Acesse a aba **Configurações**
2. Clique em "Restaurar Backup"
3. Selecione o arquivo de backup (.zip)
4. Confirme a operação

## ❓ Solução de Problemas

### Falha na Conexão SMTP
- Verifique as configurações do servidor SMTP
- Confirme se a porta está correta (587 para TLS, 465 para SSL)
- Verifique as credenciais de acesso
- Confirme se o servidor permite o tipo de conexão configurada

### Erros no Envio de E-mails
- Verifique se os e-mails dos destinatários estão corretos
- Confirme se há conexão com a internet
- Verifique se há limites de envio no servidor SMTP

### Problemas com o Banco de Dados
- Verifique se o arquivo do banco de dados existe e não está corrompido
- Restaure a partir de um backup recente
- Verifique permissões de escrita no diretório

### Outros Problemas
- Consulte os logs do sistema (aba **Logs**)
- Verifique a existência de atualizações
- Entre em contato com o suporte técnico

## 📞 Suporte

Para obter suporte técnico:

- **E-mail**: suporte@prefeitura.gov.br
- **Telefone**: (48) 3000-0000
- **Horário de atendimento**: Segunda a sexta-feira, das 8h às 18h

Ao solicitar suporte, tenha em mãos:
- Versão do sistema
- Descrição detalhada do problema
- Capturas de tela se possível
- Logs do sistema (exportáveis pela aba Logs)

## 📜 Licença

Este software é propriedade das Prefeituras de São José e Florianópolis.
Todos os direitos reservados.

O uso, distribuição ou modificação deste software sem autorização expressa é estritamente proibido.

© 2025 Prefeituras de São José e Florianópolis