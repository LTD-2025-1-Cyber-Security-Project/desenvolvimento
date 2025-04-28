from flask import Flask, render_template, request, redirect, url_for, jsonify
import json
import os
import markdown
import bleach

app = Flask(__name__)

# Estrutura de dados para as melhores práticas de e-mail
EMAIL_PRACTICES = [
    {
        "id": 1,
        "category": "Profissional",
        "templates": [
            {
                "id": "prof_intro",
                "title": "E-mail de Apresentação Profissional",
                "description": "Para se apresentar a novos contatos profissionais de forma eficaz",
                "structure": [
                    "Saudação formal com nome do destinatário",
                    "Breve apresentação pessoal",
                    "Motivo do contato de forma clara e concisa",
                    "Proposta de valor ou benefício para o destinatário",
                    "Solicitação de ação específica (reunião, resposta, etc.)",
                    "Agradecimento pelo tempo",
                    "Assinatura profissional completa"
                ],
                "example": """Assunto: Apresentação - [Seu Nome] - Especialista em [Sua Área]

Prezado(a) Sr./Sra. [Nome do Destinatário],

Espero que esteja bem. Meu nome é [Seu Nome], atuo como [Sua Função] na [Sua Empresa/Instituição] há [período], especializado em [área de especialização].

Entro em contato porque [motivo específico do contato, ex: "conheci seu trabalho no evento X" ou "vi sua publicação sobre Y"]. Acredito que podemos [benefício mútuo, ex: "colaborar em projetos de interesse comum" ou "explorar sinergias entre nossas organizações"].

Gostaria de [ação desejada, ex: "agendar uma breve reunião de 15 minutos" ou "conhecer mais sobre suas iniciativas na área Z"].

Estou disponível [disponibilidade] e seria um prazer conversar em um horário conveniente para você.

Agradeço antecipadamente pela atenção e fico no aguardo de seu retorno.

Atenciosamente,

[Seu Nome]
[Sua Função]
[Sua Empresa]
[Seu Contato: telefone/e-mail]
[LinkedIn/Site Profissional]"""
            },
            {
                "id": "job_application",
                "title": "E-mail de Candidatura a Emprego",
                "description": "Para candidatar-se a uma vaga de forma profissional e atrativa",
                "structure": [
                    "Assunto claro mencionando a vaga específica",
                    "Saudação formal ao recrutador/gerente de contratação",
                    "Introdução com menção à vaga e fonte onde foi encontrada",
                    "Resumo de qualificações relevantes para a posição",
                    "Conexão entre experiência e requisitos da vaga",
                    "Demonstração de conhecimento sobre a empresa",
                    "Referência aos anexos (currículo, portfólio)",
                    "Disponibilidade para entrevista",
                    "Agradecimento e encerramento cordial",
                    "Assinatura com contatos"
                ],
                "example": """Assunto: Candidatura - Vaga de [Nome da Vaga] - [Seu Nome]

Prezado(a) Sr./Sra. [Nome do Recrutador, se disponível],

Venho por meio deste e-mail manifestar meu interesse na vaga de [Nome Exato da Vaga] anunciada no [Local onde viu a vaga] no dia [Data, se relevante].

Sou [breve apresentação profissional] com [X anos] de experiência em [áreas relevantes para a posição]. Ao longo da minha trajetória, desenvolvi habilidades em [habilidades-chave solicitadas na vaga], que me permitiram [conquistas relevantes relacionadas aos requisitos].

Durante minha atuação na [empresa anterior ou atual], fui responsável por [projetos/realizações que demonstrem sua capacidade], resultando em [resultados quantificáveis, se possível].

A [Nome da Empresa] me atrai particularmente por [características específicas da empresa que você admira ou que se alinham com seus valores], e acredito que posso contribuir significativamente para [objetivos da empresa ou departamento].

Anexei meu currículo e [outros documentos solicitados] para sua apreciação. Estou disponível para entrevista em horário que lhe for conveniente e posso ser contatado pelo [telefone] ou por este e-mail.

Agradeço a oportunidade e a atenção dispensada à minha candidatura.

Atenciosamente,

[Seu Nome]
[Seu Telefone]
[Seu E-mail]
[LinkedIn]"""
            },
            {
                "id": "meeting_request",
                "title": "E-mail de Solicitação de Reunião",
                "description": "Para agendar reuniões profissionais de forma eficiente",
                "structure": [
                    "Assunto específico mencionando 'reunião' e o tema",
                    "Saudação personalizada",
                    "Contexto claro para a necessidade da reunião",
                    "Objetivo específico do encontro",
                    "Proposta de datas e horários específicos",
                    "Indicação de duração estimada",
                    "Sugestão de formato (presencial/online)",
                    "Menção aos participantes previstos",
                    "Solicitação de confirmação",
                    "Agradecimento pela disponibilidade"
                ],
                "example": """Assunto: Solicitação de Reunião - [Tema da Reunião]

Prezado(a) [Nome],

Espero que esteja bem. Entro em contato para solicitar uma reunião para discutirmos [tema específico da reunião].

O objetivo principal seria [detalhe sobre o que pretende alcançar com a reunião, ex: "alinhar os próximos passos do projeto X" ou "apresentar a proposta para o cliente Y"].

Gostaria de sugerir as seguintes opções de datas e horários:
- [Data 1], às [Horário 1]
- [Data 2], às [Horário 2]
- [Data 3], às [Horário 3]

A reunião deve durar aproximadamente [duração estimada] e sugiro que seja realizada [formato: presencial/videoconferência/chamada].

Além de nós, penso em incluir [outros participantes, se houver] para contribuírem com [motivo da inclusão].

Poderia, por gentileza, confirmar se alguma dessas datas é conveniente para você ou sugerir alternativas que melhor se encaixem em sua agenda?

Agradeço antecipadamente pela sua atenção e disponibilidade.

Atenciosamente,

[Seu Nome]
[Sua Função]
[Contatos]"""
            },
            {
                "id": "proposal_submission",
                "title": "E-mail de Envio de Proposta Comercial",
                "description": "Para enviar propostas comerciais de maneira profissional e persuasiva",
                "structure": [
                    "Assunto claro mencionando 'proposta' e o projeto/serviço",
                    "Saudação personalizada",
                    "Referência à conversação ou reunião anterior",
                    "Resumo do entendimento das necessidades do cliente",
                    "Apresentação breve da solução proposta",
                    "Menção dos diferenciais da sua proposta",
                    "Indicação clara da proposta em anexo",
                    "Próximos passos sugeridos",
                    "Disponibilidade para esclarecimentos",
                    "Agradecimento e encerramento cordial"
                ],
                "example": """Assunto: Proposta Comercial - [Projeto/Serviço] - [Sua Empresa]

Prezado(a) Sr./Sra. [Nome do Cliente],

Conforme nossa [reunião/conversa] do dia [data do contato anterior], tenho o prazer de encaminhar nossa proposta comercial para [nome do projeto ou serviço].

Com base nas necessidades que identificamos sobre [resumo das necessidades do cliente], desenvolvemos uma solução personalizada que contempla [principais aspectos da solução].

Nossa proposta se destaca por [diferenciais competitivos, ex: "metodologia exclusiva", "equipe especializada", "tecnologia de ponta", "prazo otimizado"].

Em anexo, você encontrará o documento completo da proposta, incluindo [elementos incluídos, ex: "escopo detalhado", "cronograma de implementação", "investimento e condições comerciais"].

Sugiro como próximos passos [sugestão concreta, ex: "agendar uma apresentação para esclarecer quaisquer detalhes", "realizar uma reunião com a equipe técnica"].

Estou à disposição para quaisquer esclarecimentos pelo telefone [seu telefone] ou por este e-mail. Podemos também agendar uma videoconferência se preferir.

Agradeço a oportunidade e confiança depositada em nossa empresa.

Cordialmente,

[Seu Nome]
[Sua Função]
[Sua Empresa]
[Seus Contatos]"""
            },
            {
                "id": "follow_up",
                "title": "E-mail de Follow-up Após Reunião",
                "description": "Para dar continuidade aos assuntos discutidos em reuniões",
                "structure": [
                    "Assunto referenciando a reunião anterior",
                    "Saudação informal, mas profissional",
                    "Agradecimento pela reunião",
                    "Resumo dos principais pontos discutidos",
                    "Lista de ações acordadas e responsáveis",
                    "Prazos estabelecidos",
                    "Próximos passos claros",
                    "Oferta de ajuda adicional",
                    "Sugestão da próxima interação",
                    "Encerramento positivo"
                ],
                "example": """Assunto: Acompanhamento - Reunião sobre [Tema] ([Data da Reunião])

Olá [Nome],

Obrigado(a) pelo tempo dedicado à nossa reunião de [hoje/ontem/data] sobre [tema da reunião]. Foi muito produtivo discutirmos [breve menção ao conteúdo principal].

Gostaria de resumir os principais pontos abordados e as ações definidas:

1. [Ponto discutido 1]: [Detalhamento se necessário]
   - Ação: [Ação acordada]
   - Responsável: [Nome do responsável]
   - Prazo: [Data limite]

2. [Ponto discutido 2]: [Detalhamento se necessário]
   - Ação: [Ação acordada]
   - Responsável: [Nome do responsável]
   - Prazo: [Data limite]

3. [Ponto discutido 3]: [Detalhamento se necessário]
   - Ação: [Ação acordada]
   - Responsável: [Nome do responsável]
   - Prazo: [Data limite]

Da minha parte, comprometo-me a [sua ação ou compromisso específico] até [data do seu compromisso].

Estou à disposição para qualquer dúvida ou apoio que precisar nas próximas etapas. Sugiro agendarmos nossa próxima reunião de acompanhamento para [data sugerida] para avaliarmos o progresso.

Novamente, agradeço pela colaboração e produtividade da nossa reunião.

Atenciosamente,

[Seu Nome]
[Sua Função]
[Contatos]"""
            }
        ]
    },
    {
        "id": 2,
        "category": "Marketing e Vendas",
        "templates": [
            {
                "id": "newsletter",
                "title": "Newsletter Mensal",
                "description": "Para manter clientes e leads informados sobre novidades da empresa",
                "structure": [
                    "Assunto cativante e relevante",
                    "Cumprimento sazonal ou personalizado",
                    "Introdução breve sobre o conteúdo do mês",
                    "Seções claramente divididas (notícias, artigos, ofertas)",
                    "Conteúdo de valor (dicas, insights)",
                    "Destaque para novidades ou lançamentos",
                    "Call-to-action claro e destacado",
                    "Calendário de eventos próximos",
                    "Links para redes sociais",
                    "Opção de cancelamento de inscrição (obrigatório)"
                ],
                "example": """Assunto: [Tema do Mês] - Novidades e Dicas Exclusivas de [Mês/Ano]

Olá [Nome do Destinatário],

Bem-vindo(a) à nossa newsletter de [Mês]! Esperamos que este e-mail o(a) encontre bem.

DESTAQUES DESTE MÊS:

📢 NOVIDADES
[Título da novidade principal]
[Breve descrição de 1-2 linhas]
[Link para saber mais] 

📚 ARTIGO EM DESTAQUE
[Título do artigo]
[Resumo curto do artigo]
[Link para ler o artigo completo]

💡 DICA DO MÊS
[Título da dica]
[Explicação rápida da dica]
[Se aplicável, um link para conteúdo relacionado]

🗓️ PRÓXIMOS EVENTOS
- [Data]: [Nome do evento] - [Link para inscrição]
- [Data]: [Nome do evento] - [Link para inscrição]

🔥 OFERTA ESPECIAL
[Descrição da oferta/promoção]
[Detalhes importantes - prazo, condições]
[Botão: APROVEITAR AGORA]

Siga-nos nas redes sociais para mais conteúdo exclusivo:
[Ícones e links para redes sociais]

Ficou com alguma dúvida ou tem sugestões? Responda a este e-mail - adoramos ouvir você!

Atenciosamente,
Equipe [Nome da Empresa]

[Rodapé com endereço físico e opção de cancelar inscrição]"""
            },
            {
                "id": "product_launch",
                "title": "E-mail de Lançamento de Produto",
                "description": "Para anunciar novos produtos ou serviços de forma impactante",
                "structure": [
                    "Assunto que gera curiosidade ou destaca a novidade",
                    "Anúncio empolgante do lançamento",
                    "Descrição dos problemas que o produto resolve",
                    "Principais benefícios e diferenciais",
                    "Especificações técnicas relevantes",
                    "Depoimentos ou casos de sucesso (se disponíveis)",
                    "Preço e condições especiais de lançamento",
                    "Data de disponibilidade",
                    "Call-to-action forte para compra/demonstração",
                    "Perguntas frequentes antecipadas",
                    "Contato para mais informações"
                ],
                "example": """Assunto: 🚀 LANÇAMENTO: Conheça o novo [Nome do Produto] - Disponível AGORA!

Olá [Nome do Cliente],

É COM GRANDE ENTUSIASMO QUE ANUNCIAMOS:

Acaba de chegar o [Nome do Produto]!

Desenvolvemos o [Nome do Produto] depois de ouvirmos atentamente as necessidades de clientes como você que enfrentam [problema que o produto resolve].

O QUE TORNA O [NOME DO PRODUTO] ESPECIAL:

✅ [Benefício principal]: [Breve explicação]
✅ [Benefício secundário]: [Breve explicação]
✅ [Benefício terciário]: [Breve explicação]
✅ [Diferencial exclusivo]: [Breve explicação]

ESPECIFICAÇÕES TÉCNICAS:
- [Especificação 1]
- [Especificação 2]
- [Especificação 3]

O QUE NOSSOS TESTADORES ESTÃO DIZENDO:

"[Depoimento breve de um cliente ou testador]" - [Nome do cliente/testador]

OFERTA ESPECIAL DE LANÇAMENTO:
Por tempo limitado, estamos oferecendo [desconto/bônus/condição especial] para os primeiros [número] compradores.

Preço regular: [Preço regular]
PREÇO DE LANÇAMENTO: [Preço promocional]

Disponível a partir de: [Data de disponibilidade]

[BOTÃO: COMPRAR AGORA] ou [BOTÃO: AGENDAR DEMONSTRAÇÃO]

PERGUNTAS FREQUENTES:
P: [Pergunta comum sobre o produto]
R: [Resposta clara e concisa]

P: [Outra pergunta comum]
R: [Resposta clara e concisa]

Para mais informações, entre em contato conosco:
[E-mail de suporte] | [Telefone]

Não perca esta oportunidade de [benefício principal para o cliente]!

Atenciosamente,
[Seu Nome]
[Sua Função]
[Empresa]"""
            },
            {
                "id": "discount_offer",
                "title": "E-mail de Oferta ou Desconto",
                "description": "Para promover descontos ou ofertas especiais e gerar vendas",
                "structure": [
                    "Assunto que destaca a economia ou benefício",
                    "Destaque visual da oferta/desconto (valor ou %)",
                    "Explicação clara da promoção",
                    "Produtos/serviços incluídos",
                    "Período de validade com senso de urgência",
                    "Condições especiais (se aplicável)",
                    "Imagens atrativas dos produtos",
                    "Código promocional de fácil memorização",
                    "Instruções simples para resgatar",
                    "Call-to-action destacado",
                    "Garantias oferecidas"
                ],
                "example": """Assunto: 🔥 OFERTA EXCLUSIVA: [Desconto]% OFF em [Produtos] - Apenas 48h!

Olá [Nome],

OFERTA ESPECIAL SÓ PARA VOCÊ:

[DESCONTO]% OFF
em [categoria de produtos/serviços]

👉 Por que estamos oferecendo este desconto?
[Motivo da promoção: liquidação sazonal, aniversário da empresa, etc.]

📦 PRODUTOS INCLUÍDOS NA PROMOÇÃO:
- [Produto/categoria 1]
- [Produto/categoria 2]
- [Produto/categoria 3]

⏰ CORRE! OFERTA VÁLIDA ATÉ:
[Data e hora de término] ou [Contagem regressiva]

[IMAGEM ATRATIVA DOS PRODUTOS EM PROMOÇÃO]

COMO APROVEITAR:
1. Acesse nossa [loja/site]: [link]
2. Escolha seus produtos favoritos
3. Insira o código: [CÓDIGO PROMOCIONAL] no checkout
4. Pronto! O desconto será aplicado automaticamente

[BOTÃO GRANDE: APROVEITAR AGORA]

Condições da oferta:
- Válido apenas para compras online
- Não cumulativo com outras promoções
- [Outras condições relevantes]

GARANTIMOS:
✓ Entrega rápida
✓ [Dias] dias para troca ou devolução
✓ Satisfação garantida

Dúvidas? Estamos à disposição!
[E-mail] | [Telefone] | [Chat online]

Equipe [Nome da Empresa]

[Nota sobre política de e-mails e opção de descadastramento]"""
            },
            {
                "id": "event_invitation",
                "title": "E-mail de Convite para Evento",
                "description": "Para convidar clientes e parceiros para eventos corporativos",
                "structure": [
                    "Assunto que menciona 'convite' e o tipo de evento",
                    "Saudação personalizada",
                    "Convite formal e empolgante",
                    "Nome, tema e propósito do evento",
                    "Data, horário e duração",
                    "Local com endereço completo ou link de acesso (se virtual)",
                    "Programação resumida",
                    "Palestrantes ou atrações principais",
                    "Benefícios de participar",
                    "Informações sobre inscrição/confirmação",
                    "Prazo para RSVP",
                    "Contato para dúvidas"
                ],
                "example": """Assunto: Convite: [Nome do Evento] - [Data Principal]

Prezado(a) [Nome],

É com grande satisfação que convidamos você para o [Nome Completo do Evento], um [tipo de evento: webinar, conferência, workshop] exclusivo sobre [tema do evento].

🗓️ DATA E HORÁRIO:
[Dia da semana], [Data] de [Mês]
Das [hora de início] às [hora de término]
[Fuso horário, se relevante]

📍 LOCAL:
[Se presencial: Nome do local, Endereço completo, Informações sobre estacionamento]
[Se online: "Evento online via (plataforma). O link de acesso será enviado após confirmação."]

📋 PROGRAMAÇÃO:
[Hora] - [Atividade/Palestra 1]
[Hora] - [Atividade/Palestra 2]
[Hora] - [Atividade/Palestra 3]
[Hora] - [Networking/Coffee break/Encerramento]

👥 PALESTRANTES:
- [Nome do Palestrante 1] - [Cargo/Empresa] - [Breve bio]
- [Nome do Palestrante 2] - [Cargo/Empresa] - [Breve bio]

💡 POR QUE PARTICIPAR:
- [Benefício 1 para o participante]
- [Benefício 2 para o participante]
- [Benefício 3 para o participante]

[BOTÃO: CONFIRMAR PARTICIPAÇÃO]

Por favor, confirme sua presença até [data limite para RSVP] através do botão acima ou respondendo a este e-mail.

[Se aplicável: "O evento tem vagas limitadas, garanta a sua!"]
[Se aplicável: "Investimento: [valor] - [condições de pagamento]"]

Para mais informações ou dúvidas, entre em contato:
[Nome da pessoa de contato]
[E-mail] | [Telefone]

Esperamos muito por sua presença!

Atenciosamente,
[Seu Nome]
[Sua Função]
[Empresa Organizadora]"""
            },
            {
                "id": "testimonial_request",
                "title": "E-mail de Solicitação de Depoimento",
                "description": "Para solicitar depoimentos de clientes satisfeitos",
                "structure": [
                    "Assunto personalizado mencionando feedback",
                    "Agradecimento pela confiança e parceria",
                    "Contexto sobre a importância dos depoimentos",
                    "Solicitação clara e direta do depoimento",
                    "Sugestões de pontos a abordar (opcional)",
                    "Indicação do formato preferido",
                    "Informação sobre onde o depoimento será usado",
                    "Menção à permissão de uso",
                    "Prazo sugerido (não muito longo)",
                    "Oferta de incentivo (opcional)",
                    "Agradecimento antecipado"
                ],
                "example": """Assunto: [Nome], sua opinião sobre [produto/serviço] é valiosa para nós

Olá [Nome],

Espero que esteja tudo bem com você. Gostaria de começar agradecendo por ser nosso cliente e pela confiança depositada em nossos [produtos/serviços].

Os depoimentos de clientes são uma parte fundamental da nossa estratégia de crescimento, pois ajudam potenciais clientes a entender o valor real que oferecemos através das experiências de pessoas como você.

Gostaríamos muito de contar com seu depoimento sobre sua experiência com [produto/serviço específico]. Sua opinião sincera seria extremamente valiosa para nós.

Caso aceite nosso convite, aqui estão alguns pontos que você poderia abordar (totalmente opcional):
- O que o motivou a escolher nossa [empresa/produto/serviço]
- Quais problemas ou desafios foram solucionados
- Quais resultados ou benefícios você obteve
- O que mais gostou na experiência conosco

O depoimento pode ser enviado por escrito (respondendo a este e-mail) ou, se preferir, podemos agendar uma rápida videochamada para gravar seu feedback (5-10 minutos).

Com sua permissão, utilizaremos seu depoimento em nosso [site/materiais de marketing/redes sociais], sempre destacando sua [empresa/nome] com seu devido crédito.

Seria possível enviar seu feedback até [data - idealmente 7-10 dias no futuro]?

[Se aplicável: "Como forma de agradecimento pela sua contribuição, gostaríamos de oferecer (incentivo: desconto, acesso antecipado a novos recursos, etc.)"]

Desde já agradecemos imensamente sua atenção e apoio ao nosso crescimento.

Cordialmente,

[Seu Nome]
[Sua Função]
[Sua Empresa]
[Seus Contatos]"""
            }
        ]
    },
    {
        "id": 3,
        "category": "Relacionamento com Clientes",
        "templates": [
            {
                "id": "welcome_email",
                "title": "E-mail de Boas-vindas",
                "description": "Para dar as boas-vindas a novos clientes ou assinantes",
                "structure": [
                    "Assunto caloroso de boas-vindas",
                    "Saudação personalizada",
                    "Agradecimento entusiasmado pela adesão/compra",
                    "Breve reafirmação dos benefícios",
                    "Instruções claras de próximos passos",
                    "Recursos iniciais recomendados",
                    "Informações de acesso ou login (se aplicável)",
                    "Apresentação da equipe de suporte",
                    "Canais de comunicação disponíveis",
                    "Expectativa para a jornada futura",
                    "Assinatura calorosa da equipe/fundador"
                ],
                "example": """Assunto: Bem-vindo(a) à [Nome da Empresa]! Seu próximo passo para [benefício principal]

Olá [Nome],

🎉 BEM-VINDO(A) À FAMÍLIA [NOME DA EMPRESA]! 🎉

Estamos extremamente felizes por você ter escolhido [nossa empresa/nosso produto/serviço] para [benefício principal que o cliente busca].

Você acaba de dar um passo importante para [objetivo que o cliente quer alcançar]. Nós valorizamos muito a confiança que depositou em nós e estamos comprometidos em superar suas expectativas.

SEUS PRÓXIMOS PASSOS:

1️⃣ [Primeira ação recomendada, ex: "Configure sua conta"] - [Link ou instrução]
2️⃣ [Segunda ação, ex: "Explore nossos recursos"] - [Link ou instrução]
3️⃣ [Terceira ação, ex: "Baixe nosso aplicativo"] - [Link ou instrução]

RECURSOS PARA COMEÇAR:
- [Recurso 1, ex: "Guia de Introdução"] - [Link]
- [Recurso 2, ex: "Vídeos Tutoriais"] - [Link]
- [Recurso 3, ex: "Perguntas Frequentes"] - [Link]

[Se aplicável: "Suas informações de acesso:
Login: [login do usuário]
Senha: [senha temporária ou instrução para defini-la]
Link de acesso: [URL]"]

PRECISANDO DE AJUDA?
Nossa equipe de suporte está pronta para ajudar você:
📧 E-mail: [e-mail de suporte]
📞 Telefone: [número de suporte]
💬 Chat ao vivo: [horário de disponibilidade]

Estamos ansiosos para acompanhar sua jornada conosco. Não hesite em entrar em contato se tiver dúvidas ou precisar de qualquer assistência.

Seja bem-vindo(a) e obrigado(a) por escolher a [Nome da Empresa]!

Atenciosamente,

[Nome do CEO/Fundador ou do Gerente de Relacionamento]
[Cargo]
[Nome da Empresa]

P.S.: Siga-nos nas redes sociais para dicas e novidades: [Links das redes sociais]"""
            },
            {
                "id": "support_response",
                "title": "Resposta de Suporte ao Cliente",
                "description": "Para responder a dúvidas ou solicitações de suporte técnico",
                "structure": [
                    "Assunto referenciando o ticket/problema",
                    "Agradecimento pelo contato",
                    "Empatia com o problema relatado",
                    "Confirmação de entendimento da questão",
                    "Resposta clara e objetiva",
                    "Instruções passo a passo (se aplicável)",
                    "Screenshots ou links de suporte (quando necessário)",
                    "Verificação se a resposta atende completamente",
                    "Próximos passos sugeridos",
                    "Disponibilidade para esclarecimentos adicionais",
                    "Tempo esperado para resolução (se em aberto)"
                ],
                "example": """Assunto: Re: [Nº do Ticket] - [Resumo breve do problema reportado]

Olá [Nome do Cliente],

Obrigado por entrar em contato com o suporte da [Nome da Empresa]. Agradecemos a oportunidade de poder ajudá-lo(a).

Compreendo a frustração que a situação do [problema relatado] pode causar, e quero assegurar que estamos aqui para resolver isso o quanto antes.

Com base nas informações que você forneceu, entendo que [recapitulação do problema com palavras próprias para confirmar entendimento].

SOLUÇÃO:

[Opção 1 - Se for uma solução direta:]
Para resolver este problema, por favor siga estes passos:

1. [Instrução passo a passo 1]
2. [Instrução passo a passo 2]
3. [Instrução passo a passo 3]

[Incluir screenshot ou imagem ilustrativa se necessário]

[Opção 2 - Se for uma investigação em andamento:]
Nossa equipe técnica está investigando ativamente seu caso. Aqui está o que sabemos até agora:
- [Informação sobre a causa possível]
- [Status atual da investigação]
- [Prazo estimado para resolução]: [data/hora estimada]

Esta solução resolveu completamente seu problema? Se sim, ficamos felizes em ajudar! Caso contrário, por favor, responda a este e-mail com detalhes adicionais para que possamos continuar a investigação.

Se surgir qualquer outra dúvida ou se precisar de esclarecimentos adicionais, não hesite em responder a este e-mail ou entrar em contato pelo telefone [número de suporte].

Agradecemos sua paciência e compreensão.

Atenciosamente,

[Seu Nome]
[Sua Função]
[Equipe de Suporte da Empresa]
[Contatos diretos]"""
            },
            {
                "id": "feedback_request",
                "title": "E-mail de Solicitação de Feedback",
                "description": "Para pedir feedback sobre produtos, serviços ou experiências",
                "structure": [
                    "Assunto que menciona 'feedback' e o produto/serviço",
                    "Saudação personalizada",
                    "Agradecimento pela confiança",
                    "Explicação da importância do feedback",
                    "Solicitação específica e clara",
                    "Menção à brevidade do processo",
                    "Link para formulário ou pesquisa",
                    "Tempo estimado para completar",
                    "Incentivo ou recompensa (opcional)",
                    "Garantia de confidencialidade (se aplicável)",
                    "Agradecimento antecipado",
                    "Assinatura pessoal"
                ],
                "example": """Assunto: Sua opinião é importante: feedback sobre [produto/serviço]

Olá [Nome do Cliente],

Esperamos que esteja aproveitando sua experiência com [produto/serviço]. Agradecemos muito por escolher a [Nome da Empresa].

Estamos constantemente buscando melhorar nossos [produtos/serviços] e sua opinião é fundamental nesse processo. Como um cliente valioso, seu feedback nos ajudará a entender o que estamos fazendo bem e onde podemos melhorar.

Gostaríamos de convidá-lo(a) a participar de uma breve pesquisa de satisfação. São apenas [número] perguntas que levarão aproximadamente [2-3/5] minutos do seu tempo.

[BOTÃO: COMPARTILHAR MEU FEEDBACK]

Ou acesse diretamente: [link da pesquisa]

[Se aplicável: "Como agradecimento pela sua participação, oferecemos [desconto/crédito/brinde/sorteio] como forma de demonstrar nossa gratidão."]

Todas as respostas são confidenciais e serão utilizadas exclusivamente para aprimorar nossos [produtos/serviços] e sua experiência conosco.

Agradecemos antecipadamente por dedicar um momento para nos ajudar a melhorar.

Atenciosamente,

[Seu Nome]
[Sua Função]
[Nome da Empresa]
[Seus contatos]

P.S.: Se preferir compartilhar seu feedback diretamente ou tiver alguma dúvida, sinta-se à vontade para responder a este e-mail."""
            },
            {
                "id": "apology_email",
                "title": "E-mail de Pedido de Desculpas",
                "description": "Para se desculpar por erros, problemas ou inconvenientes",
                "structure": [
                    "Assunto que reconhece o problema sem ser negativo",
                    "Saudação empática",
                    "Reconhecimento imediato do problema",
                    "Pedido de desculpas sincero e direto",
                    "Explicação breve (sem justificativas excessivas)",
                    "Ações que estão sendo tomadas para resolver",
                    "Medidas para evitar recorrência",
                    "Compensação ou gesto de boa vontade",
                    "Reafirmação do valor do cliente",
                    "Disponibilidade para qualquer necessidade adicional",
                    "Encerramento positivo olhando para o futuro"
                ],
                "example": """Assunto: Um pedido sincero de desculpas pelo ocorrido com [problema específico]

Prezado(a) [Nome do Cliente],

Gostaria de me dirigir pessoalmente a você sobre o [problema específico] que ocorreu em [data/momento do incidente]. Antes de tudo, quero pedir sinceras desculpas pelo inconveniente e frustração que isso possa ter causado.

Compreendemos completamente o impacto que isso teve em [consequência para o cliente] e assumimos total responsabilidade pelo ocorrido.

O que aconteceu:
[Breve explicação do que aconteceu, sem transferir culpa ou fazer desculpas excessivas]

O que estamos fazendo para resolver:
- [Ação imediata que foi tomada]
- [Status atual da resolução]
- [Quando o cliente pode esperar a resolução completa]

Para garantir que isso não aconteça novamente:
- [Medida preventiva 1]
- [Medida preventiva 2]

Como um gesto de reconhecimento pelo transtorno causado, gostaríamos de oferecer [compensação: desconto, crédito, upgrade, serviço gratuito, etc.]. Sabemos que isso não desfaz o ocorrido, mas esperamos demonstrar nosso comprometimento com sua satisfação.

Valorizamos muito você como cliente e nos esforçamos diariamente para oferecer a melhor experiência possível. Seu feedback é extremamente importante para nós.

Se tiver qualquer dúvida adicional ou precisar de mais assistência, estou pessoalmente à disposição para ajudar. Você pode me contatar diretamente em [seu e-mail pessoal] ou pelo telefone [seu número direto].

Agradecemos sua compreensão e esperamos continuar a atendê-lo(a) com o nível de excelência que você merece.

Atenciosamente,

[Seu Nome]
[Cargo de liderança - preferencialmente Gerente ou Diretor]
[Nome da Empresa]
[Seus contatos diretos]"""
            },
            {
                "id": "renewal_reminder",
                "title": "E-mail de Lembrete de Renovação",
                "description": "Para lembretes de renovação de assinaturas ou serviços",
                "structure": [
                    "Assunto claro indicando 'renovação' e o serviço",
                    "Saudação personalizada",
                    "Lembrete amigável sobre a data de renovação",
                    "Resumo dos benefícios recebidos até o momento",
                    "Detalhes da renovação (data, valor, período)",
                    "Informações de pagamento",
                    "Processo de renovação (automático ou manual)",
                    "Benefícios de continuar",
                    "Novas funcionalidades ou upgrades disponíveis",
                    "Opções disponíveis (renovar, upgrade, downgrade, cancelar)",
                    "Contato para dúvidas",
                    "Agradecimento pela confiança contínua"
                ],
                "example": """Assunto: Lembrete de Renovação: Sua assinatura de [Serviço] expira em [X] dias

Olá [Nome do Cliente],

Esperamos que esteja aproveitando os benefícios do seu [plano/serviço] da [Nome da Empresa]. Este é um lembrete amigável de que sua assinatura atual expirará em [X] dias, em [data exata de expiração].

RESUMO DO SEU PLANO ATUAL:
- Plano: [Nome do plano]
- Data de início: [Data de início]
- Data de expiração: [Data de expiração]
- Valor da renovação: [Valor] [periodicidade: mensal/anual]

Durante este período conosco, você aproveitou:
- [Benefício/uso 1, ex: "Acesso a X recursos"]
- [Benefício/uso 2, ex: "Download de Y conteúdos"]
- [Benefício/uso 3, ex: "Suporte prioritário Z vezes"]

[Se aplicável: "Sua renovação será processada automaticamente em [data] utilizando o método de pagamento registrado em sua conta. Não é necessária nenhuma ação da sua parte para continuar aproveitando nossos serviços."]

[Se renovação manual: "Para renovar sua assinatura, basta clicar no botão abaixo:"]

[BOTÃO: RENOVAR AGORA]

NOVIDADES PARA O PRÓXIMO PERÍODO:
Como assinante que renova, você terá acesso a:
- [Nova funcionalidade ou benefício 1]
- [Nova funcionalidade ou benefício 2]
- [Oferta exclusiva para quem renova]

OUTRAS OPÇÕES:
- [Link: Fazer upgrade para um plano superior]
- [Link: Ajustar seu plano atual]
- [Link: Gerenciar métodos de pagamento]
- [Link: Cancelar renovação automática]

Se precisar de qualquer assistência ou tiver dúvidas sobre sua renovação, nossa equipe está à disposição para ajudar:
[E-mail de contato] | [Telefone] | [Horário de atendimento]

Agradecemos muito por sua confiança contínua na [Nome da Empresa]. Estamos comprometidos em continuar oferecendo [benefício principal do serviço] para você.

Atenciosamente,

[Seu Nome]
[Sua Função]
[Nome da Empresa]"""
            },
            {
                "id": "thank_you_email",
                "title": "E-mail de Agradecimento",
                "description": "Para agradecer clientes por compras, feedback ou parcerias",
                "structure": [
                    "Assunto expressando gratidão específica",
                    "Saudação personalizada e calorosa",
                    "Agradecimento sincero e específico",
                    "Reconhecimento do valor da ação do cliente",
                    "Impacto positivo para a empresa",
                    "Pequena história ou contexto pessoal (opcional)",
                    "Reafirmação do compromisso com o cliente",
                    "Menção aos próximos passos (se aplicável)",
                    "Convite para feedback adicional",
                    "Gesto de agradecimento (desconto futuro, etc.)",
                    "Encerramento caloroso"
                ],
                "example": """Assunto: Um sincero agradecimento pela sua [compra/feedback/indicação]

Olá [Nome],

Gostaria de expressar meu sincero agradecimento pela sua recente [compra/feedback/indicação]. Gestos como o seu são o que dão sentido ao nosso trabalho diário.

Sua escolha por [produto/serviço] não é apenas uma transação para nós - representa uma confiança que valorizamos profundamente. Cada [cliente/feedback/indicação] nos ajuda a crescer e melhorar continuamente.

[Elemento pessoal, ex: "Quando fundamos a empresa há X anos, nossa visão era justamente criar um relacionamento genuíno com clientes como você."]

Estamos comprometidos em garantir que sua experiência com a [Nome da Empresa] seja sempre excepcional, e seu apoio nos motiva a continuar buscando a excelência em tudo o que fazemos.

[Se aplicável: "Seus produtos serão enviados hoje e devem chegar em [estimativa de entrega]. Você receberá atualizações de rastreamento por e-mail."]

Se houver qualquer forma de melhorarmos ainda mais sua experiência conosco, ficaríamos muito gratos em ouvir suas sugestões.

Como um pequeno gesto de nossa gratidão, gostaríamos de oferecer [desconto especial/acesso antecipado/brinde] para sua próxima compra. Basta usar o código [CÓDIGO] em seu próximo pedido.

Mais uma vez, muito obrigado por escolher a [Nome da Empresa]. Estamos ansiosos para continuar atendendo você.

Com sincera gratidão,

[Seu Nome]
[Sua Função - preferencialmente CEO/Fundador para toque pessoal]
[Nome da Empresa]
[Contato pessoal, se apropriado]"""
            }
        ]
    },
    {
        "id": 4,
        "category": "Comunicação Interna",
        "templates": [
            {
                "id": "team_announcement",
                "title": "E-mail de Anúncio para Equipe",
                "description": "Para comunicar mudanças, novidades ou diretrizes à equipe interna",
                "structure": [
                    "Assunto claro e direto sobre o anúncio",
                    "Saudação inclusiva para toda a equipe",
                    "Anúncio principal logo no início",
                    "Contexto da mudança ou decisão",
                    "Detalhes relevantes e cronograma",
                    "Impacto esperado para a equipe/empresa",
                    "Benefícios da mudança",
                    "Instruções específicas, se necessárias",
                    "Canal para dúvidas ou feedback",
                    "Agradecimento pela adaptação/compreensão",
                    "Encerramento positivo"
                ],
                "example": """Assunto: Anúncio: [Mudança/Novidade/Implementação] a partir de [Data]

Prezada Equipe,

Gostaríamos de anunciar que [anúncio principal, ex: "implementaremos uma nova plataforma de gerenciamento de projetos" ou "mudaremos para o novo escritório" ou "reestruturaremos o departamento X"].

CONTEXTO:
Esta decisão foi tomada após [contexto da decisão, ex: "uma análise detalhada das nossas necessidades operacionais" ou "feedback recebido nas últimas reuniões departamentais"]. O objetivo principal é [objetivo da mudança, ex: "aumentar nossa eficiência", "melhorar o ambiente de trabalho", "otimizar nossos processos"].

DETALHES DA IMPLEMENTAÇÃO:
- Data de início: [Data]
- Fases de implementação: [Cronograma resumido]
- Departamentos afetados: [Departamentos específicos ou "Toda a empresa"]
- Responsáveis: [Nomes dos responsáveis]

IMPACTO ESPERADO:
Esta mudança trará [impactos positivos esperados], embora possamos enfrentar [possíveis desafios iniciais] durante o período de transição.

O QUE ISSO SIGNIFICA PARA VOCÊ:
- [Consequência/instrução 1]
- [Consequência/instrução 2]
- [Consequência/instrução 3]

PRÓXIMOS PASSOS:
1. [Primeiro passo, ex: "Sessões de treinamento serão agendadas na próxima semana"]
2. [Segundo passo]
3. [Terceiro passo]

Se você tiver dúvidas ou sugestões sobre esta mudança, não hesite em contatar [nome da pessoa/departamento responsável] pelo e-mail [e-mail] ou agendar uma conversa diretamente.

Contamos com a colaboração de todos para tornar esta transição o mais tranquila possível. Agradecemos antecipadamente pelo seu apoio e compreensão.

Juntos, continuaremos fortalecendo nossa empresa e alcançando novos patamares de sucesso.

Atenciosamente,

[Nome do Diretor/Gestor]
[Cargo]
[Nome da Empresa]"""
            },
            {
                "id": "project_update",
                "title": "E-mail de Atualização de Projeto",
                "description": "Para informar stakeholders sobre o progresso de projetos",
                "structure": [
                    "Assunto com nome do projeto e tipo de atualização",
                    "Saudação direcionada às partes interessadas",
                    "Resumo executivo do status (1-2 frases)",
                    "Detalhamento de progresso por área/objetivo",
                    "Métricas e resultados alcançados",
                    "Cronograma atualizado",
                    "Desafios encontrados e soluções",
                    "Próximas etapas com prazos",
                    "Necessidades ou pendências",
                    "Apreciação ao time",
                    "Disponibilidade para esclarecimentos"
                ],
                "example": """Assunto: Atualização do Projeto [Nome do Projeto] - [Período/Semana/Mês]

Prezados Stakeholders,

Segue abaixo a atualização de status do projeto [Nome do Projeto] referente a [período da atualização].

📋 RESUMO EXECUTIVO:
O projeto está atualmente [situação: "conforme planejado" / "com atrasos em X" / "adiantado em Y"] com [X]% das entregas concluídas. [Frase resumindo principais avanços ou desafios].

✅ PROGRESSO POR ÁREA:

1. [Área/Objetivo 1]:
   - Concluído: [tarefas finalizadas]
   - Em andamento: [tarefas em progresso] ([X]% concluído)
   - Pendente: [tarefas ainda não iniciadas]

2. [Área/Objetivo 2]:
   - Concluído: [tarefas finalizadas]
   - Em andamento: [tarefas em progresso] ([X]% concluído)
   - Pendente: [tarefas ainda não iniciadas]

📊 MÉTRICAS E RESULTADOS:
- [Métrica 1]: [Resultado atual] ([comparação com meta])
- [Métrica 2]: [Resultado atual] ([comparação com meta])
- [Métrica 3]: [Resultado atual] ([comparação com meta])

⏱️ CRONOGRAMA:
- Início do projeto: [data inicial]
- Status atual: [X dias/semanas] completados, [Y dias/semanas] restantes
- Data prevista de conclusão: [data final prevista]
- Ajustes no cronograma: [alterações, se houver]

🚧 DESAFIOS E SOLUÇÕES:
- [Desafio 1]: [Solução implementada ou proposta]
- [Desafio 2]: [Solução implementada ou proposta]

⏭️ PRÓXIMAS ETAPAS:
1. [Próxima etapa 1] - Responsável: [Nome] - Prazo: [Data]
2. [Próxima etapa 2] - Responsável: [Nome] - Prazo: [Data]
3. [Próxima etapa 3] - Responsável: [Nome] - Prazo: [Data]

⚠️ PENDÊNCIAS QUE REQUEREM ATENÇÃO:
- [Pendência 1] - Necessitamos [ação necessária] até [prazo]
- [Pendência 2] - Necessitamos [ação necessária] até [prazo]

Gostaria de agradecer especialmente a [nomes ou equipes] pelo excelente trabalho em [área específica ou conquista].

Nossa próxima reunião de acompanhamento está agendada para [data e hora]. Caso tenham dúvidas ou precisem de esclarecimentos adicionais antes disso, estou à disposição.

Atenciosamente,

[Seu Nome]
[Sua Função]
[Contatos]"""
            },
            {
                "id": "meeting_minutes",
                "title": "E-mail de Ata de Reunião",
                "description": "Para documentar e compartilhar decisões e ações pós-reunião",
                "structure": [
                    "Assunto com nome/tipo de reunião e data",
                    "Saudação aos participantes",
                    "Agradecimento pela presença/participação",
                    "Resumo do propósito da reunião",
                    "Lista de participantes presentes e ausentes",
                    "Tópicos discutidos com decisões tomadas",
                    "Lista clara de ações (responsáveis e prazos)",
                    "Itens pendentes para próxima reunião",
                    "Data e pauta preliminar da próxima reunião",
                    "Solicitação de correções/adições à ata",
                    "Anexos ou links relevantes",
                    "Encerramento cordial"
                ],
                "example": """Assunto: Ata de Reunião - [Tipo/Nome da Reunião] - [Data]

Prezados participantes,

Agradeço a presença e contribuições de todos na reunião de [tipo/nome da reunião] realizada em [data] das [horário de início] às [horário de término].

Esta mensagem documenta os principais pontos discutidos, decisões tomadas e ações definidas para acompanhamento.

📝 RESUMO DA REUNIÃO:
- Propósito: [objetivo principal da reunião]
- Local: [local físico ou plataforma virtual]

👥 PARTICIPANTES:
- Presentes: [lista de nomes dos presentes]
- Ausências justificadas: [lista de nomes, se aplicável]

📋 TÓPICOS DISCUTIDOS E DECISÕES:

1. [Tópico 1]
   • Pontos discutidos: [resumo da discussão]
   • Decisão: [decisão tomada]
   • Observações: [informações adicionais relevantes]

2. [Tópico 2]
   • Pontos discutidos: [resumo da discussão]
   • Decisão: [decisão tomada]
   • Observações: [informações adicionais relevantes]

3. [Tópico 3]
   • Pontos discutidos: [resumo da discussão]
   • Decisão: [decisão tomada]
   • Observações: [informações adicionais relevantes]

✅ AÇÕES DEFINIDAS:

| Ação | Responsável | Prazo | Status |
|------|-------------|-------|--------|
| [Descrição da ação 1] | [Nome] | [Data] | Pendente |
| [Descrição da ação 2] | [Nome] | [Data] | Pendente |
| [Descrição da ação 3] | [Nome] | [Data] | Pendente |

⏭️ TÓPICOS PARA PRÓXIMA REUNIÃO:
- [Tópico pendente 1]
- [Tópico pendente 2]
- [Tópico sugerido]

📅 PRÓXIMA REUNIÃO:
- Data: [data da próxima reunião]
- Horário: [horário]
- Local/Plataforma: [local ou plataforma]
- Pauta preliminar: [tópicos principais]

📎 ANEXOS:
- [Nome do documento 1]: [link ou referência]
- [Nome do documento 2]: [link ou referência]

Por favor, caso identifiquem qualquer incorreção ou desejem adicionar algum ponto importante que não foi incluído nesta ata, respondam a este e-mail até [prazo, geralmente 24-48h] para as devidas correções.

Agradeço novamente a participação de todos e o comprometimento com os próximos passos.

Atenciosamente,

[Seu Nome]
[Sua Função]
[Contatos]"""
            },
            {
                "id": "onboarding_email",
                "title": "E-mail de Onboarding para Novos Colaboradores",
                "description": "Para dar as boas-vindas e orientações iniciais a novos funcionários",
                "structure": [
                    "Assunto caloroso de boas-vindas",
                    "Saudação entusiasmada e personalizada",
                    "Boas-vindas oficial à empresa/equipe",
                    "Expressão de entusiasmo pela contratação",
                    "Informações práticas para o primeiro dia",
                    "Horário, local e pessoa de contato",
                    "Documentos ou preparativos necessários",
                    "Visão geral da primeira semana",
                    "Recursos iniciais e materiais de leitura",
                    "Apresentação breve da cultura e valores",
                    "Detalhes sobre o processo de integração",
                    "Contatos importantes",
                    "Encerramento acolhedor"
                ],
                "example": """Assunto: Boas-vindas à [Nome da Empresa], [Nome do Novo Colaborador]!

Olá [Nome],

É com grande alegria que dou as boas-vindas oficiais à equipe da [Nome da Empresa]! Estamos verdadeiramente empolgados por você ter aceitado se juntar a nós e mal podemos esperar para ver as contribuições que você trará.

Toda a equipe está ansiosa para conhecê-lo(a) e trabalhar com você. Sua experiência em [área de expertise/formação] será extremamente valiosa para nossa missão de [missão breve da empresa].

🗓️ SEU PRIMEIRO DIA - INFORMAÇÕES PRÁTICAS:

- Data: [data de início]
- Horário: [horário de chegada recomendado]
- Local: [endereço completo ou link para reunião virtual]
- Contato de recepção: [nome e cargo], que estará esperando por você
- Código de vestimenta: [orientações sobre vestimenta]

📝 O QUE TRAZER:
- [Documento 1]
- [Documento 2]
- [Outro item necessário]

🗓️ VISÃO GERAL DA PRIMEIRA SEMANA:
Durante seus primeiros dias, você participará de várias sessões de integração para conhecer melhor nossa empresa, equipe e seu papel. Aqui está um breve resumo:

- Dia 1: Boas-vindas, tour, configurações iniciais
- Dia 2: Treinamentos de sistemas, políticas da empresa
- Dia 3: Reuniões departamentais, entendimento do fluxo de trabalho
- Dia 4-5: Imersão específica na sua função e primeiros projetos

📚 PARA COMEÇAR:
Para ajudá-lo(a) a se familiarizar com nosso trabalho antes do primeiro dia, separamos alguns materiais:
- [Link para manual do colaborador]
- [Link para apresentação da empresa]
- [Link para documentos relevantes à função]

💼 NOSSA CULTURA:
Na [Nome da Empresa], valorizamos [2-3 valores principais]. Trabalhamos em um ambiente [características do ambiente: colaborativo, dinâmico, etc.] onde [aspecto importante da cultura].

🔑 CONTATOS IMPORTANTES:
- Seu gestor direto: [Nome], [Cargo] - [E-mail] - [Telefone]
- RH: [Nome], [Cargo] - [E-mail] - [Telefone]
- Suporte de TI: [Nome/Departamento] - [E-mail] - [Telefone]

Se tiver qualquer dúvida antes do seu primeiro dia, sinta-se à vontade para entrar em contato comigo ou com [nome da pessoa de RH/gestor].

Estamos entusiasmados para tê-lo(a) em nossa equipe e ansiosos para o sucesso que construiremos juntos!

Calorosas boas-vindas,

[Seu Nome]
[Sua Função]
[Nome da Empresa]
[Seus Contatos]"""
            },
            {
                "id": "holiday_notice",
                "title": "E-mail de Comunicado de Feriado/Recesso",
                "description": "Para informar colaboradores sobre feriados e períodos de recesso",
                "structure": [
                    "Assunto claro mencionando o feriado/recesso",
                    "Saudação geral",
                    "Anúncio do feriado ou período de recesso",
                    "Datas específicas de início e fim",
                    "Impacto nas operações",
                    "Setores ou serviços que permanecerão ativos",
                    "Instruções para finalizações antes do recesso",
                    "Contatos de emergência durante o período",
                    "Detalhes sobre retorno às atividades",
                    "Desejo de bom descanso",
                    "Agradecimento pelo trabalho/dedicação",
                    "Encerramento positivo"
                ],
                "example": """Assunto: Comunicado: Feriado/Recesso de [Nome do Feriado/Recesso] - [Ano]

Prezados Colaboradores,

Informamos que em razão do [nome do feriado/festividade/recesso], nossa empresa estará fechada para o período de descanso conforme detalhamento abaixo.

📅 PERÍODO DE RECESSO:
- Início: [data e hora de início]
- Retorno: [data e hora de retorno às atividades]
- Total: [número de dias]

🏢 FUNCIONAMENTO DURANTE O PERÍODO:
- Setores fechados: [setores que não funcionarão]
- Setores com operação limitada: [setores com funcionamento parcial e horários]
- Setores com operação normal: [setores que manterão funcionamento regular]

✅ PREPARATIVOS PARA O RECESSO:
Solicitamos a todos que, antes do início do recesso:
1. [Ação necessária 1, ex: "Finalizem relatórios pendentes"]
2. [Ação necessária 2, ex: "Atualizem o status dos projetos no sistema"]
3. [Ação necessária 3, ex: "Configurem mensagem automática de e-mail"]

🆘 CONTATOS DE EMERGÊNCIA:
Durante o período, caso surja alguma situação emergencial, os seguintes contatos estarão disponíveis:
- [Área/Setor 1]: [Nome] - [Telefone] - [E-mail]
- [Área/Setor 2]: [Nome] - [Telefone] - [E-mail]

▶️ RETORNO ÀS ATIVIDADES:
No dia [data de retorno], retomaremos nossas atividades normalmente às [horário] no formato habitual. Agendas, compromissos e prazos serão retomados conforme programado anteriormente.

Desejamos a todos um excelente [feriado/recesso], com momentos de descanso e renovação ao lado de seus familiares e entes queridos.

Aproveitamos para agradecer o comprometimento e dedicação de cada um durante este [período/trimestre/ano], que têm sido fundamentais para os resultados alcançados pela nossa empresa.

Atenciosamente,

[Nome do Responsável]
[Cargo - geralmente Diretor ou Gestor de RH]
[Nome da Empresa]"""
            }
        ]
    },
    {
        "id": 5,
        "category": "E-mails Formais e Institucionais",
        "templates": [
            {
                "id": "formal_invitation",
                "title": "Convite Formal para Evento Institucional",
                "description": "Para convites formais a eventos corporativos ou institucionais",
                "structure": [
                    "Assunto formal mencionando 'convite' e o evento",
                    "Saudação formal com nome e cargo",
                    "Breve apresentação da instituição anfitriã",
                    "Declaração formal do convite",
                    "Nome completo e descrição do evento",
                    "Data, horário e local com detalhes completos",
                    "Objetivo e importância do evento",
                    "Programação resumida",
                    "Instruções para confirmação de presença",
                    "Data limite para RSVP",
                    "Informações adicionais (código de vestimenta, etc.)",
                    "Encerramento respeitoso e formal",
                    "Assinatura oficial da instituição/autoridade"
                ],
                "example": """Assunto: Convite Oficial - [Nome do Evento] - [Data]

Exmo(a). Sr(a). [Nome Completo],
[Cargo]
[Organização]

Em nome de [Nome da Instituição/Empresa Anfitriã], temos a honra de convidar Vossa Senhoria para o [Nome Completo do Evento], uma [descrição breve: conferência/cerimônia/seminário] que celebra [objetivo ou tema do evento].

DATA E HORÁRIO:
[Dia da semana], [Data] de [Mês] de [Ano]
Das [Hora de início] às [Hora de término]
[Fuso horário, se relevante]

LOCAL:
[Nome do Local]
[Endereço completo]
[Informações complementares - andar, sala, referências]

O evento tem como objetivo [propósito principal do evento] e contará com a presença de [personalidades ou instituições importantes]. Sua presença será de grande relevância para [motivo da importância da presença do convidado].

PROGRAMAÇÃO:

[Hora] - [Atividade de abertura]
[Hora] - [Atividade principal]
[Hora] - [Intervalo/Coquetel/Almoço]
[Hora] - [Atividade de encerramento]

Solicitamos a gentileza de confirmar sua presença até o dia [data limite para RSVP] através do [método de confirmação: e-mail, telefone, formulário] [contato para confirmação].

INFORMAÇÕES ADICIONAIS:
- Código de vestimenta: [traje sugerido]
- Estacionamento: [informações sobre estacionamento]
- [Outras informações relevantes]

É com grande satisfação que aguardamos sua presença neste importante evento.

Respeitosamente,

[Nome do Signatário]
[Cargo]
[Instituição/Empresa]
[Contatos Oficiais]

[Logotipo ou Brasão da Instituição, se aplicável]"""
            },
            {
                "id": "sponsorship_request",
                "title": "Solicitação de Patrocínio",
                "description": "Para solicitar patrocínio para eventos ou iniciativas",
                "structure": [
                    "Assunto claro mencionando 'patrocínio' e o evento/iniciativa",
                    "Saudação formal e personalizada",
                    "Apresentação breve da organização solicitante",
                    "Introdução ao evento ou iniciativa",
                    "Explicação da relevância e impacto esperado",
                    "Alinhamento com valores ou interesses do potencial patrocinador",
                    "Solicitação específica (valores ou apoio material)",
                    "Diferentes níveis de patrocínio disponíveis",
                    "Benefícios claros para o patrocinador",
                    "Informações sobre edições anteriores ou resultados (se aplicável)",
                    "Proposta de próximos passos",
                    "Agradecimento pela consideração",
                    "Assinatura formal com dados de contato"
                ],
                "example": """Assunto: Solicitação de Patrocínio - [Nome do Evento/Iniciativa] - [Data/Período]

Prezado(a) Sr(a). [Nome],
[Cargo]
[Empresa]

Em nome de [Organização Solicitante], venho apresentar uma oportunidade de patrocínio para [Nome do Evento/Iniciativa], que ocorrerá em [data/período] em [local].

SOBRE NOSSA ORGANIZAÇÃO:
A [Nome da Organização] é [breve descrição da organização, sua missão e trajetória]. Ao longo de [período], temos [conquistas relevantes].

SOBRE O EVENTO/INICIATIVA:
O [Nome do Evento/Iniciativa] é um [tipo do evento: conferência/projeto/programa] focado em [tema/objetivo]. Esperamos reunir aproximadamente [número estimado] de [público-alvo] e gerar impacto significativo em [área de impacto].

Por que este evento/iniciativa é relevante:
- [Razão 1]
- [Razão 2]
- [Razão 3]

Acreditamos que esta proposta se alinha perfeitamente com os valores e objetivos da [Empresa do Potencial Patrocinador], especialmente no que tange à [valor ou área de interesse comum].

OPORTUNIDADES DE PATROCÍNIO:

Oferecemos as seguintes categorias de patrocínio:

1. PATROCINADOR PLATINA: [Valor]
   • [Benefício 1]
   • [Benefício 2]
   • [Benefício 3]

2. PATROCINADOR OURO: [Valor]
   • [Benefício 1]
   • [Benefício 2]
   • [Benefício 3]

3. PATROCINADOR PRATA: [Valor]
   • [Benefício 1]
   • [Benefício 2]
   • [Benefício 3]

4. APOIADOR: [Valor ou tipo de apoio material]
   • [Benefício 1]
   • [Benefício 2]

[Se aplicável] Em nossa edição anterior, contamos com o patrocínio de [empresas anteriores] e alcançamos [resultados quantificáveis].

Gostaríamos de agendar uma reunião para apresentar em detalhes nossa proposta e discutir como podemos construir uma parceria mutuamente benéfica. Estou disponível para encontrar um horário que seja conveniente para sua agenda.

Anexo a este e-mail você encontrará nossa proposta completa com informações detalhadas sobre o evento e as contrapartidas oferecidas.

Agradecemos antecipadamente pela consideração de nosso pedido e estamos à disposição para quaisquer esclarecimentos adicionais.

Cordialmente,

[Seu Nome]
[Seu Cargo]
[Organização]
[Telefone]
[E-mail]
[Site]"""
            },
            {
                "id": "press_release",
                "title": "Press Release por E-mail",
                "description": "Para enviar comunicados de imprensa a jornalistas e veículos",
                "structure": [
                    "Assunto conciso e informativo",
                    "Saudação profissional e direta",
                    "Parágrafo introdutório com a notícia principal (o lide)",
                    "Data e local no início",
                    "Desenvolvimento da notícia com detalhes",
                    "Citações de executivos ou especialistas",
                    "Contextualização e relevância",
                    "Informações sobre a empresa/organização",
                    "Disponibilidade para entrevistas",
                    "Recursos adicionais (fotos, vídeos, etc.)",
                    "Contato para a imprensa claramente identificado",
                    "Encerramento com data de embargo, se aplicável",
                    "Assinatura institucional"
                ],
                "example": """Assunto: [Empresa] lança [Produto/Serviço/Iniciativa] para [Benefício Principal]

PARA DIVULGAÇÃO IMEDIATA
[ou "EMBARGO ATÉ: Data e Hora específicas"]

Prezado(a) Jornalista,

[CIDADE], [DATA] - A [Nome da Empresa], [breve descrição da empresa], anuncia hoje o lançamento de [produto/serviço/iniciativa], que [descrição curta do impacto ou benefício principal]. Esta novidade representa [significado estratégico ou conquista relevante].

[Parágrafo com detalhes adicionais sobre o anúncio, incluindo funcionalidades, diferenciais ou impactos esperados].

"[Citação de um executivo de alto escalão sobre a importância estratégica da novidade]", afirma [Nome e Cargo do Executivo].

[Parágrafo com contextualização do mercado ou cenário relevante, usando dados ou estatísticas quando possível].

[Parágrafo com informações adicionais, como disponibilidade, preço, local ou outras especificidades].

"[Segunda citação, idealmente de outro executivo ou especialista, abordando outro aspecto da novidade]", destaca [Nome e Cargo do Executivo/Especialista].

[Parágrafo de encerramento com próximos passos, visão futura ou convite para ação específica].

SOBRE [NOME DA EMPRESA]:
[Parágrafo padrão com informações institucionais da empresa, incluindo números relevantes, área de atuação e diferenciais de mercado].

RECURSOS ADICIONAIS:
- Imagens em alta resolução: [link]
- Vídeo de demonstração: [link]
- Fact sheet completo: [link]

ENTREVISTAS:
Representantes da [Empresa] estão disponíveis para entrevistas. Para agendar, entre em contato com a assessoria de imprensa.

CONTATO PARA IMPRENSA:
[Nome do Assessor/Responsável pela Comunicação]
[Cargo]
[Telefone direto]
[E-mail]

###"""
            },
            {
                "id": "official_statement",
                "title": "Comunicado Oficial Institucional",
                "description": "Para posicionamentos oficiais em situações especiais ou crises",
                "structure": [
                    "Assunto direto indicando 'comunicado oficial' e o tema",
                    "Cabeçalho com logotipo e data",
                    "Título do comunicado",
                    "Saudação formal e abrangente",
                    "Contextualização breve da situação",
                    "Posicionamento oficial claro e direto",
                    "Fatos relevantes (sem especulações)",
                    "Ações que estão sendo tomadas",
                    "Compromissos assumidos",
                    "Próximos passos, se aplicável",
                    "Canais para informações adicionais",
                    "Encerramento com mensagem de confiança",
                    "Assinatura da alta direção da instituição"
                ],
                "example": """Assunto: Comunicado Oficial: [Tema do Comunicado]

[LOGOTIPO DA INSTITUIÇÃO]

COMUNICADO OFICIAL
[DATA]

[TÍTULO DO COMUNICADO EM DESTAQUE]

À comunidade, clientes, colaboradores e parceiros,

A [Nome da Instituição] vem a público prestar os seguintes esclarecimentos sobre [tema ou situação que motivou o comunicado].

CONTEXTO:
[Breve parágrafo contextualizando a situação de forma objetiva e factual]

POSICIONAMENTO OFICIAL:
Diante dos fatos apresentados, a [Nome da Instituição] declara oficialmente que [posicionamento claro e inequívoco sobre a situação]. Reafirmamos nosso compromisso com [valores ou princípios relevantes para a situação].

FATOS RELEVANTES:
- [Fato 1]
- [Fato 2]
- [Fato 3]

AÇÕES EM ANDAMENTO:
Em resposta à situação, a [Nome da Instituição] já implementou as seguintes medidas:
1. [Ação 1]
2. [Ação 2]
3. [Ação 3]

COMPROMISSOS:
Reiteramos nosso compromisso com [compromissos relevantes: transparência, qualidade, segurança, etc.] e nos comprometemos a [compromissos específicos relacionados à situação].

PRÓXIMOS PASSOS:
[Se aplicável, informar quais serão os próximos passos institucionais, como investigações, divulgação de resultados, compensações, etc.]

Informações adicionais serão disponibilizadas através de nossos canais oficiais:
- Site oficial: [URL]
- Central de atendimento: [Telefone]
- E-mail institucional: [E-mail]

Agradecemos a compreensão de todos e reafirmamos nossa determinação em [mensagem positiva relacionada à resolução ou aprendizado com a situação].

Respeitosamente,

[Nome do Presidente/CEO/Diretor]
[Cargo]
[Nome da Instituição]"""
            },
            {
                "id": "formal_complaint",
                "title": "Reclamação Formal",
                "description": "Para registrar reclamações formais a empresas ou instituições",
                "structure": [
                    "Assunto claro indicando 'reclamação' e o tema",
                    "Saudação formal",
                    "Identificação completa do reclamante",
                    "Referências de protocolos, pedidos ou contas",
                    "Descrição clara e objetiva do problema",
                    "Cronologia dos fatos relevantes",
                    "Tentativas anteriores de resolução",
                    "Impactos negativos sofridos",
                    "Solicitação específica de resolução",
                    "Prazo esperado para resposta",
                    "Menção a eventuais dispositivos legais aplicáveis",
                    "Informação sobre próximos passos caso não haja resolução",
                    "Encerramento formal",
                    "Dados de contato para retorno"
                ],
                "example": """Assunto: Reclamação Formal: [Resumo do Problema] - [Nº de Protocolo/Conta, se houver]

Prezados Senhores,

Eu, [Nome Completo], [documento de identificação: CPF/RG/outro] nº [número do documento], venho por meio desta registrar uma reclamação formal referente a [serviço/produto/atendimento] oferecido por esta instituição.

DADOS PARA REFERÊNCIA:
- Número de cliente/conta: [número]
- Protocolo(s) de atendimento anterior(es): [número(s)]
- Data da compra/contratação: [data]
- Local: [estabelecimento/cidade/site]

DESCRIÇÃO DO PROBLEMA:
[Descrição clara, objetiva e detalhada do problema enfrentado]

CRONOLOGIA DOS FATOS:
- [Data]: [Fato 1]
- [Data]: [Fato 2]
- [Data]: [Fato 3]

TENTATIVAS ANTERIORES DE RESOLUÇÃO:
Informo que já tentei resolver esta situação através dos seguintes meios:
1. [Descrição da tentativa 1] em [data]
2. [Descrição da tentativa 2] em [data]
3. [Descrição da tentativa 3] em [data]

IMPACTOS NEGATIVOS:
Esta situação me causou os seguintes transtornos:
- [Impacto 1]
- [Impacto 2]
- [Impacto 3]

SOLICITAÇÃO:
Diante do exposto, solicito:
1. [Solicitação específica 1 - ex: reembolso, troca, reparo]
2. [Solicitação específica 2 - ex: compensação pelos transtornos]
3. [Solicitação específica 3 - ex: esclarecimentos formais]

Solicito uma resposta formal a esta reclamação no prazo de [número] dias úteis, conforme estabelecido [pelo Código de Defesa do Consumidor/pela política da empresa/pelo órgão regulador] para este tipo de situação.

Caso não obtenha resposta satisfatória dentro do prazo estipulado, informo que tomarei as medidas cabíveis junto aos órgãos de proteção ao consumidor [especificar: Procon, Anatel, Banco Central, etc.] e, se necessário, as vias judiciais para garantir meus direitos.

Certo de sua compreensão e pronto atendimento,

Atenciosamente,

[Nome Completo]
[Endereço completo]
[Telefone]
[E-mail]
[Data]

[Anexos, se houver: comprovantes, recibos, prints, gravações]"""
            }
        ]
    }
]

# Helper functions for loading data, similar to the code we had before
def ensure_data_directory():
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    return data_dir


# Routes
@app.route('/')
def index():
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Melhores Práticas de E-mail</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: #f8f9fa;
                color: #333;
                line-height: 1.6;
            }
            .header {
                background-color: #0d6efd;
                color: white;
                padding: 60px 0;
                margin-bottom: 40px;
                text-align: center;
            }
            .header h1 {
                font-size: 2.8rem;
                font-weight: 700;
                margin-bottom: 15px;
            }
            .header p {
                font-size: 1.2rem;
                max-width: 700px;
                margin: 0 auto;
            }
            .category-card {
                background: white;
                border-radius: 10px;
                overflow: hidden;
                transition: all 0.3s ease;
                height: 100%;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                border: none;
            }
            .category-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 10px 20px rgba(0,0,0,0.1);
            }
            .card-header {
                background-color: #0d6efd;
                color: white;
                font-weight: bold;
                padding: 15px;
            }
            .card-body {
                padding: 25px;
            }
            .category-icon {
                font-size: 3rem;
                margin-bottom: 20px;
                color: #0d6efd;
            }
            .category-description {
                margin-bottom: 20px;
                color: #6c757d;
            }
            .btn-primary {
                background-color: #0d6efd;
                border-color: #0d6efd;
                padding: 10px 20px;
                font-weight: 600;
            }
            .btn-primary:hover {
                background-color: #0b5ed7;
                border-color: #0b5ed7;
            }
            footer {
                background-color: #343a40;
                color: white;
                padding: 30px 0;
                margin-top: 50px;
            }
            .footer-links a {
                color: #adb5bd;
                text-decoration: none;
                margin: 0 15px;
            }
            .footer-links a:hover {
                color: white;
            }
        </style>
    </head>
    <body>
        <div class="header">
            <div class="container">
                <h1>Melhores Práticas de E-mail</h1>
                <p>Guia completo com mais de 20 tipos de e-mails profissionais para todas as ocasiões</p>
                <a href="/category/1" class="btn btn-light btn-lg mt-3">Começar Agora</a>
            </div>
        </div>
        
        <div class="container">
            <div class="row mb-5">
                <div class="col-md-12">
                    <div class="alert alert-info">
                        <h4 class="alert-heading"><i class="fas fa-info-circle me-2"></i>Por que a comunicação por e-mail é importante?</h4>
                        <p>E-mails bem escritos são essenciais para comunicação profissional eficaz. Eles criam primeiras impressões duradouras, estabelecem credibilidade e constroem relacionamentos sólidos no ambiente de trabalho. Nosso guia oferece modelos testados e aprovados para garantir que suas mensagens sejam claras, profissionais e eficazes.</p>
                    </div>
                </div>
            </div>
            
            <div class="row g-4">
    '''
    
    # Add each category
    for category in EMAIL_PRACTICES:
        icon_class = ""
        if category["id"] == 1:
            icon_class = "fas fa-briefcase"
        elif category["id"] == 2:
            icon_class = "fas fa-bullhorn"
        elif category["id"] == 3:
            icon_class = "fas fa-users"
        elif category["id"] == 4:
            icon_class = "fas fa-building"
        elif category["id"] == 5:
            icon_class = "fas fa-file-signature"
            
        content = f'''
                <div class="col-md-4">
                    <div class="category-card">
                        <div class="card-header">{category["category"]}</div>
                        <div class="card-body text-center">
                            <div class="category-icon">
                                <i class="{icon_class}"></i>
                            </div>
                            <h3>{category["category"]}</h3>
                            <p class="category-description">Modelos de e-mail para {category["category"].lower()}</p>
                            <p><strong>{len(category["templates"])} modelos disponíveis</strong></p>
                            <a href="/category/{category["id"]}" class="btn btn-primary">Ver Modelos</a>
                        </div>
                    </div>
                </div>
        '''
        html += content
    
    html += '''
            </div>
            
            <div class="row mt-5">
                <div class="col-md-12">
                    <div class="card">
                        <div class="card-header bg-primary text-white">
                            <h3 class="mb-0">Dicas Gerais para E-mails Eficazes</h3>
                        </div>
                        <div class="card-body">
                            <div class="row">
                                <div class="col-md-6">
                                    <h4><i class="fas fa-check-circle text-primary me-2"></i>Faça</h4>
                                    <ul>
                                        <li>Utilize assuntos claros e específicos</li>
                                        <li>Mantenha o conteúdo conciso e focado</li>
                                        <li>Adapte o tom de acordo com o destinatário</li>
                                        <li>Verifique a ortografia e gramática antes de enviar</li>
                                        <li>Responda e-mails em tempo hábil</li>
                                        <li>Utilize formatação adequada para facilitar a leitura</li>
                                        <li>Inclua uma assinatura profissional</li>
                                    </ul>
                                </div>
                                <div class="col-md-6">
                                    <h4><i class="fas fa-times-circle text-danger me-2"></i>Evite</h4>
                                    <ul>
                                        <li>Escrever em CAIXA ALTA (parece que está gritando)</li>
                                        <li>Usar excesso de exclamações ou emojis em e-mails formais</li>
                                        <li>Enviar sem revisar o conteúdo e anexos</li>
                                        <li>Copiar pessoas desnecessariamente (CC e CCO)</li>
                                        <li>Utilizar linguagem muito casual em contextos formais</li>
                                        <li>Escrever parágrafos muito longos e densos</li>
                                        <li>Responder com "Respondido acima" sem contexto</li>
                                    </ul>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <footer>
            <div class="container text-center">
                <p>&copy; 2025 Guia de Melhores Práticas de E-mail</p>
                <div class="footer-links">
                    <a href="#">Sobre</a>
                    <a href="#">Contato</a>
                    <a href="#">Política de Privacidade</a>
                    <a href="#">Termos de Uso</a>
                </div>
            </div>
        </footer>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    '''
    
    return html

# @app.route('/category/<int:category_id>')
# def show_category(category_id):
#     # Validate category_id
#     if category_id < 1 or category_id > len(EMAIL_PRACTICES):
#         return "Categoria não encontrada", 404
    
#     # Get the selected category
#     category = next((cat for cat in EMAIL_PRACTICES if cat["id"] == category_id), None)
#     if not category:
#         return "Categoria não encontrada", 404
    
#     # Get category icon
#     icon_class = ""
#     if category_id == 1:
#         icon_class = "fas fa-briefcase"
#     elif category_id == 2:
#         icon_class = "fas fa-bullhorn"
#     elif category_id == 3:
#         icon_class = "fas fa-users"
#     elif category_id == 4:
#         icon_class = "fas fa-building"
#     elif category_id == 5:
#         icon_class = "fas fa-file-signature"
    
#     html = f'''
#     <!DOCTYPE html>
#     <html>
#     <head>
#         <title>{category["category"]} - Melhores Práticas de E-mail</title>
#         <meta charset="UTF-8">
#         <meta name="viewport" content="width=device-width, initial-scale=1.0">
#         <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
#         <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
#         <style>
#             body {{
#                 font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
#                 background-color: #f8f9fa;
#                 color: #333;
#                 line-height: 1.6;
#             }}
#             .header {{
#                 background-color: #0d6efd;
#                 color: white;
#                 padding: 30px 0;
#                 margin-bottom: 40px;
#             }}
#             .header h1 {{
#                 font-size: 2.2rem;
#                 font-weight: 700;
#             }}
#             .category-icon {{
#                 font-size: 2.5rem;
#                 margin-right: 15px;
#                 color: white;
#             }}
#             .email-template {{
#                 background-color: white;
#                 border-radius: 8px;
#                 padding: 25px;
#                 margin-bottom: 30px;
#                 box-shadow: 0 2px 8px rgba(0,0,0,0.1);
#             }}
#             .template-header {{
#                 border-bottom: 1px solid #dee2e6;
#                 padding-bottom: 15px;
#                 margin-bottom: 20px;
#             }}
#             .template-content {{
#                 background-color: #f8f9fa;
#                 border-left: 4px solid #0d6efd;
#                 padding: 20px;
#                 border-radius: 4px;
#                 font-family: 'Courier New', monospace;
#             }}
#             .template-instructions {{
#                 background-color: #e9ecef;
#                 padding: 15px;
#                 border-radius: 4px;
#                 margin-top: 20px;
#             }}
#             .btn-primary {{
#                 background-color: #0d6efd;
#                 border-color: #0d6efd;
#                 padding: 10px 20px;
#                 font-weight: 600;
#             }}
#             .btn-outline-primary {{
#                 border-color: #0d6efd;
#                 color: #0d6efd;
#                 padding: 10px 20px;
#                 font-weight: 600;
#             }}
#             .btn-primary:hover {{
#                 background-color: #0b5ed7;
#                 border-color: #0b5ed7;
#             }}
#             .navigation-buttons {{
#                 margin: 30px 0;
#             }}
#             footer {{
#                 background-color: #343a40;
#                 color: white;
#                 padding: 30px 0;
#                 margin-top: 50px;
#             }}
#             .footer-links a {{
#                 color: #adb5bd;
#                 text-decoration: none;
#                 margin: 0 15px;
#             }}
#             .footer-links a:hover {{
#                 color: white;
#             }}
#             .template-navigation {{
#                 position: sticky;
#                 top: 20px;
#             }}
#             .list-group-item.active {{
#                 background-color: #0d6efd;
#                 border-color: #0d6efd;
#             }}
#             .copy-btn {{
#                 position: absolute;
#                 top: 15px;
#                 right: 15px;
#             }}
#         </style>
#     </head>
#     <body>
#         <div class="header">
#             <div class="container">
#                 <nav aria-label="breadcrumb">
#                     <ol class="breadcrumb">
#                         <li class="breadcrumb-item"><a href="/" class="text-white">Início</a></li>
#                         <li class="breadcrumb-item active text-white" aria-current="page">{category["category"]}</li>
#                     </ol>
#                 </nav>
#                 <div class="d-flex align-items-center">
#                     <i class="{icon_class} category-icon"></i>
#                     <h1>{category["category"]}</h1>
#                 </div>
#                 <p class="lead">Modelos profissionais de e-mail para {category["category"].lower()}</p>
#             </div>
#         </div>
        
#         <div class="container">
#             <div class="row">
#                 <div class="col-md-3">
#                     <div class="template-navigation">
#                         <div class="card">
#                             <div class="card-header bg-primary text-white">
#                                 <h5 class="mb-0">Modelos Disponíveis</h5>
#                             </div>
#                             <div class="list-group list-group-flush">
#     '''
    
#     # Add template links - agora usando o título como identificador do modelo
#     for i, template in enumerate(category["templates"]):
#         title = template.get("title", f"Modelo {i+1}")
#         html += f'''
#                                 <a href="#template-{i+1}" class="list-group-item list-group-item-action d-flex justify-content-between align-items-center">
#                                     {title}
#                                     <span class="badge bg-primary rounded-pill">{i+1}</span>
#                                 </a>
#         '''
    
#     html += f'''
#                             </div>
#                         </div>
                        
#                         <div class="mt-4">
#                             <div class="card">
#                                 <div class="card-header bg-primary text-white">
#                                     <h5 class="mb-0">Outras Categorias</h5>
#                                 </div>
#                                 <div class="list-group list-group-flush">
#     '''
    
#     # Add links to other categories
#     for cat in EMAIL_PRACTICES:
#         if cat["id"] != category_id:
#             html += f'''
#                                     <a href="/category/{cat["id"]}" class="list-group-item list-group-item-action">{cat["category"]}</a>
#             '''
    
#     html += '''
#                                 </div>
#                             </div>
#                         </div>
#                     </div>
#                 </div>
                
#                 <div class="col-md-9">
#     '''
    
#     # Add templates - com ajustes para acessar as chaves corretas
#     for i, template in enumerate(category["templates"]):
#         title = template.get("title", f"Modelo {i+1}")
#         description = template.get("description", "")
#         subject = template.get("subject", "")
#         body = template.get("body", "")
#         tips = template.get("tips", "")
        
#         # Se não existir 'tips', criar uma lista vazia
#         tips_html = ""
#         if isinstance(tips, list):
#             tips_html = "\n".join([f"<li>{tip}</li>" for tip in tips])
#         elif isinstance(tips, str) and tips:
#             tips_html = f"<li>{tips}</li>"
        
#         html += f'''
#                     <div id="template-{i+1}" class="email-template position-relative">
#                         <button class="btn btn-sm btn-outline-primary copy-btn" onclick="copyTemplate('{i+1}')">
#                             <i class="fas fa-copy"></i> Copiar
#                         </button>
#                         <div class="template-header">
#                             <h3>{title}</h3>
#                             <p class="text-muted">{description}</p>
#                         </div>
#                         <div class="template-content" id="template-content-{i+1}">
#                             <p><strong>Assunto:</strong> {subject}</p>
#                             <hr>
#                             {body}
#                         </div>
#                         <div class="template-instructions">
#                             <h5><i class="fas fa-lightbulb text-warning me-2"></i>Dicas de Uso</h5>
#                             <ul>
#                                 {tips_html}
#                             </ul>
#                         </div>
#                     </div>
#         '''
    
#     # Add navigation buttons
#     prev_category = category_id - 1 if category_id > 1 else None
#     next_category = category_id + 1 if category_id < len(EMAIL_PRACTICES) else None
    
#     html += '''
#                     <div class="navigation-buttons d-flex justify-content-between">
#     '''
    
#     if prev_category:
#         prev_cat = next((c for c in EMAIL_PRACTICES if c["id"] == prev_category), None)
#         if prev_cat:
#             html += f'''
#                         <a href="/category/{prev_category}" class="btn btn-outline-primary">
#                             <i class="fas fa-arrow-left me-2"></i>{prev_cat["category"]}
#                         </a>
#             '''
#         else:
#             html += '''
#                         <div></div>
#             '''
#     else:
#         html += '''
#                         <a href="/" class="btn btn-outline-primary">
#                             <i class="fas fa-home me-2"></i>Voltar ao Início
#                         </a>
#         '''
    
#     if next_category:
#         next_cat = next((c for c in EMAIL_PRACTICES if c["id"] == next_category), None)
#         if next_cat:
#             html += f'''
#                         <a href="/category/{next_category}" class="btn btn-primary">
#                             {next_cat["category"]}<i class="fas fa-arrow-right ms-2"></i>
#                         </a>
#             '''
#         else:
#             html += '''
#                         <div></div>
#             '''
#     else:
#         html += '''
#                         <a href="/" class="btn btn-primary">
#                             Voltar ao Início<i class="fas fa-home ms-2"></i>
#                         </a>
#         '''
    
#     html += '''
#                     </div>
#                 </div>
#             </div>
#         </div>
        
#         <footer>
#             <div class="container text-center">
#                 <p>&copy; 2025 Guia de Melhores Práticas de E-mail</p>
#                 <div class="footer-links">
#                     <a href="#">Sobre</a>
#                     <a href="#">Contato</a>
#                     <a href="#">Política de Privacidade</a>
#                     <a href="#">Termos de Uso</a>
#                 </div>
#             </div>
#         </footer>
        
#         <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.bundle.min.js"></script>
#         <script>
#             function copyTemplate(templateId) {
#                 const content = document.getElementById(`template-content-${templateId}`);
#                 const tempTextarea = document.createElement('textarea');
#                 tempTextarea.value = content.innerText;
#                 document.body.appendChild(tempTextarea);
#                 tempTextarea.select();
#                 document.execCommand('copy');
#                 document.body.removeChild(tempTextarea);
                
#                 // Show feedback
#                 const copyBtn = event.target.closest('.copy-btn');
#                 const originalText = copyBtn.innerHTML;
#                 copyBtn.innerHTML = '<i class="fas fa-check"></i> Copiado!';
#                 setTimeout(() => {
#                     copyBtn.innerHTML = originalText;
#                 }, 2000);
#             }
            
#             // Smooth scrolling for anchor links
#             document.querySelectorAll('a[href^="#"]').forEach(anchor => {
#                 anchor.addEventListener('click', function (e) {
#                     e.preventDefault();
#                     document.querySelector(this.getAttribute('href')).scrollIntoView({
#                         behavior: 'smooth'
#                     });
#                 });
#             });
#         </script>
#     </body>
#     </html>
#     '''
    
#     return html

@app.route('/category/<int:category_id>')
def category(category_id):
    # Find the category
    category_data = None
    for category in EMAIL_PRACTICES:
        if category["id"] == category_id:
            category_data = category
            break
    
    if category_data is None:
        return "Categoria não encontrada", 404
    
    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Melhores Práticas de E-mail - {category_data["category"]}</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: #f8f9fa;
                color: #333;
                line-height: 1.6;
            }}
            .header {{
                background-color: #0d6efd;
                color: white;
                padding: 40px 0;
                margin-bottom: 40px;
                text-align: center;
            }}
            .header h1 {{
                font-size: 2.5rem;
                font-weight: 700;
                margin-bottom: 10px;
            }}
            .header p {{
                font-size: 1.1rem;
                max-width: 700px;
                margin: 0 auto;
            }}
            .template-card {{
                background: white;
                border-radius: 10px;
                overflow: hidden;
                transition: all 0.3s ease;
                height: 100%;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                border: none;
                margin-bottom: 25px;
            }}
            .template-card:hover {{
                transform: translateY(-5px);
                box-shadow: 0 10px 20px rgba(0,0,0,0.1);
            }}
            .card-header {{
                background-color: #0d6efd;
                color: white;
                font-weight: bold;
                padding: 15px;
            }}
            .card-body {{
                padding: 25px;
            }}
            .template-description {{
                margin-bottom: 20px;
                color: #6c757d;
            }}
            .structure-list {{
                margin-bottom: 20px;
                padding-left: 20px;
            }}
            .structure-list li {{
                margin-bottom: 5px;
            }}
            .btn-primary {{
                background-color: #0d6efd;
                border-color: #0d6efd;
                padding: 10px 20px;
                font-weight: 600;
            }}
            .btn-primary:hover {{
                background-color: #0b5ed7;
                border-color: #0b5ed7;
            }}
            .btn-secondary {{
                background-color: #6c757d;
                border-color: #6c757d;
            }}
            .btn-secondary:hover {{
                background-color: #5a6268;
                border-color: #5a6268;
            }}
            footer {{
                background-color: #343a40;
                color: white;
                padding: 30px 0;
                margin-top: 50px;
            }}
            .footer-links a {{
                color: #adb5bd;
                text-decoration: none;
                margin: 0 15px;
            }}
            .footer-links a:hover {{
                color: white;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <div class="container">
                <h1>E-mails para {category_data["category"]}</h1>
                <p>Modelos e melhores práticas para comunicação eficaz</p>
            </div>
        </div>
        
        <div class="container">
            <div class="row mb-4">
                <div class="col-md-12">
                    <a href="/" class="btn btn-secondary mb-4"><i class="fas fa-arrow-left me-2"></i>Voltar para Categorias</a>
                </div>
            </div>
            
            <div class="row">
    '''
    
    # Add each template in this category
    for template in category_data["templates"]:
        html += f'''
                <div class="col-md-12">
                    <div class="template-card">
                        <div class="card-header">
                            <h2>{template["title"]}</h2>
                        </div>
                        <div class="card-body">
                            <p class="template-description">{template["description"]}</p>
                            
                            <h4>Estrutura Recomendada:</h4>
                            <ul class="structure-list">
        '''
        
        # Add each structure point for this specific template
        for point in template["structure"]:
            html += f'<li>{point}</li>'
            
        html += f'''
                            </ul>
                            
                            <a href="/template/{category_id}/{template["id"]}" class="btn btn-primary">Ver Exemplo Completo</a>
                        </div>
                    </div>
                </div>
        '''
    
    html += '''
            </div>
        </div>
        
        <footer>
            <div class="container text-center">
                <p>&copy; 2025 Guia de Melhores Práticas de E-mail</p>
                <div class="footer-links">
                    <a href="#">Sobre</a>
                    <a href="#">Contato</a>
                    <a href="#">Política de Privacidade</a>
                    <a href="#">Termos de Uso</a>
                </div>
            </div>
        </footer>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    '''
    
    return html

@app.route('/template/<int:category_id>/<template_id>')
def template(category_id, template_id):
    # Find the category
    category_data = None
    for category in EMAIL_PRACTICES:
        if category["id"] == category_id:
            category_data = category
            break
    
    if category_data is None:
        return "Categoria não encontrada", 404
    
    # Find the template
    template_data = None
    for template in category_data["templates"]:
        if template["id"] == template_id:
            template_data = template
            break
    
    if template_data is None:
        return "Modelo não encontrado", 404
    
    # Parse markdown in example (if needed)
    example_html = markdown.markdown(template_data["example"])
    # Sanitize HTML for security
    example_html = bleach.clean(
        example_html,
        tags=['p', 'br', 'strong', 'em', 'h1', 'h2', 'h3', 'h4', 'ul', 'ol', 'li', 'blockquote', 'code', 'pre'],
        attributes={},
        strip=True
    )
    
    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>{template_data["title"]} - Melhores Práticas de E-mail</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: #f8f9fa;
                color: #333;
                line-height: 1.6;
            }}
            .header {{
                background-color: #0d6efd;
                color: white;
                padding: 30px 0;
                margin-bottom: 40px;
                text-align: center;
            }}
            .header h1 {{
                font-size: 2.2rem;
                font-weight: 700;
                margin-bottom: 10px;
            }}
            .header p {{
                font-size: 1.1rem;
                max-width: 700px;
                margin: 0 auto;
            }}
            .template-card {{
                background: white;
                border-radius: 10px;
                overflow: hidden;
                box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                border: none;
                margin-bottom: 25px;
            }}
            .card-header {{
                background-color: #0d6efd;
                color: white;
                font-weight: bold;
                padding: 15px;
            }}
            .card-body {{
                padding: 25px;
            }}
            .template-description {{
                margin-bottom: 20px;
                color: #6c757d;
                font-size: 1.1rem;
            }}
            .structure-list {{
                margin-bottom: 30px;
                padding-left: 20px;
            }}
            .structure-list li {{
                margin-bottom: 8px;
            }}
            .btn-primary {{
                background-color: #0d6efd;
                border-color: #0d6efd;
                padding: 10px 20px;
                font-weight: 600;
            }}
            .btn-primary:hover {{
                background-color: #0b5ed7;
                border-color: #0b5ed7;
            }}
            .btn-secondary {{
                background-color: #6c757d;
                border-color: #6c757d;
            }}
            .btn-secondary:hover {{
                background-color: #5a6268;
                border-color: #5a6268;
            }}
            .example-box {{
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 10px;
                padding: 25px;
                font-family: 'Courier New', monospace;
                white-space: pre-wrap;
                margin-bottom: 30px;
                position: relative;
            }}
            .copy-btn {{
                position: absolute;
                top: 10px;
                right: 10px;
                opacity: 0.7;
            }}
            .copy-btn:hover {{
                opacity: 1;
            }}
            .tips-box {{
                background-color: #e8f4f8;
                border-left: 4px solid #0d6efd;
                padding: 20px;
                margin: 30px 0;
                border-radius: 0 10px 10px 0;
            }}
            footer {{
                background-color: #343a40;
                color: white;
                padding: 30px 0;
                margin-top: 50px;
            }}
            .footer-links a {{
                color: #adb5bd;
                text-decoration: none;
                margin: 0 15px;
            }}
            .footer-links a:hover {{
                color: white;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <div class="container">
                <h1>{template_data["title"]}</h1>
                <p>{template_data["description"]}</p>
            </div>
        </div>
        
        <div class="container">
            <div class="row mb-4">
                <div class="col-md-12">
                    <a href="/category/{category_id}" class="btn btn-secondary mb-4"><i class="fas fa-arrow-left me-2"></i>Voltar para {category_data["category"]}</a>
                </div>
            </div>
            
            <div class="row">
                <div class="col-md-12">
                    <div class="template-card">
                        <div class="card-header">
                            <h2>{template_data["title"]}</h2>
                        </div>
                        <div class="card-body">
                            <p class="template-description">{template_data["description"]}</p>
                            
                            <h4>Estrutura Recomendada:</h4>
                            <ul class="structure-list">
    '''
    
    # Add each structure point
    for point in template_data["structure"]:
        html += f'<li>{point}</li>'
        
    # Corrigindo a formatação para evitar problemas com f-strings aninhadas
    html += '''
                            </ul>
                            
                            <h4>Exemplo Completo:</h4>
                            <div class="example-box" id="example-text">'''
    
    # Adicionando o exemplo como uma string separada
    html += template_data["example"]
    
    # Continuando com o restante do HTML
    html += '''
                            </div>
                            <button class="btn btn-sm btn-outline-secondary copy-btn" onclick="copyExample()">
                                <i class="fas fa-copy"></i> Copiar
                            </button>
                            
                            <div class="tips-box">
                                <h4><i class="fas fa-lightbulb me-2"></i>Dicas para Personalização:</h4>
                                <p>Ao utilizar este modelo, lembre-se de:</p>
                                <ul>
                                    <li>Substituir todos os campos entre colchetes [exemplo] com informações específicas</li>
                                    <li>Ajustar o tom conforme necessário para seu público-alvo e relacionamento</li>
                                    <li>Personalizar conforme a cultura da sua empresa e setor de atuação</li>
                                    <li>Adaptar a extensão de acordo com a complexidade do assunto</li>
                                    <li>Revisar cuidadosamente antes do envio para evitar erros</li>
                                </ul>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <footer>
            <div class="container text-center">
                <p>&copy; 2025 Guia de Melhores Práticas de E-mail</p>
                <div class="footer-links">
                    <a href="#">Sobre</a>
                    <a href="#">Contato</a>
                    <a href="#">Política de Privacidade</a>
                    <a href="#">Termos de Uso</a>
                </div>
            </div>
        </footer>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.bundle.min.js"></script>
        <script>
            function copyExample() {
                const exampleText = document.getElementById('example-text').innerText;
                navigator.clipboard.writeText(exampleText)
                    .then(() => {
                        const copyBtn = document.querySelector('.copy-btn');
                        copyBtn.innerHTML = '<i class="fas fa-check"></i> Copiado!';
                        setTimeout(() => {
                            copyBtn.innerHTML = '<i class="fas fa-copy"></i> Copiar';
                        }, 2000);
                    })
                    .catch(err => {
                        console.error('Erro ao copiar: ', err);
                    });
            }
        </script>
    </body>
    </html>
    '''
    
    return html

# Função para abrir automaticamente o navegador quando o aplicativo iniciar
import webbrowser
import threading
import time

def open_browser():
    # Aguarda 1.5 segundos para garantir que o servidor iniciou
    time.sleep(1.5)
    # Abre o navegador padrão
    webbrowser.open('http://127.0.0.1:5000/')

if __name__ == '__main__':
    # Inicia um thread para abrir o navegador
    threading.Thread(target=open_browser).start()
    
    # Inicia o servidor Flask
    app.run(debug=True)