# CurriculoBot - Assistente Futurista para Criação de Currículos

![CurriculoBot Logo](https://via.placeholder.com/800x200/00bcd4/ffffff?text=CurriculoBot)

## 📝 Índice
- [Sobre o Projeto](#sobre-o-projeto)
- [Características](#características)
- [Tecnologias Utilizadas](#tecnologias-utilizadas)
- [Requisitos do Sistema](#requisitos-do-sistema)
- [Instalação](#instalação)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Como Usar](#como-usar)
- [Fluxo de Conversação](#fluxo-de-conversação)
- [Personalização](#personalização)
- [Solução de Problemas](#solução-de-problemas)
- [Contribuições](#contribuições)
- [Licença](#licença)
- [Contato](#contato)

## 🤖 Sobre o Projeto

CurriculoBot é um assistente interativo com interface futurista que ajuda usuários a criar currículos profissionais através de uma experiência de chatbot guiada. O sistema coleta informações do usuário por meio de uma conversação natural e gera um currículo formatado profissionalmente em tempo real.

O projeto combina interface moderna e atraente com funcionalidade prática, permitindo aos usuários criar um currículo completo sem precisar entender formatação ou design.

## ✨ Características

- **Interface de Chatbot Intuitiva**: Comunicação natural e interativa para coleta de dados
- **Prévia em Tempo Real**: Visualização instantânea do currículo sendo montado
- **Design Futurista e Responsivo**: Funciona em dispositivos desktop e móveis
- **Sugestões Contextuais**: Botões de resposta rápida para facilitar a interação
- **Geração de PDF**: Fácil exportação e impressão do currículo finalizado
- **Armazenamento de Dados**: Salvamento das informações para recuperação futura
- **Fluxo Adaptativo**: Perguntas personalizadas com base em respostas anteriores (ex.: GitHub apenas para profissionais de TI)
- **Sessões Persistentes**: Possibilidade de retomar a criação do currículo posteriormente
- **Indicador de Digitação**: Feedback visual de quando o bot está "pensando"

## 🛠️ Tecnologias Utilizadas

- **Backend**:
  - Python 3.8+
  - Flask 2.0+
  - JSON para armazenamento de dados

- **Frontend**:
  - HTML5
  - CSS3 com animações
  - JavaScript / jQuery
  - Bootstrap 5
  - Font Awesome 6

## 📋 Requisitos do Sistema

### Requisitos Mínimos
- **Python**: 3.8 ou superior
- **Navegador**: Chrome 80+, Firefox 75+, Edge 80+, Safari 13+
- **Armazenamento**: 50MB de espaço livre
- **Memória**: 512MB RAM

### Requisitos Recomendados
- **Python**: 3.10 ou superior
- **Navegador**: Última versão do Chrome ou Firefox
- **Armazenamento**: 100MB de espaço livre
- **Memória**: 1GB RAM ou mais
- **Conexão Internet**: Para uso de CDNs (Bootstrap, jQuery, FontAwesome)

## 💻 Instalação

1. **Clone o repositório**:
   ```bash
   git clone https://github.com/seunome/curriculobot.git
   cd curriculobot
   ```

2. **Crie um ambiente virtual (recomendado)**:
   ```bash
   python -m venv venv
   
   # Ativação no Windows
   venv\Scripts\activate
   
   # Ativação no macOS/Linux
   source venv/bin/activate
   ```

3. **Instale as dependências**:
   ```bash
   pip install flask
   ```

4. **Crie a estrutura de diretórios**:
   ```bash
   mkdir -p data templates
   ```

5. **Execute a aplicação**:
   ```bash
   python app.py
   ```

6. **Acesse a aplicação**:  
   Abra seu navegador e acesse `http://127.0.0.1:5000`

## 📁 Estrutura do Projeto

```
curriculobot/
│
├── app.py                     # Arquivo principal da aplicação Flask
│
├── templates/                 # Diretório de templates HTML
│   ├── index.html            # Interface principal do chatbot
│   └── curriculo.html        # Template do currículo gerado
│
├── data/                      # Diretório para armazenamento de dados
│   └── curriculo_*.json      # Arquivos de dados dos currículos (gerados automaticamente)
│
├── README.md                  # Documentação do projeto
├── LICENSE                    # Licença do projeto
└── requirements.txt           # Dependências do projeto
```

## 🚀 Como Usar

### Iniciando uma Nova Sessão

1. Acesse a aplicação no navegador (http://127.0.0.1:5000)
2. O chatbot irá cumprimentá-lo com uma mensagem inicial
3. Digite "começar" ou clique no botão "Começar" para iniciar a criação do currículo
4. Siga as instruções do chatbot, respondendo às perguntas sobre suas informações pessoais e profissionais

### Navegação e Interação

- **Entrada de Texto**: Digite suas respostas no campo de texto na parte inferior da tela
- **Botões de Opção**: Clique nos botões disponíveis para respostas rápidas
- **Visualização**: Acompanhe a prévia do currículo no painel direito (ou abaixo, em dispositivos móveis)
- **Navegação**: Use os botões oferecidos para avançar ou voltar no processo

### Finalização e Download

1. Quando terminar de fornecer todas as informações, o chatbot oferecerá a opção de finalizar
2. Clique em "Finalizar" para concluir o processo
3. Você será levado à página do currículo gerado
4. Utilize o botão "Imprimir" para salvar como PDF ou imprimir o currículo
5. Você pode retornar ao chatbot para fazer alterações ou criar um novo currículo

## 🗣️ Fluxo de Conversação

O CurriculoBot segue um fluxo de conversação estruturado para coletar informações. Cada etapa é dependente da anterior e pode se adaptar com base nas respostas fornecidas:

1. **Boas-vindas e Introdução**
   - Apresentação do bot
   - Explicação do processo

2. **Informações Pessoais**
   - Nome e sobrenome
   - E-mail e endereço
   - Área de atuação profissional
   - Links sociais (site, LinkedIn, GitHub para área de TI)

3. **Formação Acadêmica** (opcional)
   - Instituição de ensino
   - Tipo de diploma/formação
   - Área de estudo/curso
   - Período (início e conclusão)
   - Descrição e competências adquiridas
   - Opção para adicionar múltiplas formações

4. **Cursos e Certificados** (opcional)
   - Nome do curso ou certificação
   - Instituição ou entidade emissora
   - Período (início e conclusão)
   - Descrição da certificação
   - Opção para adicionar múltiplos cursos

5. **Projetos** (opcional)
   - Nome do projeto
   - Habilidades e tecnologias utilizadas
   - Descrição e resultados
   - Opção para adicionar múltiplos projetos

6. **Experiência Profissional** (opcional)
   - Cargo ou posição
   - Empresa ou organização
   - Tipo de emprego (tempo integral, estágio, etc.)
   - Período (início e término)
   - Localidade e modalidade (presencial, home office, híbrido)
   - Responsabilidades e realizações
   - Opção para adicionar múltiplas experiências

7. **Finalização**
   - Revisão do currículo
   - Opções para edição adicional
   - Geração do currículo final
   - Download e impressão

## 🎨 Personalização

### Cores e Estilos

Para personalizar o visual do CurriculoBot, você pode modificar as variáveis CSS no arquivo `templates/index.html`:

```css
:root {
    --primary-color: #00bcd4;     /* Cor principal */
    --secondary-color: #3f51b5;   /* Cor secundária */
    --dark-color: #263238;        /* Cor para texto escuro */
    --light-color: #eceff1;       /* Cor para fundo claro */
    --success-color: #4caf50;     /* Cor para sucesso */
    --warning-color: #ff9800;     /* Cor para avisos */
    --danger-color: #f44336;      /* Cor para erro/perigo */
    --text-color: #37474f;        /* Cor para texto normal */
}
```

### Mensagens e Perguntas

Para personalizar as mensagens e o fluxo de perguntas, modifique a função `processar_etapa()` no arquivo `app.py`. Cada etapa é definida como um caso no fluxo condicional:

```python
# Exemplo de personalização de uma etapa
elif etapa == 'nome':
    if not mensagem.strip():
        return (
            "Ops, não consegui entender seu nome. Poderia repetir por favor?",  # Mensagem personalizada
            'nome',  # Próxima etapa (permanecer na atual)
            []  # Opções de botões
        )
    
    dados_curriculo['informacoes_pessoais']['nome'] = mensagem.strip()
    session['dados_curriculo'] = dados_curriculo
    
    return (
        f"Que nome bonito, {mensagem.strip()}! Agora, qual é o seu sobrenome?",  # Mensagem personalizada
        'sobrenome',  # Próxima etapa
        []  # Opções de botões
    )
```

### Layout do Currículo

Para personalizar o layout do currículo gerado, edite o arquivo `templates/curriculo.html`. Você pode modificar a estrutura HTML e o CSS para alterar a aparência:

```html
<!-- Exemplo de personalização da seção de cabeçalho -->
<div class="header">
    <h1>{{ dados.informacoes_pessoais.nome }} {{ dados.informacoes_pessoais.sobrenome }}</h1>
    <!-- Adicione elementos ou modifique a estrutura aqui -->
    <div class="profissao">{{ dados.informacoes_pessoais.area }}</div>
</div>
```

## ❓ Solução de Problemas

### Problemas Comuns e Soluções

| Problema | Possível Causa | Solução |
|----------|----------------|---------|
| Aplicação não inicia | Porta 5000 em uso | Altere a porta em `app.run(port=5001)` |
| Erros na sessão | Cookies do navegador | Limpe os cookies ou use modo anônimo |
| Prévia não atualiza | Problema de JavaScript | Verifique console do navegador (F12) |
| Erros na geração do PDF | Falha na formatação | Tente navegador alternativo para impressão |
| Dados não são salvos | Permissões de diretório | Verifique permissões na pasta `data/` |

### Depuração

Para habilitar o modo de depuração e obter mensagens de erro detalhadas:

```python
if __name__ == '__main__':
    app.run(debug=True)
```

## 👥 Contribuições

Contribuições são bem-vindas! Para contribuir com o projeto:

1. Faça um fork do repositório
2. Crie uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -m 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 📬 Contato

Para dúvidas, sugestões ou problemas, entre em contato:

- **Email**: contato@ltd.com.br
- **GitHub**: [LTD-2025-1-Cyber-Security-Project](https://github.com/LTD-2025-1-Cyber-Security-Project)
- **Website**: [LTD-2025-1-Cyber-Security-Project](https://www.LTD-2025-1-Cyber-Security-Project.com.br)

---

<p align="center">
  Feito com ❤️ para ajudar pessoas a criarem currículos incríveis
</p>