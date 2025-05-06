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
    
    Args:
        resume_text (str): Texto processado do currículo
        tipo_analise (str): Tipo de análise desejada
        nivel (str): Nível profissional
        stack_area (str): Área/stack de tecnologia
        skills (list): Lista de habilidades identificadas
        text_metrics (dict): Métricas básicas do texto
        
    Returns:
        dict: Resultado da análise estruturada em formato de dicionário
    """
    if not GOOGLE_API_KEY:
        raise ValueError("API key do Google Gemini não encontrada. Configure a variável de ambiente GOOGLE_API_KEY.")

    # Criar o modelo Gemini Pro
    model = genai.GenerativeModel('gemini-pro')
    
    # Preparar o prompt para o modelo
    skills_str = ", ".join(skills) if skills else "Nenhuma habilidade específica identificada."
    
    prompt = f"""
    Você é um analisador de currículos profissional desenvolvido com IA avançada. Sua tarefa é avaliar minuciosamente o currículo a seguir.

    Considere os seguintes parâmetros na sua análise:
    - Tipo de análise: {tipo_analise}
    - Nível profissional: {nivel}
    - Stack/Área de tecnologia: {stack_area}

    Texto do currículo:
    {resume_text}

    Habilidades técnicas identificadas: {skills_str}
    
    Métricas do texto:
    - Total de palavras: {text_metrics['word_count']}
    - Parágrafos: {text_metrics['paragraph_count']}
    - Sentenças: {text_metrics['sentence_count']}

    Forneça uma análise detalhada e estruturada no formato JSON com os seguintes componentes:
    1. pontuacao_geral: Um número entre 0 e 100
    2. resumo_executivo: Um parágrafo resumindo as principais impressões
    3. analise_detalhada:
        a. formatacao_apresentacao: Avaliação da clareza, organização e legibilidade
        b. estrutura_organizacao: Avaliação da estrutura e organização do conteúdo
        c. qualidade_descricoes: Avaliação das descrições de experiência profissional
        d. relevancia_habilidades: Avaliação das habilidades técnicas para a área especificada
        e. destaque_conquistas: Avaliação de conquistas e resultados mensuráveis
        f. adequacao_nivel: Avaliação da adequação para o nível profissional indicado
    4. pontos_fortes: Lista de 3-5 aspectos mais positivos do currículo
    5. oportunidades_melhoria: Lista de 3-5 sugestões específicas de melhoria
    6. otimizacao_ats: Avaliação se o currículo está otimizado para sistemas de rastreamento
    7. recomendacoes: Lista de sugestões específicas considerando a área/stack mencionada

    Deve retornar APENAS o JSON, sem texto adicional ou explicações.
    """

    # Gerar resposta
    response = model.generate_content(prompt)
    
    # Extrair o JSON da resposta
    response_text = response.text
    
    # Limpar o texto para garantir que é um JSON válido
    # Remover qualquer texto antes e depois do JSON, se existir
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
        # Retornar análise básica em caso de erro
        return {
            "pontuacao_geral": 50,
            "resumo_executivo": "Não foi possível gerar uma análise completa devido a um erro no processamento.",
            "analise_detalhada": {
                "formatacao_apresentacao": "Não avaliado",
                "estrutura_organizacao": "Não avaliado",
                "qualidade_descricoes": "Não avaliado",
                "relevancia_habilidades": "Não avaliado",
                "destaque_conquistas": "Não avaliado",
                "adequacao_nivel": "Não avaliado"
            },
            "pontos_fortes": ["Não foi possível identificar pontos fortes"],
            "oportunidades_melhoria": ["Recomendamos revisar e reenviar o currículo"],
            "otimizacao_ats": "Não avaliado",
            "recomendacoes": ["Consulte um especialista em currículo"],
            "metadados": {
                "tipo_analise": tipo_analise,
                "nivel": nivel,
                "stack_area": stack_area,
                "habilidades_identificadas": skills,
                "metricas_texto": text_metrics
            },
            "erro": str(e)
        }