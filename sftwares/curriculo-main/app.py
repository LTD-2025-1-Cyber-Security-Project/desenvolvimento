from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import os
import json
from datetime import datetime
import time
import uuid

app = Flask(__name__)
app.secret_key = 'curriculum_bot_secret_key'

# Garantir que o diretório de dados exista
def ensure_data_directory():
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    return data_dir

# Rota principal - Home
@app.route('/')
def index():
    return render_template('home.html')

# Rota para o chatbot
@app.route('/chatbot')
def chatbot():
    # Gerar ID único para esta sessão se não existir
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
        session['dados_curriculo'] = {
            'informacoes_pessoais': {},
            'formacoes_academicas': [],
            'cursos': [],
            'projetos': [],
            'experiencias': [],
            'idiomas': []
        }
        session['etapa_atual'] = 'boas_vindas'
    
    return render_template('chatbot.html')

# Rota para listar currículos
@app.route('/meus-curriculos')
def meus_curriculos():
    data_dir = ensure_data_directory()
    curriculos = []
    
    # Listar arquivos de currículo
    if os.path.exists(data_dir):
        for arquivo in os.listdir(data_dir):
            if arquivo.startswith('curriculo_') and arquivo.endswith('.json'):
                session_id = arquivo[10:-5]  # Remove 'curriculo_' e '.json'
                
                # Carregar dados para obter nome
                try:
                    with open(os.path.join(data_dir, arquivo), 'r', encoding='utf-8') as f:
                        dados = json.load(f)
                        
                    nome = f"{dados.get('informacoes_pessoais', {}).get('nome', '')} {dados.get('informacoes_pessoais', {}).get('sobrenome', '')}"
                    data_criacao = datetime.fromtimestamp(os.path.getctime(os.path.join(data_dir, arquivo))).strftime('%d/%m/%Y %H:%M')
                    
                    curriculos.append({
                        'id': session_id,
                        'nome': nome.strip() or 'Currículo sem nome',
                        'data': data_criacao
                    })
                except:
                    continue
    
    return render_template('meus_curriculos.html', curriculos=curriculos)

# Processar mensagens do chat
@app.route('/processar_mensagem', methods=['POST'])
def processar_mensagem():
    data = request.get_json()
    mensagem = data.get('mensagem', '')
    etapa_atual = session.get('etapa_atual', 'boas_vindas')
    
    # Processar a mensagem de acordo com a etapa atual
    resposta, proxima_etapa, opcoes = processar_etapa(etapa_atual, mensagem)
    
    # Atualizar etapa atual
    session['etapa_atual'] = proxima_etapa
    
    # Retornar resposta, próxima etapa e opções
    return jsonify({
        'resposta': resposta,
        'etapa': proxima_etapa,
        'opcoes': opcoes,
        'previa': gerar_previa(session.get('dados_curriculo', {}))
    })

# Função para processar a etapa atual
def processar_etapa(etapa, mensagem):
    dados_curriculo = session.get('dados_curriculo', {})
    
    # Etapa de boas-vindas
    if etapa == 'boas_vindas':
        if mensagem.lower() in ['oi', 'olá', 'ola', 'começar', 'iniciar', 'hello', 'hi']:
            return (
                "Olá! Eu sou o CurriculoBot, seu assistente para criar um currículo profissional. Vamos começar com suas informações pessoais. Como posso te chamar?",
                'nome',
                []
            )
        else:
            return (
                "Olá! Sou o CurriculoBot, seu assistente para criar um currículo profissional. Digite 'começar' quando estiver pronto para iniciar.",
                'boas_vindas',
                ['Começar']
            )
    
    # Etapa de nome
    elif etapa == 'nome':
        if not mensagem.strip():
            return (
                "Desculpe, não consegui entender seu nome. Poderia repetir por favor?",
                'nome',
                []
            )
        
        dados_curriculo['informacoes_pessoais']['nome'] = mensagem.strip()
        session['dados_curriculo'] = dados_curriculo
        
        return (
            f"Prazer em conhecê-lo, {mensagem.strip()}! Agora, qual é o seu sobrenome?",
            'sobrenome',
            []
        )
    
    # Etapa de sobrenome
    elif etapa == 'sobrenome':
        if not mensagem.strip():
            return (
                "Desculpe, não consegui entender seu sobrenome. Poderia repetir por favor?",
                'sobrenome',
                []
            )
        
        dados_curriculo['informacoes_pessoais']['sobrenome'] = mensagem.strip()
        session['dados_curriculo'] = dados_curriculo
        
        return (
            f"Ótimo! Agora, qual é o seu endereço de e-mail?",
            'email',
            []
        )
    
    # Etapa de email
    elif etapa == 'email':
        if not '@' in mensagem:
            return (
                "Hmm, isso não parece um endereço de e-mail válido. Por favor, inclua um '@' no seu e-mail.",
                'email',
                []
            )
        
        dados_curriculo['informacoes_pessoais']['email'] = mensagem.strip()
        session['dados_curriculo'] = dados_curriculo
        
        return (
            "Excelente! Agora, qual é o seu endereço?",
            'endereco',
            []
        )
    
    # Etapa de endereço
    elif etapa == 'endereco':
        if not mensagem.strip():
            return (
                "Desculpe, não consegui entender seu endereço. Poderia repetir por favor?",
                'endereco',
                []
            )
        
        dados_curriculo['informacoes_pessoais']['endereco'] = mensagem.strip()
        session['dados_curriculo'] = dados_curriculo
        
        return (
            "Perfeito! Agora, qual é a sua área de atuação profissional?",
            'area',
            ['Tecnologia da Informação', 'Saúde', 'Educação', 'Engenharia', 'Direito', 'Marketing', 'Administração', 'Outro']
        )
    
    # Etapa de área profissional
    elif etapa == 'area':
        if not mensagem.strip():
            return (
                "Desculpe, não consegui entender sua área profissional. Poderia repetir por favor?",
                'area',
                ['Tecnologia da Informação', 'Saúde', 'Educação', 'Engenharia', 'Direito', 'Marketing', 'Administração', 'Outro']
            )
        
        dados_curriculo['informacoes_pessoais']['area'] = mensagem.strip()
        session['dados_curriculo'] = dados_curriculo
        
        return (
            "Você tem um site pessoal ou portfólio? Se sim, qual é o endereço? (Se não tiver, digite 'não')",
            'site',
            ['Não']
        )
    
    # Etapa de site
    elif etapa == 'site':
        if mensagem.lower() not in ['não', 'nao', 'no', 'n']:
            dados_curriculo['informacoes_pessoais']['site'] = mensagem.strip()
        
        session['dados_curriculo'] = dados_curriculo
        
        return (
            "Você tem um perfil no LinkedIn? Se sim, qual é o endereço? (Se não tiver, digite 'não')",
            'linkedin',
            ['Não']
        )
    
    # Etapa de LinkedIn
    elif etapa == 'linkedin':
        if mensagem.lower() not in ['não', 'nao', 'no', 'n']:
            dados_curriculo['informacoes_pessoais']['linkedin'] = mensagem.strip()
        
        session['dados_curriculo'] = dados_curriculo
        
        # Perguntar sobre GitHub apenas para quem é da área de tecnologia
        if dados_curriculo['informacoes_pessoais'].get('area', '').lower() in ['tecnologia', 'tecnologia da informação', 'ti', 'desenvolvimento', 'programação']:
            return (
                "Você tem uma conta no GitHub? Se sim, qual é o endereço? (Se não tiver, digite 'não')",
                'github',
                ['Não']
            )
        else:
            return (
                "Vamos prosseguir. O que você prefere adicionar primeiro? (Você pode finalizar a qualquer momento digitando 'finalizar')",
                'escolher_proximo',
                ['Formação Acadêmica', 'Experiência Profissional', 'Cursos e Certificados', 'Projetos', 'Idiomas', 'Finalizar']
            )
    
    # Etapa de GitHub
    elif etapa == 'github':
        if mensagem.lower() not in ['não', 'nao', 'no', 'n']:
            dados_curriculo['informacoes_pessoais']['github'] = mensagem.strip()
        
        session['dados_curriculo'] = dados_curriculo
        
        return (
            "Vamos prosseguir. O que você prefere adicionar primeiro? (Você pode finalizar a qualquer momento digitando 'finalizar')",
            'escolher_proximo',
            ['Formação Acadêmica', 'Experiência Profissional', 'Cursos e Certificados', 'Projetos', 'Idiomas', 'Finalizar']
        )
    
    # Etapa para escolher próxima seção
    elif etapa == 'escolher_proximo':
        opcao = mensagem.lower()
        
        if 'finalizar' in opcao or 'concluir' in opcao or 'pronto' in opcao:
            return (
                "Deseja finalizar seu currículo? Todas as informações já foram salvas.",
                'finalizar',
                ['Sim, finalizar', 'Não, continuar editando']
            )
        elif 'formação' in opcao or 'formacao' in opcao:
            return (
                "Você possui alguma formação acadêmica para adicionar?",
                'formacao_pergunta',
                ['Sim', 'Não']
            )
        elif 'experiência' in opcao or 'experiencia' in opcao:
            return (
                "Você possui alguma experiência profissional para adicionar?",
                'experiencia_pergunta',
                ['Sim', 'Não']
            )
        elif 'curso' in opcao or 'certificado' in opcao:
            return (
                "Você possui cursos, certificados ou licenças para adicionar?",
                'cursos_pergunta',
                ['Sim', 'Não']
            )
        elif 'projeto' in opcao:
            return (
                "Você tem projetos relevantes para adicionar ao seu currículo?",
                'projetos_pergunta',
                ['Sim', 'Não']
            )
        elif 'idioma' in opcao:
            return (
                "Você deseja adicionar idiomas ao seu currículo?",
                'idiomas_pergunta',
                ['Sim', 'Não']
            )
        else:
            return (
                "Desculpe, não entendi sua escolha. O que você gostaria de adicionar agora? (Você pode finalizar a qualquer momento digitando 'finalizar')",
                'escolher_proximo',
                ['Formação Acadêmica', 'Experiência Profissional', 'Cursos e Certificados', 'Projetos', 'Idiomas', 'Finalizar']
            )
    
    # Etapa de pergunta sobre formação acadêmica
    elif etapa == 'formacao_pergunta':
        if mensagem.lower() in ['sim', 'yes', 's', 'y']:
            return (
                "Qual é a instituição de ensino?",
                'formacao_instituicao',
                []
            )
        else:
            return (
                "O que você gostaria de adicionar agora? (Você pode finalizar a qualquer momento digitando 'finalizar')",
                'escolher_proximo',
                ['Experiência Profissional', 'Cursos e Certificados', 'Projetos', 'Idiomas', 'Finalizar']
            )
    
    # Etapa de formação - instituição
    elif etapa == 'formacao_instituicao':
        # Verificar se o usuário quer finalizar
        if mensagem.lower() in ['finalizar', 'concluir', 'pronto']:
            return (
                "Deseja finalizar seu currículo? Todas as informações já foram salvas.",
                'finalizar',
                ['Sim, finalizar', 'Não, continuar editando']
            )
        
        # Inicializar formação atual se não existir
        if 'formacao_atual' not in session:
            session['formacao_atual'] = {}
        
        formacao_atual = session.get('formacao_atual', {})
        formacao_atual['instituicao'] = mensagem.strip()
        session['formacao_atual'] = formacao_atual
        
        return (
            "Qual diploma ou grau você obteve? (Técnico, Tecnólogo, Bacharel, Licenciatura, MBA, Pós-Graduação, Mestrado, Doutorado, Pós-Doutorado)",
            'formacao_diploma',
            ['Técnico', 'Tecnólogo', 'Bacharel', 'Licenciatura', 'MBA', 'Pós-Graduação', 'Mestrado', 'Doutorado', 'Pós-Doutorado']
        )
    
    # Etapa de formação - diploma
    elif etapa == 'formacao_diploma':
        # Verificar se o usuário quer finalizar
        if mensagem.lower() in ['finalizar', 'concluir', 'pronto']:
            return (
                "Deseja finalizar seu currículo? Todas as informações já foram salvas.",
                'finalizar',
                ['Sim, finalizar', 'Não, continuar editando']
            )
        
        formacao_atual = session.get('formacao_atual', {})
        formacao_atual['diploma'] = mensagem.strip()
        session['formacao_atual'] = formacao_atual
        
        return (
            "Qual foi a área de estudo ou curso?",
            'formacao_area',
            []
        )
    
    # Etapa de formação - área
    elif etapa == 'formacao_area':
        # Verificar se o usuário quer finalizar
        if mensagem.lower() in ['finalizar', 'concluir', 'pronto']:
            return (
                "Deseja finalizar seu currículo? Todas as informações já foram salvas.",
                'finalizar',
                ['Sim, finalizar', 'Não, continuar editando']
            )
        
        formacao_atual = session.get('formacao_atual', {})
        formacao_atual['area_estudo'] = mensagem.strip()
        session['formacao_atual'] = formacao_atual
        
        return (
            "Qual foi a data de início? (formato: MM/AAAA)",
            'formacao_data_inicio',
            []
        )
    
    # Etapa de formação - data início
    elif etapa == 'formacao_data_inicio':
        # Verificar se o usuário quer finalizar
        if mensagem.lower() in ['finalizar', 'concluir', 'pronto']:
            return (
                "Deseja finalizar seu currículo? Todas as informações já foram salvas.",
                'finalizar',
                ['Sim, finalizar', 'Não, continuar editando']
            )
        
        formacao_atual = session.get('formacao_atual', {})
        formacao_atual['data_inicio'] = mensagem.strip()
        session['formacao_atual'] = formacao_atual
        
        return (
            "Qual foi a data de conclusão? (formato: MM/AAAA, ou digite 'cursando' se ainda estiver em andamento)",
            'formacao_data_fim',
            ['Cursando']
        )
    
    # Etapa de formação - data fim
    elif etapa == 'formacao_data_fim':
        # Verificar se o usuário quer finalizar
        if mensagem.lower() in ['finalizar', 'concluir', 'pronto']:
            return (
                "Deseja finalizar seu currículo? Todas as informações já foram salvas.",
                'finalizar',
                ['Sim, finalizar', 'Não, continuar editando']
            )
        
        formacao_atual = session.get('formacao_atual', {})
        
        if mensagem.lower() in ['cursando', 'em andamento', 'atual']:
            formacao_atual['data_fim'] = 'Atual'
        else:
            formacao_atual['data_fim'] = mensagem.strip()
        
        session['formacao_atual'] = formacao_atual
        
        return (
            "Descreva brevemente o curso ou programa:",
            'formacao_descricao',
            []
        )
    
    # Etapa de formação - descrição
    elif etapa == 'formacao_descricao':
        # Verificar se o usuário quer finalizar
        if mensagem.lower() in ['finalizar', 'concluir', 'pronto']:
            return (
                "Deseja finalizar seu currículo? Todas as informações já foram salvas.",
                'finalizar',
                ['Sim, finalizar', 'Não, continuar editando']
            )
        
        formacao_atual = session.get('formacao_atual', {})
        formacao_atual['descricao'] = mensagem.strip()
        session['formacao_atual'] = formacao_atual
        
        return (
            "Quais competências técnicas você adquiriu nesta formação? (Separe por vírgulas)",
            'formacao_competencias',
            []
        )
    
    # Etapa de formação - competências
    elif etapa == 'formacao_competencias':
        # Verificar se o usuário quer finalizar
        if mensagem.lower() in ['finalizar', 'concluir', 'pronto']:
            return (
                "Deseja finalizar seu currículo? Todas as informações já foram salvas.",
                'finalizar',
                ['Sim, finalizar', 'Não, continuar editando']
            )
        
        formacao_atual = session.get('formacao_atual', {})
        formacao_atual['competencias'] = mensagem.strip()
        
        # Adicionar formação atual à lista de formações
        dados_curriculo['formacoes_academicas'].append(formacao_atual)
        session['dados_curriculo'] = dados_curriculo
        
        # Limpar formação atual
        session.pop('formacao_atual', None)
        
        return (
            "Formação acadêmica adicionada com sucesso! Deseja adicionar outra formação acadêmica?",
            'formacao_adicionar_outra',
            ['Sim', 'Não']
        )
    
    # Etapa de formação - adicionar outra
    elif etapa == 'formacao_adicionar_outra':
        if mensagem.lower() in ['sim', 'yes', 's', 'y']:
            return (
                "Ótimo! Vamos adicionar outra formação acadêmica. Qual é a instituição de ensino?",
                'formacao_instituicao',
                []
            )
        else:
            return (
                "O que você gostaria de adicionar agora? (Você pode finalizar a qualquer momento digitando 'finalizar')",
                'escolher_proximo',
                ['Experiência Profissional', 'Cursos e Certificados', 'Projetos', 'Idiomas', 'Finalizar']
            )
    
    # Etapa de pergunta sobre cursos
    elif etapa == 'cursos_pergunta':
        if mensagem.lower() in ['sim', 'yes', 's', 'y']:
            return (
                "Qual é o nome do curso ou certificado?",
                'curso_nome',
                []
            )
        else:
            return (
                "O que você gostaria de adicionar agora? (Você pode finalizar a qualquer momento digitando 'finalizar')",
                'escolher_proximo',
                ['Formação Acadêmica', 'Experiência Profissional', 'Projetos', 'Idiomas', 'Finalizar']
            )
    
    # Etapa de curso - nome
    elif etapa == 'curso_nome':
        # Verificar se o usuário quer finalizar
        if mensagem.lower() in ['finalizar', 'concluir', 'pronto']:
            return (
                "Deseja finalizar seu currículo? Todas as informações já foram salvas.",
                'finalizar',
                ['Sim, finalizar', 'Não, continuar editando']
            )
        
        # Inicializar curso atual se não existir
        if 'curso_atual' not in session:
            session['curso_atual'] = {}
        
        curso_atual = session.get('curso_atual', {})
        curso_atual['nome'] = mensagem.strip()
        session['curso_atual'] = curso_atual
        
        return (
            "Qual a instituição ou entidade emissora?",
            'curso_instituicao',
            []
        )
    
    # Continuar com o restante das etapas de cursos...
    
    # Etapa de finalização
    elif etapa == 'finalizar':
        if mensagem.lower() in ['sim', 'sim, finalizar', 'yes', 's', 'y']:
            # Salvar dados do currículo
            data_dir = ensure_data_directory()
            filename = f"curriculo_{session.get('session_id')}.json"
            filepath = os.path.join(data_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(dados_curriculo, f, ensure_ascii=False, indent=4)
            
            return (
                f"Seu currículo foi finalizado e está pronto para download! <a href='/download/{session.get('session_id')}' class='download-btn'>Baixar Currículo</a> Obrigado por usar o CurriculoBot!",
                'concluido',
                ['Iniciar Novo Currículo']
            )
        else:
            return (
                "O que você gostaria de adicionar agora?",
                'escolher_proximo',
                ['Formação Acadêmica', 'Experiência Profissional', 'Cursos e Certificados', 'Projetos', 'Idiomas', 'Finalizar']
            )
    
    # Outras etapas continuam...
    
    # Se chegou até aqui, é uma etapa desconhecida
    return (
        "Parece que tivemos um problema. Vamos recomeçar. Como posso ajudar com seu currículo?",
        'boas_vindas',
        ['Começar']
    )

# Função para gerar prévia do currículo
def gerar_previa(dados):
    previa = ""
    
    # Informações pessoais
    pessoal = dados.get('informacoes_pessoais', {})
    nome_completo = f"{pessoal.get('nome', '')} {pessoal.get('sobrenome', '')}".strip()
    
    if nome_completo:
        previa += f"<h3 class='previa-nome'>{nome_completo}</h3>"
    
    if pessoal.get('email') or pessoal.get('endereco'):
        previa += "<p class='previa-contato'>"
        if pessoal.get('email'):
            previa += f"{pessoal.get('email')}"
            if pessoal.get('endereco'):
                previa += " | "
        if pessoal.get('endereco'):
            previa += f"{pessoal.get('endereco')}"
        previa += "</p>"
    
    # Links
    links = []
    if pessoal.get('site'):
        links.append(f"<a href='{pessoal.get('site')}' target='_blank'>{pessoal.get('site')}</a>")
    if pessoal.get('linkedin'):
        links.append(f"<a href='{pessoal.get('linkedin')}' target='_blank'>{pessoal.get('linkedin')}</a>")
    if pessoal.get('github'):
        links.append(f"<a href='{pessoal.get('github')}' target='_blank'>{pessoal.get('github')}</a>")
    
    if links:
        previa += f"<p class='previa-links'>{' | '.join(links)}</p>"
    
    # Formação Acadêmica
    formacoes = dados.get('formacoes_academicas', [])
    if formacoes:
        previa += "<div class='previa-secao'>"
        previa += "<h4>Formação Acadêmica</h4>"
        
        for formacao in formacoes:
            previa += "<div class='previa-item'>"
            previa += f"<h5>{formacao.get('diploma', '')} em {formacao.get('area_estudo', '')}</h5>"
            previa += f"<p><strong>{formacao.get('instituicao', '')}</strong></p>"
            
            # Data
            if formacao.get('data_inicio'):
                data = formacao.get('data_inicio', '')
                if formacao.get('data_fim'):
                    if formacao.get('data_fim').lower() == 'atual':
                        data += " - Presente"
                    else:
                        data += f" - {formacao.get('data_fim', '')}"
                previa += f"<p>{data}</p>"
            
            # Descrição
            if formacao.get('descricao'):
                previa += f"<p>{formacao.get('descricao', '')}</p>"
            
            # Competências
            if formacao.get('competencias'):
                previa += f"<p><strong>Competências:</strong> {formacao.get('competencias', '')}</p>"
            
            previa += "</div>"
        
        previa += "</div>"
    
    # Experiência Profissional
    experiencias = dados.get('experiencias', [])
    if experiencias:
        previa += "<div class='previa-secao'>"
        previa += "<h4>Experiência Profissional</h4>"
        
        for experiencia in experiencias:
            previa += "<div class='previa-item'>"
            previa += f"<h5>{experiencia.get('cargo', '')}</h5>"
            previa += f"<p><strong>{experiencia.get('empresa', '')}</strong> • {experiencia.get('tipo', '')}</p>"
            
            # Localidade e Modalidade
            localidade_modal = []
            if experiencia.get('localidade'):
                localidade_modal.append(experiencia.get('localidade'))
            if experiencia.get('modalidade'):
                localidade_modal.append(experiencia.get('modalidade'))
            
            if localidade_modal:
                previa += f"<p>{' • '.join(localidade_modal)}</p>"
            
            # Data
            if experiencia.get('data_inicio'):
                data = experiencia.get('data_inicio', '')
                if experiencia.get('data_fim'):
                    if experiencia.get('data_fim').lower() == 'atual':
                        data += " - Presente"
                    else:
                        data += f" - {experiencia.get('data_fim', '')}"
                previa += f"<p>{data}</p>"
            
            # Descrição
            if experiencia.get('descricao'):
                previa += f"<p>{experiencia.get('descricao', '')}</p>"
            
            previa += "</div>"
        
        previa += "</div>"
    
    # Cursos e Certificados
    cursos = dados.get('cursos', [])
    if cursos:
        previa += "<div class='previa-secao'>"
        previa += "<h4>Cursos e Certificados</h4>"
        
        for curso in cursos:
            previa += "<div class='previa-item'>"
            previa += f"<h5>{curso.get('nome', '')}</h5>"
            previa += f"<p><strong>{curso.get('instituicao', '')}</strong></p>"
            
            # Data
            if curso.get('data_inicio') or curso.get('data_fim'):
                data = ""
                if curso.get('data_inicio'):
                    data = curso.get('data_inicio', '')
                    if curso.get('data_fim'):
                        if curso.get('data_fim').lower() == 'atual':
                            data += " - Presente"
                        else:
                            data += f" - {curso.get('data_fim', '')}"
                elif curso.get('data_fim'):
                    data = f"Concluído em {curso.get('data_fim', '')}"
                
                if data:
                    previa += f"<p>{data}</p>"
            
            # Descrição
            if curso.get('descricao'):
                previa += f"<p>{curso.get('descricao', '')}</p>"
            
            previa += "</div>"
        
        previa += "</div>"
    
    # Projetos
    projetos = dados.get('projetos', [])
    if projetos:
        previa += "<div class='previa-secao'>"
        previa += "<h4>Projetos</h4>"
        
        for projeto in projetos:
            previa += "<div class='previa-item'>"
            previa += f"<h5>{projeto.get('nome', '')}</h5>"
            
            # Habilidades
            if projeto.get('habilidades'):
                previa += f"<p><strong>Habilidades:</strong> {projeto.get('habilidades', '')}</p>"
            
            # Descrição
            if projeto.get('descricao'):
                previa += f"<p>{projeto.get('descricao', '')}</p>"
            
            previa += "</div>"
        
        previa += "</div>"
    
    # Idiomas
    idiomas = dados.get('idiomas', [])
    if idiomas:
        previa += "<div class='previa-secao'>"
        previa += "<h4>Idiomas</h4>"
        
        for idioma in idiomas:
            previa += "<div class='previa-item'>"
            previa += f"<h5>{idioma.get('nome', '')}</h5>"
            previa += f"<p><strong>Nível:</strong> {idioma.get('nivel', '')}</p>"
            previa += "</div>"
        
        previa += "</div>"
    
    return previa if previa else "<p>Nenhuma informação adicionada ainda.</p>"

# Rota para baixar o currículo
@app.route('/download/<session_id>')
def download_curriculo(session_id):
    # Verificar se o arquivo existe
    data_dir = ensure_data_directory()
    filename = f"curriculo_{session_id}.json"
    filepath = os.path.join(data_dir, filename)
    
    if not os.path.exists(filepath):
        return "Currículo não encontrado."
    
    # Carregar dados do currículo
    with open(filepath, 'r', encoding='utf-8') as f:
        dados = json.load(f)
    
    # Gerar HTML do currículo
    html = render_template('curriculo.html', dados=dados)
    
    # Retornar para o navegador
    return html

# Rota para iniciar um novo currículo (limpar sessão)
@app.route('/novo')
def novo_curriculo():
    session.clear()
    return redirect(url_for('chatbot'))

if __name__ == '__main__':
    app.run(debug=True)