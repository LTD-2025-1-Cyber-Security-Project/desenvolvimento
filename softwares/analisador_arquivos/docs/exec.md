# DocMaster Pro - Documentação de Instalação e Uso

## Visão Geral

O DocMaster Pro é um sistema inteligente de processamento de documentos que permite analisar, gerenciar e extrair informações de diversos tipos de arquivos. Esta documentação oferece instruções detalhadas para instalar, configurar e utilizar o sistema em ambientes Windows.

![DocMaster Pro Banner](https://placeholder.com/banner)

## Índice

1. [Requisitos do Sistema](#requisitos-do-sistema)
2. [Arquivos do Projeto](#arquivos-do-projeto)
3. [Métodos de Instalação](#métodos-de-instalação)
   - [Método 1: Instalação com Python](#método-1-instalação-com-python)
   - [Método 2: Instalação via Executável](#método-2-instalação-via-executável)
4. [Criação de Executável Personalizado](#criação-de-executável-personalizado)
5. [Uso do Sistema](#uso-do-sistema)
6. [Configuração da API Google Gemini](#configuração-da-api-google-gemini)
7. [Solução de Problemas](#solução-de-problemas)
8. [Perguntas Frequentes](#perguntas-frequentes)

## Requisitos do Sistema

- **Sistema Operacional**: Windows 10/11 (64 bits)
- **Requisitos de Hardware**:
  - 4GB de RAM (8GB recomendado)
  - 500MB de espaço livre em disco (para instalação básica)
  - Processador dual-core 2.0 GHz ou superior
- **Software Necessário**:
  - Para instalação via Python: Python 3.9 ou superior
  - Para instalação via executável: Nenhum requisito adicional

## Arquivos do Projeto

Os seguintes arquivos são essenciais para o funcionamento do DocMaster Pro:

| Arquivo | Descrição |
|---------|-----------|
| `run.py` | Script principal de instalação e execução do DocMaster Pro |
| `build_exe.py` | Script para criação de executável standalone |
| `DocMaster.bat` | Arquivo batch para facilitar a execução no Windows |
| `app.py` | Aplicação principal do DocMaster (não modificar) |
| `requirements.txt` | Lista de dependências Python |
| `.env.example` | Modelo para arquivo de configuração |

## Métodos de Instalação

### Método 1: Instalação com Python

Se você tem Python instalado no seu sistema, este é o método recomendado para desenvolvedores e usuários técnicos:

1. **Certifique-se de ter Python 3.9 ou superior instalado**:
   ```
   python --version
   ```

2. **Clone ou baixe os arquivos do projeto** para uma pasta no seu computador

3. **Execute o instalador usando o arquivo batch**:
   ```
   DocMaster.bat
   ```
   Ou diretamente com Python:
   ```
   python run.py
   ```

4. **Siga as instruções na tela** para completar a instalação
   - O instalador criará um ambiente virtual
   - Instalará as dependências necessárias
   - Configurará o ambiente (incluindo API do Google Gemini)
   - Inicializará o banco de dados
   - Lançará o aplicativo no navegador

### Método 2: Instalação via Executável

Para usuários não técnicos, é recomendado usar o executável pré-compilado:

1. **Baixe o arquivo `DocMaster.exe`** da área de releases
   
2. **Execute o arquivo** com privilégios de administrador
   - Clique com o botão direito > "Executar como administrador"
   
3. **Siga as instruções na tela**
   - O programa abrirá uma janela de console
   - O navegador será aberto automaticamente com a interface
   - Siga as instruções adicionais de configuração, se solicitadas

## Criação de Executável Personalizado

Se você precisar criar seu próprio executável, siga estas etapas:

1. **Instale o Python 3.9 ou superior** no seu sistema

2. **Execute o script de criação de executável**:
   ```
   python build_exe.py
   ```

3. **Acompanhe o processo**:
   - O script verificará os requisitos do sistema
   - Instalará o PyInstaller, se necessário
   - Criará um arquivo de especificação (.spec)
   - Compilará o executável
   - Criará um atalho na área de trabalho (opcional)

4. **Após a conclusão**, o executável estará disponível na pasta `dist/DocMaster.exe`

## Uso do Sistema

Após a instalação bem-sucedida, o DocMaster Pro será aberto automaticamente no navegador padrão. Caso isso não aconteça, você pode acessar:

```
http://127.0.0.1:5000
```

O sistema oferece as seguintes funcionalidades principais:

- **Upload de Documentos**: Faça upload de documentos PDF, Word, imagens e outros formatos suportados
- **Processamento Automático**: O sistema processará automaticamente os documentos, extraindo texto e metadados
- **Análise com IA**: Com a API Gemini configurada, o sistema pode analisar o conteúdo dos documentos
- **Organização e Busca**: Organize seus documentos e realize buscas por conteúdo
- **Exportação de Relatórios**: Exporte os resultados da análise em diferentes formatos

## Configuração da API Google Gemini

Para utilizar recursos avançados de IA:

1. **Obtenha uma chave de API do Google Gemini**:
   - Acesse: [https://makersuite.google.com/app/apikey](https://makersuite.google.com/app/apikey)
   - Crie uma conta Google, se necessário
   - Gere uma nova chave de API

2. **Configure a chave no DocMaster Pro**:
   - Durante a primeira execução, você será solicitado a fornecer a chave
   - Ou edite manualmente o arquivo `.env` e adicione:
     ```
     GOOGLE_AI_API_KEY=sua-chave-aqui
     ```

3. **Reinicie o aplicativo** para que as alterações entrem em vigor

## Solução de Problemas

### Problemas Comuns

| Problema | Solução |
|----------|---------|
| **Erro de codificação de caracteres** | Configure seu terminal Windows para usar UTF-8: `chcp 65001` |
| **Porta 5000 já em uso** | O sistema tentará automaticamente outra porta. Verifique a mensagem no console |
| **Falha ao inicializar o banco de dados** | Verifique permissões na pasta do projeto e execute como administrador |
| **Navegador não abre automaticamente** | Acesse manualmente http://127.0.0.1:5000 (ou a porta indicada no console) |
| **Dependências não instaladas** | Execute `pip install -r requirements.txt` manualmente |

### Logs de Diagnóstico

Os logs do sistema estão disponíveis em:

- `installation.log` - Log de instalação e inicialização
- `logs/app.log` - Log de uso da aplicação

### Redefinindo a Instalação

Para reiniciar do zero:

1. **Remova os diretórios**:
   - `venv` (ambiente virtual)
   - `instance` (banco de dados)
   
2. **Execute novamente o instalador**:
   ```
   python run.py
   ```

## Perguntas Frequentes

**P: O DocMaster Pro funciona offline?**
R: Sim, a maioria das funcionalidades funciona offline. Apenas os recursos de análise com IA requerem conexão com a internet.

**P: Posso instalar em sistemas Linux ou macOS?**
R: Sim, o código suporta todos os sistemas operacionais principais, mas esta documentação é específica para Windows. Para outros sistemas, consulte a documentação complementar.

**P: Quais formatos de arquivo são suportados?**
R: O sistema suporta PDF, DOCX, TXT, imagens (JPG, PNG) e outros formatos comuns de documentos.

**P: Como faço backup dos meus dados?**
R: O sistema cria automaticamente backups na pasta `backups`. Você também pode fazer backup manual copiando a pasta `instance`.

**P: O que fazer se o executável não funcionar?**
R: Tente a instalação via Python (Método 1) ou verifique os logs para identificar problemas específicos.

---

© 2025 DocMaster Pro | Desenvolvido por [Sua Empresa]