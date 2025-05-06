# Analisador de Currículos com IA

Um sistema avançado de análise de currículos desenvolvido com Python e Flask, que utiliza inteligência artificial para fornecer feedback detalhado sobre currículos em PDF.

## Funcionalidades

- Upload de currículos em formato PDF
- Extração avançada de texto dos PDFs
- Análise personalizada com base em:
  - Tipo de análise (geral, técnico, comportamental, etc.)
  - Nível profissional (júnior, pleno, sênior, etc.)
  - Stack/Área de tecnologia (desenvolvimento web, ciência de dados, DevOps, etc.)
- Feedback detalhado incluindo:
  - Pontuação geral
  - Resumo executivo
  - Análise detalhada de vários aspectos
  - Pontos fortes identificados
  - Oportunidades de melhoria
  - Avaliação de otimização para ATS
  - Recomendações personalizadas

## Tecnologias Utilizadas

- Python 3.8+
- Flask (framework web)
- PyPDF2 e pdfminer.six (extração de texto de PDFs)
- OpenAI GPT-4 (análise avançada de texto)
- LangChain (estruturação de prompts e integração com LLMs)
- spaCy (processamento de linguagem natural)
- Transformers (modelos de IA local)
- NLTK (análise de texto)

## Configuração

1. Clone o repositório
2. Instale as dependências:
   ```
   pip install -r requirements.txt
   ```
3. Configure as variáveis de ambiente:
   - Crie um arquivo `.env` na raiz do projeto com:
     ```
     SECRET_KEY=sua-chave-secreta
     OPENAI_API_KEY=sua-chave-da-api-openai
     FLASK_ENV=development
     ```
4. Execute a aplicação:
   ```
   python app.py
   ```

## Uso

1. Acesse a aplicação em `http://localhost:5000`
2. Faça upload de um currículo em formato PDF
3. Selecione os parâmetros de análise:
   - Tipo de análise
   - Nível profissional
   - Stack/Área de tecnologia
4. Clique em "Analisar Currículo"
5. Visualize os resultados detalhados da análise

## Contribuição

Contribuições são bem-vindas! Sinta-se à vontade para abrir issues ou enviar pull requests com melhorias.

## Licença

Este projeto está licenciado sob a licença MIT.