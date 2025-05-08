# Encurtador de URL com IA para Prefeitura

![alt text](<images/Captura de Tela 2025-05-08 às 09.56.18.png>)

Sistema de encurtamento de URL utilizando Python e Flask com integração à API do Google Gemini para geração de códigos inteligentes.

## Funcionalidades

- Encurtamento de URLs longas utilizando Inteligência Artificial
- Geração de códigos curtos inteligentes relacionados ao conteúdo da URL
- Redirecionamento para URLs originais
- Rastreamento de acessos e estatísticas de uso
- Interface responsiva em HTML, CSS e JavaScript

## Requisitos

- Python 3.8 ou superior
- Flask e outras dependências (listadas em `requirements.txt`)
- Chave de API do Google Gemini

## Instalação

1. Clone o repositório:
   ```
   git clone https://github.com/ltd/encurtador-url.git
   cd encurtador-url
   ```

2. Crie um ambiente virtual Python e ative-o:
   ```
   python -m venv venv
   source venv/bin/activate  # No Windows: venv\Scripts\activate
   ```

3. Instale as dependências:
   ```
   pip install -r requirements.txt
   ```

4. Configure a chave da API do Google Gemini no arquivo `config.py`

## Uso

1. Inicie o servidor:
   ```
   python app.py
   ```

2. Acesse o aplicativo no navegador:
   ```
   http://localhost:5000
   ```

3. Cole a URL longa no campo e clique em "Encurtar"

4. Copie a URL curta gerada para compartilhar

## Estrutura do Projeto

```
app/
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── script.js
├── templates/
│   ├── base.html
│   ├── index.html
│   └── stats.html
├── app.py
├── url_shortener.py
├── config.py
├── requirements.txt
└── README.md
```

## Tecnologias Utilizadas

- **Backend**: Python, Flask
- **Frontend**: HTML5, CSS3, JavaScript
- **Banco de Dados**: SQLite
- **API**: Google Gemini (IA generativa)

## Configuração para Produção

Para um ambiente de produção, recomenda-se:

1. Usar um servidor WSGI como Gunicorn ou uWSGI
2. Configurar um proxy reverso como Nginx
3. Implementar HTTPS para segurança
4. Configurar um banco de dados mais robusto como PostgreSQL ou MySQL

Exemplo de configuração para produção:

```
# Instalar pacotes adicionais
pip install gunicorn psycopg2-binary

# Configurar variáveis de ambiente
export FLASK_ENV=production
export SECRET_KEY=sua_chave_secreta_aqui

# Iniciar com Gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

## Manutenção

- O banco de dados SQLite é adequado para uso interno com volume baixo a médio
- Para volumes maiores, considere migrar para PostgreSQL
- Faça backup regular do arquivo `urls.db`
- Monitore o uso da API Gemini para não exceder limites de quota

## Suporte

Para suporte técnico, entre em contato com o Departamento de TI da Prefeitura.

## Licença

Este projeto é confidencial e de uso exclusivo da Prefeitura Municipal.