# Portal de Tecnologia da Prefeitura - LTD Estácio

![Banner do Projeto](https://via.placeholder.com/1200x300/0056b3/ffffff?text=Portal+de+Tecnologia+LTD+Est%C3%A1cio)

Um portal web moderno para disponibilização de aplicativos e recursos tecnológicos desenvolvidos pelo Laboratório de Tecnologia e Desenvolvimento (LTD) da Estácio em parceria com as Prefeituras de São José e Florianópolis.

## 📋 Índice

- [Visão Geral](#visão-geral)
- [Tecnologias Utilizadas](#tecnologias-utilizadas)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Requisitos](#requisitos)
- [Instalação e Configuração](#instalação-e-configuração)
- [Desenvolvimento Local](#desenvolvimento-local)
- [API e Endpoints](#api-e-endpoints)
- [Sistema de Download](#sistema-de-download)
- [Deploy](#deploy)
- [Manutenção](#manutenção)
- [Contribuições](#contribuições)
- [Licença](#licença)

## 🔍 Visão Geral

O Portal de Tecnologia da Prefeitura é uma plataforma web desenvolvida para facilitar o acesso aos aplicativos e recursos tecnológicos criados pelos estudantes dos cursos de Sistemas de Informação e Engenharia de Software da Estácio em parceria com as prefeituras locais. O portal permite que os funcionários municipais baixem ferramentas executáveis, consultem guias e acessem recursos de segurança da informação.

### Principais Funcionalidades

- Download de aplicativos executáveis compatíveis com diferentes sistemas operacionais (Windows, macOS, Linux)
- Filtragem e busca de recursos por categoria (Segurança, Produtividade, Treinamento, IA)
- Visualização detalhada das especificações de cada aplicativo
- Registro e monitoramento de downloads
- Interface responsiva para acesso em diferentes dispositivos

## 🔧 Tecnologias Utilizadas

- **Frontend**:
  - HTML5, CSS3, JavaScript (ES6+)
  - Responsividade com Media Queries
  - Font Awesome para ícones
  
- **Backend**:
  - Node.js
  - Express.js
  - API RESTful
  
- **Infraestrutura**:
  - Vercel para hospedagem
  - Serverless Functions

## 📂 Estrutura do Projeto

```
/
├── api/                          # API Serverless para Vercel
│   ├── download.js               # Endpoint para download de aplicativos
│   └── list.js                   # Endpoint para listar aplicativos disponíveis
├── public/                       # Arquivos estáticos
│   ├── css/                      # Estilos CSS
│   │   ├── styles.css            # Estilos principais
│   │   └── apps.css              # Estilos da seção de aplicativos
│   ├── js/                       # Scripts JavaScript
│   │   └── main.js               # Funcionalidades principais do site
│   └── images/                   # Imagens do site
├── dist/                         # Arquivos de distribuição
│   └── images/                   # Imagens processadas
│       └── ltd.png               # Logo do Laboratório
├── apps/                         # Diretório para armazenar aplicativos
├── logs/                         # Registros de downloads e eventos
├── index.html                    # Página principal do portal
├── server.js                     # Servidor Express para desenvolvimento local
├── vercel.json                   # Configuração para deploy na Vercel
├── .gitignore                    # Arquivos e diretórios ignorados pelo Git
└── README.md                     # Documentação do projeto
```

## 📋 Requisitos

- Node.js (versão 14.x ou superior)
- NPM (versão 6.x ou superior)
- Conta na Vercel (para deploy em produção)

## 🚀 Instalação e Configuração

### 1. Clone o repositório

```bash
git clone https://github.com/LTD-2025-1-Cyber-Security-Project/website-ltd

cd portal-tecnologia-prefeitura
```

### 2. Instale as dependências

```bash
npm install
```

### 3. Configure as variáveis de ambiente (se necessário)

Crie um arquivo `.env` na raiz do projeto com as seguintes variáveis:

```
PORT=3000
NODE_ENV=development
```

### 4. Crie os diretórios necessários (caso não existam)

```bash
mkdir -p dist/images public/css public/js apps logs
```

## 💻 Desenvolvimento Local

### Iniciar o servidor de desenvolvimento

```bash
node server.js
```

O servidor estará disponível em `http://localhost:3000`

### Estrutura dos Aplicativos

Os aplicativos são gerenciados pelo banco de dados simulado no arquivo `server.js`. Para adicionar um novo aplicativo, adicione suas informações ao objeto `appDatabase`:

```javascript
// Exemplo de adição de um novo aplicativo
appDatabase["novo-aplicativo"] = {
    title: "Nome do Novo Aplicativo",
    version: "v1.0.0",
    size: "25 MB",
    developer: "Equipe Responsável - LTD Estácio",
    date: "01/01/2025",
    category: "Categoria Principal, Categoria Secundária",
    requirements: "Windows 10/11, macOS, Linux, 4GB RAM, 50MB espaço livre",
    description: "Descrição completa do aplicativo e suas funcionalidades."
};
```

## 🔌 API e Endpoints

### Endpoints Disponíveis

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/api/apps` | GET | Lista todos os aplicativos disponíveis |
| `/api/apps/info/:appName` | GET | Retorna detalhes de um aplicativo específico |
| `/apps/:appName` | GET | Inicia o download de um aplicativo específico |

### Formato de Resposta da API

```json
{
  "success": true,
  "count": 13,
  "platform": "windows",
  "apps": [
    {
      "id": "neuraai-assistant",
      "title": "neuraai-assistant",
      "version": "v2.1.0",
      "size": "45 MB",
      "category": "ia produtividade",
      "description": "Assistente virtual baseado em inteligência artificial para atendimento ao cidadão e suporte aos servidores municipais.",
      "downloadName": "neuraai-assistant.exe",
      "os": "windows"
    },
    // ... outros aplicativos
  ]
}
```

## 📥 Sistema de Download

O sistema de download foi projetado para fornecer a melhor experiência de usuário em diferentes sistemas operacionais:

### Detecção de Sistema Operacional

O sistema detecta automaticamente o sistema operacional do usuário através do User-Agent e adapta os nomes dos arquivos de acordo:

- **Windows**: Adiciona a extensão `.exe` aos arquivos para download (ex: `neuraai-assistant.exe`)
- **macOS e Linux**: Mantém os nomes dos arquivos sem extensão específica (ex: `neuraai-assistant`)

### Registro de Downloads

Todos os downloads são registrados no diretório `logs/` com as seguintes informações:
- Nome do aplicativo baixado
- Endereço IP do usuário
- Timestamp do download
- User-Agent do navegador
- Sistema operacional detectado

### Personalização do Sistema de Download

Para modificar o comportamento do sistema de download, edite os seguintes arquivos:

- `api/download.js`: Lógica de download para ambiente Vercel
- `server.js`: Rota `/apps/:appName` para ambiente de desenvolvimento local

## 🚢 Deploy

### Deploy na Vercel

1. Instale a CLI da Vercel:

```bash
npm install -g vercel
```

2. Faça login na sua conta Vercel:

```bash
vercel login
```

3. Execute o comando de deploy:

```bash
vercel
```

4. Para ambientes de produção:

```bash
vercel --prod
```

### Configuração da Vercel

O arquivo `vercel.json` contém as configurações necessárias para o deploy na Vercel, incluindo:

- Configuração de builds para arquivos estáticos e funções serverless
- Rotas para API e recursos estáticos
- Redirecionamentos para endpoints de download

## 🔄 Manutenção

### Adicionar Novos Aplicativos

1. Adicione os detalhes do aplicativo ao objeto `appDatabase` no arquivo `server.js`
2. Crie uma imagem de miniatura para o aplicativo no diretório `public/images/apps/`
3. Atualize a lista de categorias, se necessário

### Atualizar Aplicativos Existentes

Para atualizar um aplicativo existente, atualize suas informações no objeto `appDatabase` no arquivo `server.js`:

```javascript
appDatabase["aplicativo-existente"].version = "v2.0.0";
appDatabase["aplicativo-existente"].date = "01/01/2025";
// Outras atualizações conforme necessário
```

### Monitoramento de Logs

Os logs de download são armazenados em `logs/downloads.log`. Em ambiente de produção, considere integrar com um serviço de logging como:

- Papertrail
- Loggly
- New Relic
- DataDog

## 🤝 Contribuições

### Fluxo de Trabalho para Contribuições

1. Faça um fork do repositório
2. Crie uma branch para sua feature (`git checkout -b feature/nova-funcionalidade`)
3. Faça commit das suas alterações (`git commit -m 'Adiciona nova funcionalidade'`)
4. Faça push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

### Padrões de Código

- Utilize 2 espaços para indentação
- Siga o padrão camelCase para nomes de variáveis e funções
- Documente todas as funções e APIs

## 📄 Licença

Este projeto está licenciado sob a [Licença MIT](LICENSE) - veja o arquivo LICENSE para detalhes.

---

## 👥 Equipe

Desenvolvido pelo Laboratório de Tecnologia e Desenvolvimento (LTD) da Estácio em parceria com as Prefeituras de São José e Florianópolis.

## 📞 Contato

Para mais informações, entre em contato pelo email: ltd@estacio.edu.br
