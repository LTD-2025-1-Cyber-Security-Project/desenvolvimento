# Instruções de Uso - Aplicativo de Notícias Gemini

## Visão Geral

O Aplicativo de Notícias Gemini é uma ferramenta de linha de comando que permite consultar notícias sobre qualquer tópico usando a API Gemini do Google com Search Grounding. As notícias consultadas são automaticamente salvas em arquivos de texto para referência futura.

## Funcionalidades

- **Consulta de notícias**: Busca informações atualizadas da web sobre qualquer tópico
- **Salvamento automático**: Todas as consultas são salvas em arquivos TXT na pasta "noticias"
- **Listagem de arquivos**: Visualize e acesse notícias salvas anteriormente
- **Interface amigável**: Formatação colorida para melhor legibilidade

## Como Usar

### Instalação

1. Certifique-se de que as dependências estão instaladas:
   ```bash
   pip install -r requirements.txt
   ```

2. Execute o aplicativo:
   ```bash
   python noticias.py
   ```

### Comandos Disponíveis

O aplicativo reconhece os seguintes comandos especiais:

| Comando | Alternativas | Função |
|---------|--------------|--------|
| `arquivo` | `arquivos`, `ver` | Mostra a lista de notícias salvas |
| `ajuda` | `help`, `?` | Exibe a tela de ajuda |
| `limpar` | `clear` | Limpa a tela do terminal |
| `sair` | `exit`, `quit`, `q` | Encerra o aplicativo |

### Consulta de Notícias

Para buscar notícias sobre qualquer tópico:

1. Digite sua consulta no prompt `>`
2. O aplicativo pesquisará informações atualizadas usando o Gemini e Google Search
3. A resposta será exibida no terminal
4. As informações serão automaticamente salvas em um arquivo de texto

### Visualização de Notícias Salvas

Para ver notícias já consultadas:

1. Digite `arquivo`, `arquivos` ou `ver` no prompt
2. Será exibida uma lista numerada de notícias salvas, da mais recente para a mais antiga
3. Digite o número correspondente à notícia que deseja visualizar
4. O conteúdo completo da notícia será exibido
5. Pressione Enter para voltar ao menu principal

## Estrutura dos Arquivos Salvos

Cada arquivo salvo segue este padrão:

- **Nome do arquivo**: `AAAAMMDD_HHMMSS_consulta.txt`
- **Conteúdo**:
  - Consulta original
  - Data e hora da consulta
  - Resposta completa do Gemini
  - Lista de fontes usadas para gerar a resposta

## Exemplos de Consultas

- "Últimas notícias sobre a guerra na Ucrânia"
- "O que aconteceu no Brasil hoje?"
- "Novidades sobre inteligência artificial"
- "Resultados dos jogos de futebol de ontem"
- "Previsão do tempo para São Paulo nos próximos dias"

## Solução de Problemas

- **Erro de conexão**: Verifique sua conexão com a internet
- **Erro na API**: Verifique se a chave API está correta e ativa
- **Arquivo não encontrado**: Certifique-se de que a pasta "noticias" não foi excluída ou movida