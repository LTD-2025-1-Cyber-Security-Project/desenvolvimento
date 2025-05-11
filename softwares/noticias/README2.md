# NexusInfo - Sistema de Notícias com IA

![NexusInfo Logo](assets/logo.png)

NexusInfo é um sistema desktop avançado que usa a API Google Gemini para buscar, processar e apresentar notícias sobre tecnologia, cibersegurança, inteligência artificial e Internet das Coisas. Com uma interface gráfica moderna e funcionalidades completas de gerenciamento de usuários, o NexusInfo representa uma solução profissional para consumo personalizado de notícias.

## Funcionalidades

- **Interface Gráfica Moderna**: Interface construída com Tkinter e ttkbootstrap para uma experiência visual profissional
- **Autenticação de Usuários**: Sistema completo de login, registro e gerenciamento de perfil
- **Pesquisa com IA**: Integração com a API Gemini para busca inteligente de notícias
- **Categorias Especializadas**:
  - Tecnologia
  - Cibersegurança
  - Inteligência Artificial (IA)
  - Internet das Coisas (IoT)
- **Gerenciamento de Notícias**: Salve, organize e exporte suas notícias favoritas
- **Temas Personalizáveis**: Escolha entre tema claro, escuro e outros estilos visuais
- **Banco de Dados Local**: Armazenamento eficiente de usuários e notícias

## Requisitos do Sistema

- Python 3.8+
- Bibliotecas Python (instaladas automaticamente):
  - ttkbootstrap (para interface moderna)
  - Pillow (processamento de imagens)
  - google-genai (cliente para API Gemini)
  - requests (comunicação HTTP)
  - sqlite3 (incluído com Python)

## Instalação

1. Clone este repositório ou baixe o código-fonte:
```bash
git clone https://github.com/seu-usuario/nexusinfo.git
cd nexusinfo
```

2. Crie e ative um ambiente virtual (recomendado):
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

## Configuração

O NexusInfo funciona com uma chave da API Gemini. Você pode configurá-la de várias maneiras:

1. **Variável de ambiente**:
```bash
# Windows
set GOOGLE_API_KEY=sua-chave-api
# Linux/macOS
export GOOGLE_API_KEY=sua-chave-api
```

2. **Arquivo .env**:
Crie um arquivo `.env` na pasta raiz do projeto com o conteúdo:
```
GOOGLE_API_KEY=sua-chave-api
```

3. **Argumento de linha de comando**:
```bash
python run.py --api-key=sua-chave-api
```

4. **Interface do aplicativo**:
Você também pode configurar a chave API nas configurações do aplicativo após o login.

## Execução

Para iniciar o aplicativo:

```bash
python run.py
```

Opções de linha de comando:
```
--theme THEME     Tema da interface (dark, light, etc.)
--api-key API_KEY Chave da API Gemini
--debug           Ativar modo de depuração
```

## Estrutura do Projeto

```
nexusinfo/
├── assets/               # Recursos gráficos
├── data/                 # Diretório de dados
├── main.py               # Arquivo principal da aplicação
├── run.py                # Script de inicialização
├── auth_manager.py       # Gerenciamento de autenticação
├── database_manager.py   # Gerenciamento de banco de dados
├── gemini_service.py     # Serviço de integração com API Gemini
├── requirements.txt      # Dependências do projeto
└── README.md             # Este arquivo
```

## Modo de Demonstração

Se a API do Google Gemini não estiver disponível, o aplicativo funcionará em "modo de demonstração", usando dados simulados para mostrar as funcionalidades da interface.

## Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo LICENSE para detalhes.

## Créditos

- **NexusInfo Team**
- **Google Gemini API**: https://ai.google.dev/gemini-api
- **ttkbootstrap**: https://ttkbootstrap.readthedocs.io/

---

Desenvolvido para demonstrar o uso da API Gemini com interface Tkinter moderna.