# Instruções para Gerar o Executável do Analisador de Currículos

Este guia vai te ajudar a transformar seu aplicativo Flask em um executável para Windows usando o script `run.py`.

## Pré-requisitos

- macOS (o script foi projetado para ser executado no macOS)
- Python 3.x instalado
- pip instalado

## Passos para gerar o executável

1. **Preparação**

   - Certifique-se de que o arquivo `app.py` está no diretório atual
   - Salve o script `run.py` fornecido no mesmo diretório

2. **Execução do script**

   Abra o Terminal e navegue até o diretório do projeto, depois execute:

   ```bash
   python3 run.py
   ```

3. **O que o script faz**

   O script automatiza todo o processo de criação do executável:

   - Verifica seu sistema e pré-requisitos
   - Configura um ambiente virtual Python
   - Instala todas as dependências necessárias
   - Cria os arquivos utilitários e templates HTML necessários
   - Cria um arquivo `.env.example` e um `.env` para suas chaves API
   - Usa PyInstaller para criar o executável para Windows

4. **Após a conclusão**

   Se tudo correr bem, você encontrará:
   
   - Uma pasta `dist_win/AnalisadorCurriculos` contendo o executável e todos os arquivos necessários
   - Um arquivo `README.txt` com instruções para o usuário Windows

5. **Transferência para Windows**

   - Copie a pasta `dist_win/AnalisadorCurriculos` completa para o computador Windows
   - No Windows, edite o arquivo `.env` para adicionar sua chave da API do Google
   - Execute o arquivo `AnalisadorCurriculos.exe` no Windows

## Configuração da API do Google

É **fundamental** adicionar sua chave da API do Google Gemini no arquivo `.env`:

```
GOOGLE_API_KEY=sua_chave_aqui
SECRET_KEY=chave_secreta_para_flask
```

Sem a chave da API do Google, o analisador de currículos não funcionará corretamente.

## Solução de problemas

- Se o executável não iniciar no Windows, verifique se todas as DLLs necessárias estão presentes
- Certifique-se de que o Windows Defender ou outro antivírus não está bloqueando o aplicativo
- Verifique se a chave da API no arquivo `.env` está correta
- Se necessário, execute o aplicativo como administrador

## Estrutura do projeto final

O executável final conterá:

- O aplicativo principal (`AnalisadorCurriculos.exe`)
- Pasta `templates` com os arquivos HTML
- Arquivo `.env` para configurações
- Todas as bibliotecas e dependências necessárias