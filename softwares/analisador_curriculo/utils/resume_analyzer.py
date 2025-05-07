import re
import nltk
import google.generativeai as genai
import json
import os
from dotenv import load_dotenv
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords

# Carregar variáveis de ambiente
load_dotenv()

# Baixar recursos necessários do NLTK
nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)
nltk.download('wordnet', quiet=True)

# Configuração da API do Google Gemini
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)
else:
    print("AVISO: Chave de API do Google Gemini não encontrada. Configure a variável de ambiente GOOGLE_API_KEY.")

def preprocess_text(text):
    """
    Pré-processa o texto extraído do currículo.
    
    Args:
        text (str): Texto extraído do PDF
        
    Returns:
        str: Texto pré-processado
    """
    if not text or not isinstance(text, str):
        return ""
    
    # Remover caracteres especiais e formatar texto
    text = re.sub(r'\s+', ' ', text)  # Substituir múltiplos espaços por um único
    text = text.strip()
    
    return text

def generate_fallback_analysis(resume_text, tipo_analise, nivel, stack_area, skills, text_metrics):
    """
    Gera uma análise básica de fallback quando a API do Google Gemini falha.
    """
    # Analisar parágrafos e seções
    paragraphs = text_metrics['paragraph_count']
    words = text_metrics['word_count']
    sentences = text_metrics['sentence_count']
    
    # Definir skill_count aqui, antes de usá-lo
    skill_count = len(skills)
    
    # Identificar tipos comuns de palavras de ação
    action_words = ['desenvolvi', 'implementei', 'gerenciei', 'liderei', 'criei', 'otimizei', 
                    'aumentei', 'reduzi', 'melhorei', 'coordenei', 'supervisionei', 'projetei']
    
    # Verificar se o currículo contém palavras de ação
    has_action_words = any(word in resume_text.lower() for word in action_words)
    
    # Calcular pontuação básica
    format_score = 60  # Valor padrão médio
    
    # Definir structure_issue aqui antes de usá-lo
    if paragraphs < 3:
        format_score -= 20
        structure_issue = "O currículo parece ter poucas seções ou parágrafos."
    elif paragraphs > 20:
        format_score -= 10
        structure_issue = "O currículo parece ter muitas seções, o que pode dificultar a leitura."
    else:
        structure_issue = "A estrutura do currículo parece adequada em termos de número de seções."
    
    # Ajustar com base no comprimento
    if words < 200:
        format_score -= 15
        length_issue = "O currículo é muito curto, o que pode indicar falta de informações importantes."
    elif words > 1000:
        format_score -= 10
        length_issue = "O currículo é bastante extenso. Considere condensar para melhorar a legibilidade."
    else:
        length_issue = "O comprimento do currículo parece adequado."
        
    # Ajustar com base nas habilidades encontradas
    if skill_count == 0:
        format_score -= 15
        skills_issue = f"Não foram identificadas habilidades específicas para a área de {stack_area}."
    elif skill_count < 3:
        format_score -= 10
        skills_issue = f"Poucas habilidades específicas para {stack_area} foram identificadas."
    else:
        format_score += 10
        skills_issue = f"Foram identificadas várias habilidades relevantes para {stack_area}."
    
    # Determinar nível atual baseado em análise básica
    experience_indicators = ['gerenciei', 'liderei', 'coordenei', 'dirigi', 'chefiei', 'supervisionei']
    has_leadership = any(word in resume_text.lower() for word in experience_indicators)
    
    years_experience = 0
    # Tentar extrair anos de experiência do texto
    experience_patterns = [
        r'(\d+)\s+anos\s+de\s+experiência',
        r'experiência\s+de\s+(\d+)\s+anos',
        r'(\d+)\s+anos\s+na\s+área'
    ]
    
    for pattern in experience_patterns:
        matches = re.findall(pattern, resume_text.lower())
        if matches:
            try:
                years_experience = max(years_experience, int(matches[0]))
            except ValueError:
                pass
    
    # Determinar nível com base em experiência e indicadores
    current_level = "estagiário"
    if years_experience > 8 or (years_experience > 5 and has_leadership):
        current_level = "sênior"
    elif years_experience > 3 or (years_experience > 2 and skill_count > 5):
        current_level = "pleno"
    elif years_experience > 1 or skill_count > 3:
        current_level = "júnior"
    
    # Recomendações para próximo nível
    next_level_map = {
        'estagiário': 'júnior',
        'júnior': 'pleno',
        'pleno': 'sênior',
        'sênior': 'especialista/líder técnico'
    }
    
    next_level = next_level_map.get(current_level, 'especialista')
    
    next_level_reqs = {
        'júnior': 'Desenvolva projetos práticos, aprimore habilidades técnicas fundamentais e busque experiência para consolidar conhecimentos.',
        'pleno': 'Aprofunde suas especialidades técnicas, comece a liderar pequenos projetos e desenvolva habilidades de mentoria.',
        'sênior': 'Desenvolva habilidades de liderança técnica, tome decisões importantes e influencie a direção dos projetos.',
        'especialista/líder técnico': 'Torne-se referência em sua área, compartilhe conhecimento através de publicações ou palestras e lidere inovações.'
    }
    
    next_level_req = next_level_reqs.get(next_level, next_level_reqs['júnior'])
    
    # Gerar recomendações genéricas de cursos e certificações (que serão substituídas pela IA real quando disponível)
    fallback_courses = [
        f"Curso especializado em {stack_area}",
        f"Pós-graduação ou especialização em {stack_area}",
        f"Workshops práticos sobre {stack_area}",
        "Cursos de gestão de projetos",
        "Cursos de desenvolvimento de soft skills"
    ]
    
    fallback_certifications = [
        f"Certificação profissional em {stack_area}",
        "Certificações de ferramentas específicas da área",
        "Certificações reconhecidas internacionalmente",
        "Certificações de gestão",
        "Certificações de metodologias aplicáveis à área"
    ]
    
    fallback_tech_skills = [
        f"Habilidades fundamentais em {stack_area}",
        "Conhecimento de tecnologias emergentes na área",
        "Metodologias aplicáveis à função",
        "Ferramentas específicas do setor",
        "Técnicas avançadas de resolução de problemas"
    ]
    
    fallback_soft_skills = [
        "Comunicação eficaz",
        "Trabalho em equipe",
        "Resolução de problemas",
        "Adaptabilidade",
        "Inteligência emocional"
    ]
    
    # Construir o resultado final
    return {
        "pontuacao_geral": format_score,
        "nivel_atual": current_level,
        "resumo_executivo": f"Análise básica para currículo na área de {stack_area} com {words} palavras e {skill_count} habilidades relevantes identificadas. Este currículo indica um profissional de nível {current_level}. A avaliação básica sugere uma pontuação de {format_score}/100.",
        
        "analise_detalhada": {
            "formatacao_apresentacao": f"O texto extraído contém {paragraphs} parágrafos, o que sugere uma estrutura {paragraphs < 3 and 'simples' or paragraphs > 10 and 'detalhada' or 'adequada'}.",
            "estrutura_organizacao": structure_issue,
            "qualidade_descricoes": f"O currículo contém aproximadamente {sentences} sentenças. {has_action_words and 'Foram identificados verbos de ação, o que é positivo para descrições de experiência.' or 'Não foram identificados muitos verbos de ação, o que pode indicar descrições passivas.'}",
            "relevancia_habilidades": skills_issue,
            "destaque_conquistas": f"{'Verbos de ação que indicam conquistas foram identificados' if has_action_words else 'Não foram identificados muitos verbos que indicam conquistas mensuráveis'}. Recomenda-se utilizar verbos de ação e métricas específicas para destacar realizações.",
            "adequacao_nivel": f"O currículo sugere um profissional de nível {current_level}, enquanto o nível alvo é {nivel}. {current_level == nivel and 'Há alinhamento entre o perfil atual e o desejado.' or 'Há uma lacuna entre o perfil atual e o desejado que pode ser trabalhada com as recomendações fornecidas.'}"
        },
        
        "pontos_fortes": [
            f"O currículo possui {paragraphs} parágrafos, indicando uma estrutura organizada" if paragraphs >= 3 else "O currículo é conciso",
            f"Foram identificadas {skill_count} habilidades relevantes para a área de {stack_area}" if skill_count > 0 else "O currículo tem potencial para destacar mais habilidades específicas",
            "O texto apresenta verbos de ação, o que é positivo para descrições de experiência" if has_action_words else "O currículo tem estrutura básica que pode ser aprimorada",
            f"O comprimento do currículo ({words} palavras) está dentro do esperado" if 300 <= words <= 800 else f"O currículo tem {words} palavras, o que {'pode precisar de mais detalhes' if words < 300 else 'é bastante detalhado'}"
        ],
        
        "oportunidades_melhoria": [
            "Adicione mais verbos de ação e resultados quantificáveis" if not has_action_words else "Refine as descrições com mais dados quantitativos",
            f"Inclua mais habilidades específicas para a área de {stack_area}" if skill_count < 5 else "Continue mantendo as habilidades relevantes atualizadas",
            "Estruture o currículo com seções claras (Experiência, Formação, Habilidades, etc.)" if paragraphs < 3 else "Mantenha a organização das seções",
            "Adicione mais detalhes sobre suas experiências profissionais" if words < 300 else "Mantenha o foco nas experiências mais relevantes",
            "Verifique se o currículo está adaptado para sistemas ATS, usando palavras-chave da vaga"
        ],
        
        "otimizacao_ats": f"O currículo contém {skill_count} palavras-chave relevantes para a área de {stack_area}, o que {'pode ser suficiente' if skill_count >= 3 else 'pode ser insuficiente'} para passar por sistemas ATS (Applicant Tracking Systems). Recomenda-se incluir mais palavras-chave específicas da vaga e da área sem exageros que possam prejudicar a legibilidade.",
        
        "recomendacoes": [
            f"Inclua mais palavras-chave relevantes para a área de {stack_area}" if skill_count < 3 else "Continue mantendo as palavras-chave relevantes",
            "Utilize verbos de ação para descrever suas experiências (desenvolvi, implementei, gerenciei)" if not has_action_words else "Adicione resultados quantificáveis às suas experiências",
            "Estruture seu currículo com seções claras e bem definidas" if paragraphs < 3 else "Mantenha a boa estruturação do currículo",
            "Adapte seu currículo para cada vaga, incluindo palavras-chave do anúncio",
            f"Para o nível {nivel}, enfatize {'sua capacidade de aprendizado e adaptação' if nivel == 'estagiario' or nivel == 'junior' else 'suas habilidades técnicas e realizações' if nivel == 'pleno' else 'sua liderança e impacto nos resultados' if nivel == 'senior' or nivel == 'lideranca' else 'suas habilidades específicas'}"
        ],
        
        "plano_desenvolvimento": {
            "cursos_recomendados": fallback_courses,
            "certificacoes": fallback_certifications,
            "habilidades_tecnicas": fallback_tech_skills,
            "habilidades_comportamentais": fallback_soft_skills,
            "proximo_nivel": f"Para avançar de {current_level} para {next_level}: {next_level_req}"
        }
    }
    
def extract_skills(text, stack_area):
    """
    Extrai habilidades técnicas relevantes do texto do currículo.
    
    Args:
        text (str): Texto do currículo
        stack_area (str): Área/stack de tecnologia para focar
        
    Returns:
        list: Lista de habilidades encontradas
    """
    # Dicionário de habilidades por área
    skill_keywords = {
        # Áreas de tecnologia
        'desenvolvimento web': [
            'html', 'css', 'javascript', 'typescript', 'react', 'angular', 'vue', 
            'node.js', 'express', 'django', 'flask', 'php', 'laravel', 'symfony',
            'ruby on rails', 'asp.net', 'mvc', 'api rest', 'graphql', 'responsive',
            'bootstrap', 'sass', 'less', 'webpack', 'babel', 'pwa', 'spa'
        ],
        'ciência de dados': [
            'python', 'r', 'sql', 'nosql', 'pandas', 'numpy', 'scikit-learn', 
            'tensorflow', 'pytorch', 'keras', 'matplotlib', 'seaborn', 'tableau',
            'power bi', 'hadoop', 'spark', 'big data', 'machine learning', 'nlp',
            'data mining', 'estatística', 'modelagem', 'regressão', 'classificação'
        ],
        'devops': [
            'docker', 'kubernetes', 'aws', 'azure', 'gcp', 'linux', 'unix',
            'shell', 'bash', 'ansible', 'terraform', 'jenkins', 'ci/cd', 'git',
            'github actions', 'monitoramento', 'logs', 'segurança', 'cloud',
            'infraestrutura como código', 'automação', 'pipeline', 'prometheus'
        ],
        'mobile': [
            'swift', 'objective-c', 'ios', 'android', 'kotlin', 'java', 'react native',
            'flutter', 'xamarin', 'firebase', 'ux/ui mobile', 'push notifications',
            'offline', 'híbrido', 'nativo', 'publicação', 'app store', 'play store'
        ],
        'segurança': [
            'pentest', 'ethical hacking', 'vulnerabilidades', 'firewall', 'ids/ips',
            'criptografia', 'vpn', 'compliance', 'lgpd', 'gdpr', 'oauth', 'jwt',
            'autenticação', 'autorização', 'forense', 'incident response', 'malware'
        ],
        
        # Áreas de negócios e administração
        'administração': [
            'gestão', 'planejamento', 'estratégia', 'processos', 'indicadores', 
            'kpis', 'metas', 'resultados', 'performance', 'eficiência', 'produtividade',
            'organização', 'controle', 'qualidade', 'custos', 'orçamento', 'finanças',
            'recursos humanos', 'liderança', 'equipe', 'relatórios', 'análise'
        ],
        'marketing': [
            'branding', 'marca', 'campanha', 'público-alvo', 'mercado', 'mídia social',
            'redes sociais', 'facebook', 'instagram', 'linkedin', 'tiktok', 'seo', 'sem',
            'google ads', 'inbound', 'outbound', 'funil', 'conversão', 'leads', 'crm',
            'copywriting', 'conteúdo', 'métricas', 'analytics', 'persona', 'jornada', 'ux'
        ],
        'vendas': [
            'negociação', 'prospecção', 'leads', 'pipeline', 'crm', 'gestão de clientes',
            'inside sales', 'vendas externas', 'b2b', 'b2c', 'conversão', 'fechamento',
            'proposta', 'follow-up', 'pós-venda', 'retenção', 'upsell', 'cross-sell',
            'quota', 'metas', 'indicadores', 'comissão', 'vendas consultivas'
        ],
        'recursos humanos': [
            'recrutamento', 'seleção', 'entrevista', 'admissão', 'demissão', 'folha',
            'benefícios', 'treinamento', 'desenvolvimento', 'avaliação', 'desempenho',
            'clima organizacional', 'cultura', 'engajamento', 'onboarding', 'sucessão',
            'cargos', 'salários', 'remuneração', 'legislação trabalhista', 'e-social'
        ],
        'financeiro': [
            'contabilidade', 'fiscal', 'tributário', 'impostos', 'demonstrações', 
            'balanço', 'dre', 'fluxo de caixa', 'contas', 'pagamentos', 'recebimentos',
            'conciliação', 'auditoria', 'compliance', 'investimentos', 'roi', 'budget',
            'forecast', 'controladoria', 'custos', 'precificação', 'lucro', 'margem'
        ],
        
        # Áreas de saúde
        'medicina': [
            'diagnóstico', 'tratamento', 'anamnese', 'exame físico', 'prescrição',
            'prontuário', 'patologia', 'fisiologia', 'anatomia', 'farmacologia',
            'prevenção', 'terapêutica', 'prognóstico', 'clínica', 'paciente',
            'consulta', 'cirurgia', 'residência', 'especialização', 'saúde pública'
        ],
        'enfermagem': [
            'cuidados', 'paciente', 'procedimentos', 'medicação', 'sinais vitais',
            'protocolos', 'assistência', 'prevenção', 'higienização', 'curativo',
            'sae', 'processo de enfermagem', 'diagnóstico', 'intervenção', 'evolução',
            'ética', 'humanização', 'sistematização', 'coren', 'dimensionamento'
        ],
        'psicologia': [
            'avaliação', 'intervenção', 'terapia', 'psicoterapia', 'anamnese',
            'diagnóstico', 'tratamento', 'comportamento', 'cognitivo', 'emocional',
            'psicossocial', 'entrevista', 'teste', 'laudo', 'parecer', 'orientação',
            'aconselhamento', 'saúde mental', 'desenvolvimento', 'crp'
        ],
        
        # Áreas de educação
        'educação': [
            'ensino', 'aprendizagem', 'didática', 'pedagogia', 'metodologia',
            'avaliação', 'currículo', 'plano de aula', 'projeto pedagógico',
            'bncc', 'educação infantil', 'ensino fundamental', 'ensino médio',
            'ead', 'educação a distância', 'tecnologia educacional', 'inclusão',
            'assessoria pedagógica', 'coordenação', 'gestão escolar'
        ],
        
        # Áreas jurídicas
        'direito': [
            'processo', 'petição', 'recurso', 'audiência', 'sentença', 'acórdão',
            'jurisprudência', 'doutrina', 'legislação', 'parecer', 'consultivo',
            'civil', 'penal', 'trabalhista', 'tributário', 'administrativo',
            'contencioso', 'contratos', 'compliance', 'due diligence', 'oab'
        ],
        
        # Áreas de engenharia
        'engenharia civil': [
            'projeto', 'execução', 'obra', 'construção', 'estrutura', 'fundação',
            'concreto', 'aço', 'alvenaria', 'hidráulica', 'elétrica', 'orçamento',
            'cronograma', 'fiscalização', 'vistoria', 'laudo', 'perícia', 'crea',
            'nbr', 'autocad', 'revit', 'bim', 'gerenciamento de projetos'
        ],
        'engenharia mecânica': [
            'projetos mecânicos', 'manufatura', 'produção', 'manutenção', 'qualidade',
            'processos', 'automação', 'cad', 'solidworks', 'inventor', 'simulação',
            'resistência dos materiais', 'metrologia', 'hidráulica', 'pneumática',
            'refrigeração', 'hvac', 'cnc', 'lean manufacturing', 'seis sigma'
        ],
        
        # Áreas criativas
        'design': [
            'ux', 'ui', 'user experience', 'interface', 'web design', 'mobile',
            'responsivo', 'wireframe', 'protótipo', 'mockup', 'photoshop', 'illustrator',
            'indesign', 'sketch', 'figma', 'adobe xd', 'design thinking', 'design sprint',
            'direção de arte', 'identidade visual', 'branding', 'tipografia'
        ],
        'audiovisual': [
            'produção', 'direção', 'roteiro', 'filmagem', 'captação', 'edição',
            'montagem', 'finalização', 'pós-produção', 'premiere', 'after effects',
            'davinci resolve', 'animação', 'motion graphics', 'fotografia', 'iluminação',
            'captação de áudio', 'mixagem', 'color grading', 'storyboard'
        ]
    }
    
    # Obter keywords para a área especificada ou usar todas se a área não for reconhecida
    target_skills = skill_keywords.get(stack_area.lower(), [])
    if not target_skills:
        # Combinar todas as habilidades se a área não for reconhecida
        target_skills = [skill for skills in skill_keywords.values() for skill in skills]
    
    # Converter texto para minúsculas para matching case-insensitive
    text_lower = text.lower()
    
    # Encontrar habilidades no texto
    found_skills = []
    for skill in target_skills:
        if re.search(r'\b' + re.escape(skill) + r'\b', text_lower):
            found_skills.append(skill)
    
    return found_skills
    
def basic_text_analysis(text):
    """
    Realiza uma análise básica do texto usando NLTK em vez de spaCy
    
    Args:
        text (str): Texto do currículo
    
    Returns:
        dict: Métricas básicas do texto
    """
    if not text:
        return {
            "word_count": 0,
            "paragraph_count": 0,
            "sentence_count": 0
        }
    
    # Tokenização
    try:
        words = word_tokenize(text.lower())
        paragraphs = len(re.split(r'\n\s*\n', text))
        sentences = len(re.split(r'[.!?]+', text))
        
        # Remover stopwords
        stop_words = set(stopwords.words('portuguese') + stopwords.words('english'))
        filtered_words = [w for w in words if w.isalnum() and w not in stop_words]
        
        return {
            "word_count": len(words),
            "filtered_word_count": len(filtered_words),
            "paragraph_count": paragraphs,
            "sentence_count": sentences
        }
    except Exception as e:
        print(f"Erro na análise básica de texto: {e}")
        return {
            "word_count": len(text.split()),
            "paragraph_count": 1,
            "sentence_count": 1
        }

def analyze_resume_with_gemini(resume_text, tipo_analise, nivel, stack_area, skills, text_metrics):
    """
    Analisa o currículo usando a API do Google Gemini.
    """
    if not GOOGLE_API_KEY:
        raise ValueError("API key do Google Gemini não encontrada. Configure a variável de ambiente GOOGLE_API_KEY.")

    # Criar o modelo Gemini Pro
    model = genai.GenerativeModel('gemini-pro')
    
    # Preparar o prompt para o modelo
    skills_str = ", ".join(skills) if skills else "Nenhuma habilidade específica identificada."
    
    prompt = f"""
    Você é um analisador de currículos profissional e especialista em desenvolvimento de carreira, com conhecimento profundo em todas as áreas profissionais. Sua tarefa é avaliar minuciosamente o currículo a seguir para a área de {stack_area}.

    Considere os seguintes parâmetros na sua análise:
    - Tipo de análise: {tipo_analise}
    - Nível profissional alvo: {nivel}
    - Área profissional: {stack_area}

    Texto do currículo:
    {resume_text}

    Habilidades identificadas: {skills_str}

    Métricas do texto:
    - Total de palavras: {text_metrics['word_count']}
    - Parágrafos: {text_metrics['paragraph_count']}
    - Sentenças: {text_metrics['sentence_count']}

    Forneça uma análise detalhada e estruturada no formato JSON com os seguintes componentes:
    1. pontuacao_geral: Um número entre 0 e 100
    2. nivel_atual: A classificação do nível profissional atual com base no currículo (estagiário, júnior, pleno, sênior, especialista)
    3. resumo_executivo: Um parágrafo resumindo as principais impressões
    4. analise_detalhada:
        a. formatacao_apresentacao: Avaliação da clareza, organização e legibilidade
        b. estrutura_organizacao: Avaliação da estrutura e organização do conteúdo
        c. qualidade_descricoes: Avaliação das descrições de experiência profissional
        d. relevancia_habilidades: Avaliação das habilidades técnicas para a área especificada
        e. destaque_conquistas: Avaliação de conquistas e resultados mensuráveis
        f. adequacao_nivel: Avaliação da adequação para o nível profissional alvo e especificar qual o nível atual do profissional
    5. pontos_fortes: Lista de 3-5 aspectos mais positivos do currículo
    6. oportunidades_melhoria: Lista de 3-5 sugestões específicas de melhoria
    7. otimizacao_ats: Avaliação se o currículo está otimizado para sistemas de rastreamento
    8. recomendacoes: Lista de sugestões específicas considerando a área profissional mencionada
    9. plano_desenvolvimento:
        a. cursos_recomendados: Lista de 3-5 cursos ESPECÍFICOS com nomes de cursos reais e instituições reais para a área, evitando generalizações e recomendações vagas
        b. certificacoes: Lista de 3-5 certificações ESPECÍFICAS relevantes para a área que agregariam valor, com nomes exatos de certificações reconhecidas
        c. habilidades_tecnicas: Lista de 3-5 habilidades técnicas específicas que devem ser desenvolvidas, adequadas à área
        d. habilidades_comportamentais: Lista de 3-5 soft skills importantes para evoluir na área
        e. proximo_nivel: Detalhes sobre o que é necessário para avançar ao próximo nível profissional

    IMPORTANTE:
    1. Seja ALTAMENTE ESPECÍFICO nas recomendações, garantindo que as sugestões são ÚNICAS para o currículo analisado e não genéricas.
    2. Para a área de {stack_area}, pesquise profundamente e recomende cursos, certificações e habilidades que são REALMENTE RELEVANTES para essa área específica, não apenas recomendações genéricas.
    3. Inclua nomes reais e atuais de cursos, plataformas de ensino específicas, certificações reconhecidas pelo mercado, e instituições educacionais legítimas.
    4. Se o currículo for de uma área não-tecnológica (como saúde, direito, educação, etc.), garanta que as recomendações sejam 100% adequadas para aquela área, evitando recomendações voltadas para tecnologia quando não for apropriado.
    5. Caso o mesmo currículo seja analisado múltiplas vezes com pequenas modificações, ofereça recomendações diferentes para demonstrar um caminho de evolução, nunca repetindo exatamente as mesmas recomendações.
    6. Analise de forma crítica as lacunas no perfil do candidato, oferecendo sugestões personalizadas de desenvolvimento.

    Deve retornar APENAS o JSON, sem texto adicional ou explicações.
    """

    # Gerar resposta
    response = model.generate_content(prompt)
    
    # Extrair o JSON da resposta
    response_text = response.text
    
    # Limpar o texto para garantir que é um JSON válido
    json_start = response_text.find('{')
    json_end = response_text.rfind('}') + 1
    
    if json_start >= 0 and json_end > json_start:
        json_str = response_text[json_start:json_end]
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            print(f"Erro ao decodificar JSON: {e}")
            print(f"JSON recebido: {json_str}")
            # Tentar limpar ainda mais o JSON
            json_str = re.sub(r'```json|```', '', json_str).strip()
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                raise ValueError(f"Não foi possível extrair um JSON válido da resposta do modelo Gemini")
    else:
        raise ValueError(f"Não foi possível identificar JSON na resposta: {response_text}")

def analyze_resume(resume_text, tipo_analise, nivel, stack_area):
    """
    Analisa o currículo usando IA e retorna uma análise estruturada.
    
    Args:
        resume_text (str): Texto extraído do currículo
        tipo_analise (str): Tipo de análise desejada
        nivel (str): Nível profissional
        stack_area (str): Área/stack de tecnologia
        
    Returns:
        dict: Resultado da análise estruturada
    """
    # Pré-processar o texto
    processed_text = preprocess_text(resume_text)
    
    # Extrair habilidades
    skills = extract_skills(processed_text, stack_area)
    
    # Análise básica de texto (substituindo análise do spaCy)
    text_metrics = basic_text_analysis(processed_text)
    
    # Executar a análise usando o Google Gemini
    try:
        analysis_result = analyze_resume_with_gemini(
            resume_text=processed_text[:8000],  # Limitar tamanho para evitar exceder limites da API
            tipo_analise=tipo_analise,
            nivel=nivel,
            stack_area=stack_area,
            skills=skills,
            text_metrics=text_metrics
        )
        
        # Adicionar metadados da análise
        analysis_result["metadados"] = {
            "tipo_analise": tipo_analise,
            "nivel": nivel,
            "stack_area": stack_area,
            "habilidades_identificadas": skills,
            "metricas_texto": text_metrics
        }
        
        return analysis_result
    
    except Exception as e:
        print(f"Erro na análise do currículo: {e}")
        # Usar análise básica de fallback em caso de erro
        fallback_result = generate_fallback_analysis(
            resume_text=processed_text,
            tipo_analise=tipo_analise,
            nivel=nivel,
            stack_area=stack_area,
            skills=skills,
            text_metrics=text_metrics
        )
        
        # Adicionar metadados e informação de erro
        fallback_result["metadados"] = {
            "tipo_analise": tipo_analise,
            "nivel": nivel,
            "stack_area": stack_area,
            "habilidades_identificadas": skills,
            "metricas_texto": text_metrics,
            "analise_completa": False
        }
        fallback_result["erro"] = str(e)
        
        return fallback_result