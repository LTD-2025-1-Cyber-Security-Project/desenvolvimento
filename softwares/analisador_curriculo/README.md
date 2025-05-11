# Analisador de Currículos com IA

Este aplicativo web permite analisar currículos em PDF usando a API do Google Gemini.

## Requisitos

- Python 3.6+
- Conexão com a Internet
- Chave de API do Google Gemini

## Instalação no Windows

### Método 1: Instalação Automatizada
1. Simplesmente execute o arquivo `iniciar_analisador.bat` e siga as instruções.
2. O script irá configurar automaticamente o ambiente virtual e instalar as dependências.

### Método 2: Instalação Manual
1. Certifique-se de ter o Python 3.6+ instalado. [Download Python](https://www.python.org/downloads/windows/)
2. Abra um Prompt de Comando e navegue até o diretório do aplicativo.
3. Crie um ambiente virtual:
   ```
   python -m venv venv
   ```
4. Ative o ambiente virtual:
   ```
   venv\Scripts\activate
   ```
5. Instale as dependências:
   ```
   pip install -r requirements.txt
   ```
6. Configure a API do Google:
   - Edite o arquivo `.env` e adicione sua chave da API do Google Gemini.
7. Inicie o aplicativo:
   ```
   python app.py
   ```
8. Acesse no navegador: `http://localhost:5000`

## Funcionalidades

- Upload de currículos em formato PDF
- Análise do currículo com diferentes focos:
  - Análise Geral
  - Foco em Habilidades Técnicas
  - Foco em Soft Skills
  - Sugestões de Melhorias
- Personalização por nível (Estágio, Júnior, Pleno, Sênior, etc.)
- Personalização por área (Web, Mobile, Data Science, DevOps, etc.)

## Solução de Problemas

- **Erro de API do Google**: Verifique se a chave no arquivo `.env` está correta.
- **Problemas na inicialização**: Verifique se todas as dependências estão instaladas corretamente.
- **Erros de arquivo**: Certifique-se de que o PDF está em um formato válido.

## Licença

Todos os direitos reservados.
