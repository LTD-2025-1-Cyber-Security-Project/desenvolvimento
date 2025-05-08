# Guia de Instalação Rápida - Sistema Multi-IA para Prefeitura

Este guia apresenta os passos para instalar e configurar o Sistema Multi-IA para Prefeitura.

## Pré-requisitos

- Python 3.9 ou superior
- Acesso à internet
- Permissões de administrador (opcional, para instalação global)

## Passo a Passo de Instalação

### 1. Baixar e Preparar o Ambiente

```bash
# Clonar o repositório (ou baixar o ZIP)
git clone <url-do-repositório> sistema-ia-prefeitura
cd sistema-ia-prefeitura

# Criar ambiente virtual
python -m venv venv

# Ativar ambiente virtual
# No Windows:
venv\Scripts\activate
# No Linux/Mac:
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
```

### 2. Executar o Sistema

```bash
# Iniciar o servidor Flask
python app.py
```

### 3. Acessar o Sistema

Abra seu navegador e acesse:
```
http://127.0.0.1:5000/
```

### 4. Fazer Login

Use as credenciais padrão iniciais:
- **Usuário**: admin
- **Senha**: admin123

## Informações Importantes

### Modelos de IA Pré-configurados

- Google Gemini 1.5 Pro e Flash já vêm pré-configurados com a chave de API padrão
- Não é necessário configurar nada para começar a usar estes modelos

### Configurando Modelos Adicionais

Para usar outros modelos de IA:

1. Acesse o menu "Administração" > "Configurações de IA"
2. Insira suas chaves de API para os modelos desejados
3. Habilite os modelos que deseja usar
4. Defina um modelo padrão

### Recomendações para Produção

- Ative HTTPS em ambiente de produção
- Substitua o armazenamento baseado em arquivos por um banco de dados real
- Configure backups regulares para os dados
- Atualize a SECRET_KEY no arquivo app.py

### Solução de Problemas Comuns

**O sistema não inicia:**
- Verifique se todas as dependências foram instaladas
- Confirme que o Python 3.9+ está instalado

**Limite de API do Google Gemini:**
- Por padrão, a API gratuita do Google Gemini tem limites de uso
- Configure modelos alternativos como backup
- Considere planos pagos para uso intensivo

**Erro ao acessar modelos adicionais:**
- Verifique se a chave API está correta
- Confirme se a API está disponível para sua região
- Alguns modelos podem exigir configurações específicas

## Próximos Passos

1. Altere a senha padrão do administrador
2. Crie usuários adicionais conforme necessário
3. Personalize as configurações de cada modelo de IA
4. Explore a criação de templates para seus documentos mais comuns

Para informações mais detalhadas, consulte o arquivo README.md completo.