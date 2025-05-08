# Sistema Multi-Modelo de IA para Prefeitura

![alt text](<images/Captura de Tela 2025-05-08 às 12.08.29.png>)

Um sistema web com Flask que permite funcionários da prefeitura gerar documentos e conteúdos usando vários modelos de IA através de prompts de comando personalizados.

## Características Principais

- Suporte para múltiplos modelos de IA:
  - Google Gemini (1.5 Pro e Flash) - **Pré-configurado com chave API padrão**
  - OpenAI GPT (3.5 e 4)
  - Anthropic Claude
  - Perplexity AI
  - DeepSeek
  - xAI Grok
  - Blackbox AI

- Gerenciamento central de chaves de API e configurações
- Sistema inteligente de fallback quando um modelo atinge limites de requisição
- Templates reutilizáveis para prompts comuns
- Histórico de todas as solicitações
- Administração de usuários e permissões

## Configuração de API

- **Google Gemini**: Chave padrão já configurada (`AIzaSyCY5JQRIAZlq7Re-GNDtwn8b1Hmza_hk8Y`)
- Outros modelos: Cada funcionário pode definir suas próprias chaves API nas configurações

## Requisitos

- Python 3.9+ 
- Flask e dependências (veja requirements.txt)
- Conexão à internet para acessar as APIs de IA
- Chaves API para os modelos de IA adicionais (opcional)

## Instalação

1. Clone o repositório:
```bash
git clone <repositório>
cd sistema-ia-prefeitura
```

2. Crie e ative um ambiente virtual:
```bash
python -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

4. Execute o aplicativo:
```bash
python app.py
```

5. Acesse no navegador:
```
http://127.0.0.1:5000/
```

## Credenciais Padrão

- **Usuário**: admin
- **Senha**: admin123

## Uso do Sistema

1. **Após login**:
   - Use diretamente o Google Gemini (chave já configurada)
   - Ou vá para "Configurações de IA" para personalizar/adicionar outras chaves

2. **Gerando documentos**:
   - Escolha o modelo de IA desejado
   - Preencha os dados do prompt
   - Obtenha resultados imediatamente

3. **Em caso de limite de API**:
   - O sistema tentará usar modelos alternativos
   - Você pode configurar outros modelos com suas próprias chaves

## Configuração de Modelo Preferido

Cada usuário pode configurar seu modelo de IA preferido através do menu de Preferências. Isso permite que cada funcionário use sua própria chave API quando necessário.

## Modelos de IA Suportados

### Google Gemini (Pré-configurado)
- Modelos: gemini-1.5-pro, gemini-1.5-flash
- Chave API padrão já configurada

### OpenAI
- Modelos: gpt-4, gpt-3.5-turbo
- [Obter chave API](https://platform.openai.com/)

### Anthropic Claude
- Modelos: claude-3-opus-20240229 e outros
- [Obter chave API](https://www.anthropic.com/api)

### Outros Modelos
- Perplexity AI: [Site oficial](https://www.perplexity.ai/)
- DeepSeek: [Site oficial](https://www.deepseek.com/)
- xAI Grok: [Site oficial](https://grok.x.ai/)
- Blackbox AI: [Site oficial](https://www.blackbox.ai/)

## Estrutura de Diretórios

```
sistema-ia-prefeitura/
├── app.py                # Aplicação principal
├── data/                 # Diretório para dados persistentes
│   ├── ai_models.json    # Configurações dos modelos de IA
│   ├── users.json        # Dados de usuários
│   ├── prompts_history.json # Histórico de prompts
│   └── templates.json    # Templates salvos
├── static/               # Arquivos estáticos
│   ├── css/
│   │   └── style.css     # Estilos personalizados
│   └── js/
│       └── main.js       # JavaScript do frontend
├── templates/            # Templates HTML
└── requirements.txt      # Dependências Python
```

## Solução para Problemas Comuns

### "Limite de requisições atingido"
- O sistema tentará automaticamente outro modelo de IA
- Você pode configurar vários modelos como backup
- O Google Gemini tem limite de requisições no plano gratuito

### "API Key não configurada"
- Para modelos além do Gemini, é necessário inserir sua própria chave API nas configurações
- Administradores podem configurar chaves globais
- Cada usuário pode ter sua própria chave preferida

## Contribuindo

Contribuições são bem-vindas! Por favor, abra uma issue ou pull request para sugestões, correções de bugs ou novos recursos.

## Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo LICENSE para detalhes.