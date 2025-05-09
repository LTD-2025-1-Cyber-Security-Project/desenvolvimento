# Sistema Gerador de Ofícios
![alt text](<images/Captura de Tela 2025-05-09 às 10.55.39.png>)
![Logo do Sistema](https://img.shields.io/badge/Sistema-Gerador%20de%20Of%C3%ADcios-1A5276?style=for-the-badge&logo=data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAACXBIWXMAAAsTAAALEwEAmpwYAAABUUlEQVR42mNkIAIIC8vwMDAw5DAwMGgzMDJ+Y2BkPPP+/aujv3//ZiBGPyMxmsXEJCYxMTL2MTExGzEwMHAzMTFzMTExtTMyMk5jYGBcxMzMXP/x44cPDAwMTHAD9PT0GG7fvs3AzS3QwcTEvJCJifk/CwvLf6h4FhMT0z8WFpabLCwscxkYGYWePXv6CV0TIyMj4+rVqxhERUVhfJ63b9/+//Tp0//Bgf7/bWys/0VFRf5LSkr8FxQU/K+kpPTf3t7+PwcHB8zpiYmJ/7OyMsEG5OblMLCxsbNISEr+/vv37/+3b97+v3P79v/r16//v3L5MsOzZ88YQM4FB+3du3cZWltbGQoLC///+ePHbyYmJkagIWJMTExcQIV/QJpB7v3z5w/Dv39/GYDqwQaw4jIAZPvHT58ZQAZ8/PCB4e/fvyDnsgDdDwZM+JIhLK2C/BVGFwMAC25sMJhNPxMAAAAASUVORK5CYII=)

## 📑 Tabela de Conteúdos

- [Visão Geral](#-visão-geral)
- [Funcionalidades](#-funcionalidades)
- [Tecnologias](#-tecnologias)
- [Requisitos do Sistema](#-requisitos-do-sistema)
- [Instalação](#-instalação)
- [Credenciais de Acesso](#-credenciais-de-acesso)
- [Estrutura dos Ofícios](#-estrutura-dos-ofícios)
- [Guia de Uso](#-guia-de-uso)
- [Administração do Sistema](#-administração-do-sistema)
- [Solução de Problemas](#-solução-de-problemas)
- [FAQ](#-faq)
- [Contribuições](#-contribuições)
- [Licença](#-licença)
- [Contato e Suporte](#-contato-e-suporte)

## 🌟 Visão Geral

O **Sistema Gerador de Ofícios** é uma solução completa e profissional para criação, gestão e controle de ofícios, desenvolvida especificamente para as prefeituras de Florianópolis e São José. Este sistema permite que funcionários públicos criem, editem e gerenciem documentos oficiais de forma eficiente, com recursos avançados de autenticação, armazenamento em banco de dados, exportação para PDF e gerenciamento administrativo.

![Screenshot do Sistema](https://img.shields.io/badge/Status-Em%20Produção-success)

## 🚀 Funcionalidades

### Autenticação e Segurança
- ✅ Sistema de login e cadastro de usuários
- ✅ Perfis diferenciados (Administrador e Usuário)
- ✅ Senhas criptografadas com SHA-256
- ✅ Validação de email institucional (.gov.br)

### Gestão de Ofícios
- ✅ Criação de ofícios com numeração sequencial automática
- ✅ Personalização por município (cabeçalhos específicos)
- ✅ Edição e visualização de ofícios existentes
- ✅ Sistema de status (Pendente, Em andamento, Finalizado, Cancelado)
- ✅ Pesquisa e filtros avançados

### Geração de Documentos
- ✅ Exportação para PDF com layout profissional
- ✅ Inclusão de logotipos e assinaturas digitais
- ✅ Formatação conforme normas oficiais
- ✅ Visualização prévia antes da finalização

### Interface de Usuário
- ✅ Dashboard intuitivo com estatísticas
- ✅ Menu de navegação simplificado
- ✅ Formulários organizados e intuitivos
- ✅ Design responsivo e moderno

### Administração
- ✅ Gerenciamento completo de usuários
- ✅ Resetar senhas de usuários
- ✅ Visualização de estatísticas do sistema

## 💻 Tecnologias

- **Python 3.8+**: Linguagem principal do sistema
- **Tkinter**: Framework para interface gráfica
- **SQLite**: Banco de dados leve e portátil
- **ReportLab**: Biblioteca para geração de PDFs
- **Pillow**: Processamento de imagens (logotipos e assinaturas)
- **Hashlib**: Criptografia de senhas

## 📋 Requisitos do Sistema

### Requisitos de Hardware
- Processador de 1 GHz ou superior
- 2 GB de RAM (4 GB recomendado)
- 100 MB de espaço em disco para o programa
- Espaço adicional para armazenamento de ofícios e PDFs

### Requisitos de Software
- Sistema Operacional: Windows 7+, macOS 10.12+, ou Linux
- Python 3.8 ou superior
- Conexão com Internet (para instalação inicial)

## 📥 Instalação

### Método Automatizado (Recomendado)

A maneira mais simples de instalar e executar o sistema é usando o script automatizado `run.py`, que configura todo o ambiente necessário:

1. Clone ou baixe o repositório para sua máquina local
2. Abra um terminal/prompt de comando na pasta do projeto
3. Execute o script de instalação:

```bash
python run.py
```

Este script irá:
- Verificar se seu sistema atende aos requisitos
- Criar um ambiente virtual Python
- Instalar todas as dependências necessárias
- Configurar o banco de dados
- Iniciar o sistema automaticamente

### Instalação Manual

Se preferir instalar manualmente:

1. Clone o repositório:
```bash
git clone https://github.com/prefeituras/sistema-gerador-oficios.git
cd sistema-gerador-oficios
```

2. Crie e ative um ambiente virtual:
```bash
# No Windows
python -m venv venv
venv\Scripts\activate

# No macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

4. Execute o aplicativo:
```bash
python app.py
```

## 🔑 Credenciais de Acesso

O sistema vem pré-configurado com três usuários para teste:

| Tipo | Email | Senha | Descrição |
|------|-------|-------|-----------|
| **Administrador** | admin@sistema.gov.br | admin123 | Acesso total ao sistema, incluindo gerenciamento de usuários |
| **Usuário Florianópolis** | usuario@floripa.sc.gov.br | floripa123 | Usuário padrão com acesso aos recursos de Florianópolis |
| **Usuário São José** | usuario@saojose.sc.gov.br | saojose123 | Usuário padrão com acesso aos recursos de São José |

⚠️ **Importante**: Por segurança, altere as senhas padrão no primeiro acesso ao sistema.

## 📄 Estrutura dos Ofícios

### Elementos do Ofício

O sistema implementa a estrutura padrão de ofícios conforme as normas da administração pública:

| Elemento | Descrição | Obrigatório |
|----------|-----------|:-----------:|
| **Logotipo** | Identidade visual da prefeitura (opcional) | ❌ |
| **Número do Ofício** | Identificador único sequencial (gerado automaticamente) | ✅ |
| **Protocolo (OE)** | Número de protocolo externo | ❌ |
| **Cidade e Data** | Local e data de emissão | ✅ |
| **Destinatário** | Nome, cargo e órgão do destinatário | ✅ |
| **Assunto** | Resumo do conteúdo do ofício | ✅ |
| **Cumprimentos** | Saudação inicial (ex: "Prezado Senhor,") | ✅ |
| **Texto do Ofício** | Conteúdo principal do documento | ✅ |
| **Despedida** | Expressão de cordialidade (ex: "Atenciosamente,") | ✅ |
| **Remetente** | Nome do autor do ofício | ✅ |
| **Cargo do Remetente** | Função do autor no órgão | ✅ |
| **Assinatura** | Imagem da assinatura (opcional) | ❌ |

### Normas e Legislação

O sistema segue as diretrizes do Manual de Redação da Presidência da República e as seguintes normativas:

- **Decreto nº 9.758/2019**: Dispõe sobre formas de tratamento e endereçamento
- **Portaria nº 1.369/2018**: Estabelece o padrão visual das comunicações
- **Instrução Normativa nº 4/2018**: Define os padrões de arquivos digitais

## 📝 Guia de Uso

### 1. Login e Navegação

1. Inicie o sistema usando `python run.py`
2. Faça login com suas credenciais
3. Navegue pelo sistema usando o menu lateral:
   - **Início**: Dashboard com estatísticas
   - **Novo Ofício**: Criar um novo documento
   - **Meus Ofícios**: Gerenciar documentos existentes
   - **Meu Perfil**: Editar informações pessoais
   - **Sair**: Encerrar a sessão

### 2. Criando um Novo Ofício

1. Clique em "Novo Ofício" no menu lateral
2. Preencha os campos obrigatórios:
   - O número do ofício é gerado automaticamente
   - Adicione um assunto claro e objetivo
   - Preencha os dados do destinatário
   - Digite o conteúdo do ofício
3. Opcionalmente, adicione elementos extras:
   - Logotipo da instituição
   - Assinatura digital
   - Número de protocolo
4. Clique em "Visualizar Prévia" para revisar o documento
5. Clique em "Salvar Ofício" para armazenar no sistema

### 3. Gerenciando Ofícios

1. Acesse "Meus Ofícios" no menu lateral
2. Use os filtros para buscar documentos específicos
3. Clique duas vezes em um ofício para editar
4. Use os botões de ação para:
   - Editar: Modificar o conteúdo
   - Gerar PDF: Exportar para formato PDF
   - Excluir: Remover o ofício do sistema

### 4. Exportando para PDF

1. Abra um ofício existente ou crie um novo
2. Clique em "Gerar PDF"
3. Escolha o local para salvar o arquivo
4. O sistema gerará um PDF profissional com todos os elementos do ofício
5. Opcionalmente, o sistema pode abrir o PDF automaticamente após a geração

### 5. Editando seu Perfil

1. Acesse "Meu Perfil" no menu lateral
2. Atualize suas informações pessoais
3. Para alterar a senha:
   - Digite sua senha atual
   - Digite a nova senha
   - Confirme a nova senha
4. Clique em "Salvar Alterações" para atualizar seu perfil

## 👑 Administração do Sistema

### Gerenciamento de Usuários

Administradores têm acesso ao módulo de gerenciamento de usuários:

1. Acesse "Gerenciar Usuários" no menu lateral (apenas para administradores)
2. Visualize todos os usuários do sistema
3. Use os filtros para buscar usuários específicos
4. Clique nos botões de ação para:
   - Editar: Modificar informações do usuário
   - Resetar Senha: Definir uma nova senha
   - Excluir: Remover o usuário do sistema

### Adicionando Novos Usuários

1. No módulo de gerenciamento de usuários, clique em "Adicionar Usuário"
2. Preencha todos os campos obrigatórios
3. Selecione o município e o perfil de acesso
4. Defina uma senha inicial
5. Clique em "Adicionar Usuário" para concluir o cadastro

### Backup e Segurança

O sistema armazena todos os dados em um banco SQLite (`oficios_sistema.db`). Para garantir a segurança dos dados:

1. Faça backups regulares do arquivo de banco de dados
2. Armazene os backups em local seguro
3. Considere implementar um sistema de backup automatizado
4. Para restaurar, substitua o arquivo de banco de dados pelo backup

## 🔧 Solução de Problemas

### Problemas Comuns

| Problema | Possível Causa | Solução |
|----------|----------------|---------|
| **O sistema não inicia** | Python não instalado ou versão incompatível | Verifique a instalação do Python (versão 3.8+) |
| **Erro ao fazer login** | Credenciais incorretas | Verifique email e senha. Use as credenciais padrão se for o primeiro acesso |
| **Erro ao gerar PDF** | Falta de permissões ou bibliotecas | Verifique se o ReportLab está instalado e se há permissões de escrita |
| **Elementos gráficos não aparecem** | Falta de bibliotecas para imagens | Certifique-se de que o Pillow está instalado corretamente |
| **Erros de banco de dados** | Banco corrompido ou incompatível | Considere usar um backup ou executar `python run.py` para recriar o banco |

### Logs de Erro

Se encontrar problemas, verifique os logs no console para obter informações detalhadas sobre o erro. Muitos problemas podem ser resolvidos reinstalando as dependências:

```bash
pip install -r requirements.txt --force-reinstall
```

## ❓ FAQ

**P: Posso usar o sistema em qualquer computador?**
R: Sim, desde que atenda aos requisitos mínimos e tenha o Python instalado.

**P: É possível personalizar os modelos de ofício?**
R: Sim, o sistema permite personalização de cabeçalhos, logotipos e assinaturas.

**P: Os ofícios são armazenados apenas localmente?**
R: Sim, o sistema usa um banco de dados local SQLite. Para uso em rede, considere implementar um servidor compartilhado.

**P: Como faço para adicionar novos usuários?**
R: Usuários administradores podem adicionar novos usuários através do módulo "Gerenciar Usuários".

**P: É possível importar ofícios de outros sistemas?**
R: Não há funcionalidade de importação automática. Ofícios de outros sistemas precisariam ser recriados manualmente.

## 👥 Contribuições

Para contribuir com o desenvolvimento deste projeto:

1. Fork o repositório
2. Crie uma branch para sua funcionalidade (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Crie um Pull Request

### Diretrizes de Contribuição

- Siga as convenções de código do projeto
- Documente qualquer nova funcionalidade
- Adicione testes para novas funcionalidades
- Atualize a documentação conforme necessário

## 📄 Licença

Este software é de uso exclusivo das prefeituras de Florianópolis e São José, sendo protegido por direitos autorais e propriedade intelectual. A cópia, distribuição ou uso não autorizado é expressamente proibido.

## 📞 Contato e Suporte

Para suporte técnico ou dúvidas, entre em contato:

- **Email**: suporte@sistemaoficio.gov.br
- **Telefone**: (48) 3000-0000
- **Horário de atendimento**: Segunda a sexta, das 8h às 18h

---

Desenvolvido para as Prefeituras de Florianópolis e São José © 2025