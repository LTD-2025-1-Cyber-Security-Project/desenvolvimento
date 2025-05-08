#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Serviço de integração com a API do Google Gemini.
Este módulo implementa a comunicação e funcionalidades baseadas no modelo de IA da Google.
"""

import google.generativeai as genai
from flask import current_app
import json
from tenacity import retry, stop_after_attempt, wait_exponential
import logging

logger = logging.getLogger(__name__)

class GeminiService:
    """Classe de serviço para integração com Google Gemini."""
    
    def __init__(self, api_key=None):
        """Inicializa o serviço com a chave da API."""
        self.api_key = api_key
        self.model = None
        
    def initialize(self):
        """Inicializa o cliente da API Gemini."""
        if not self.api_key:
            # Obtém a chave da configuração da aplicação
            self.api_key = current_app.config.get('GOOGLE_GEMINI_API_KEY')
            
        if not self.api_key:
            raise ValueError("Chave da API do Google Gemini não configurada")
            
        # Configura a API
        genai.configure(api_key=self.api_key)
        
        # Carrega o modelo Gemini Pro
        self.model = genai.GenerativeModel('gemini-pro')
    
    def get_model(self):
        """Obtém o modelo, inicializando-o se necessário."""
        if not self.model:
            self.initialize()
        return self.model
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def generate_content(self, prompt, temperature=0.7, max_tokens=2048):
        """Gera conteúdo com o modelo de IA, com mecanismo de retry em caso de falha."""
        try:
            model = self.get_model()
            
            # Configura os parâmetros da geração
            generation_config = {
                'temperature': temperature,
                'max_output_tokens': max_tokens,
                'top_p': 0.95,
                'top_k': 40
            }
            
            # Gera o conteúdo
            response = model.generate_content(
                prompt,
                generation_config=generation_config
            )
            
            return response.text
        except Exception as e:
            logger.error(f"Erro ao gerar conteúdo com Gemini: {str(e)}")
            raise
    
    def format_json_response(self, text):
        """Formata uma resposta de texto em JSON."""
        try:
            # Tenta extrair o JSON da resposta, removendo possíveis textos extras
            json_start = text.find('{')
            json_end = text.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_text = text[json_start:json_end]
                return json.loads(json_text)
            else:
                # Caso não encontre um objeto JSON, tenta extrair lista
                json_start = text.find('[')
                json_end = text.rfind(']') + 1
                
                if json_start >= 0 and json_end > json_start:
                    json_text = text[json_start:json_end]
                    return json.loads(json_text)
                    
            # Se não for possível extrair JSON, retorna o texto como está
            return {"text": text}
        except json.JSONDecodeError:
            # Em caso de erro de decodificação, retorna o texto original
            return {"text": text}
    
    def generate_quiz_questions(self, title, content, difficulty='medium', count=5):
        """Gera questões de quiz com base no conteúdo de uma lição."""
        prompt = f"""
        Você é um especialista em educação, criando questões de quiz para uma plataforma educacional.
        Gere {count} questões de múltipla escolha sobre o seguinte conteúdo:
        
        Título: {title}
        
        Conteúdo: {content[:5000]}
        
        Nível de dificuldade: {difficulty}
        
        Para cada questão inclua:
        1. O texto da pergunta
        2. 4 alternativas (rotuladas de A a D)
        3. A alternativa correta
        4. Uma breve explicação sobre a resposta correta
        
        Retorne as questões em formato JSON usando este modelo:
        [
            {{
                "question": "Texto da pergunta",
                "type": "multiple_choice",
                "options": [
                    "Alternativa A",
                    "Alternativa B",
                    "Alternativa C",
                    "Alternativa D"
                ],
                "correct_answer": "0",  // Índice da resposta correta (0, 1, 2 ou 3)
                "explanation": "Explicação da resposta correta"
            }},
            // ... mais questões
        ]
        
        Certifique-se de que as questões:
        - Estejam diretamente relacionadas ao conteúdo
        - Sejam variadas em formato e complexidade
        - Sejam claras e não ambíguas
        - Tenham apenas uma resposta correta
        - Tenham explicações precisas e informativas
        """
        
        # Gera as questões
        response = self.generate_content(prompt, temperature=0.7)
        
        # Formata e valida a resposta JSON
        questions = self.format_json_response(response)
        
        # Se a resposta não for uma lista, tenta encontrar a lista dentro da resposta
        if not isinstance(questions, list):
            for key, value in questions.items():
                if isinstance(value, list):
                    questions = value
                    break
            else:
                # Se ainda não encontrou uma lista, retorna uma lista vazia
                logger.error(f"Não foi possível extrair as questões da resposta: {response}")
                return []
        
        return questions
    
    def generate_quiz(self, title, content, difficulty='medium', question_count=5):
        """Gera um quiz completo com título, descrição e questões."""
        prompt = f"""
        Você é um especialista em educação criando um quiz para uma plataforma educacional.
        Gere um quiz completo sobre o seguinte conteúdo:
        
        Título: {title}
        
        Conteúdo: {content[:5000]}
        
        Nível de dificuldade: {difficulty}
        
        Seu quiz deve incluir:
        1. Uma descrição do quiz (2-3 frases)
        2. {question_count} questões de múltipla escolha
        
        Para cada questão inclua:
        1. O texto da pergunta
        2. 4 alternativas (rotuladas de A a D)
        3. A alternativa correta
        4. Uma breve explicação sobre a resposta correta
        
        Retorne o quiz em formato JSON usando este modelo:
        {{
            "description": "Descrição do quiz",
            "questions": [
                {{
                    "question": "Texto da pergunta",
                    "type": "multiple_choice",
                    "options": [
                        "Alternativa A",
                        "Alternativa B",
                        "Alternativa C",
                        "Alternativa D"
                    ],
                    "correct_answer": "0",  // Índice da resposta correta (0, 1, 2 ou 3)
                    "explanation": "Explicação da resposta correta"
                }},
                // ... mais questões
            ]
        }}
        """
        
        # Gera o quiz
        response = self.generate_content(prompt, temperature=0.7)
        
        # Formata e valida a resposta JSON
        quiz_data = self.format_json_response(response)
        
        return quiz_data
    
    def generate_single_question(self, title, content, difficulty='medium', question_type='multiple_choice'):
        """Gera uma única questão com base no conteúdo de uma lição."""
        prompt = f"""
        Você é um especialista em educação gerando uma questão para uma plataforma educacional.
        Gere UMA questão de {question_type} sobre o seguinte conteúdo:
        
        Título: {title}
        
        Conteúdo: {content[:5000]}
        
        Nível de dificuldade: {difficulty}
        
        Para a questão inclua:
        1. O texto da pergunta
        2. 4 alternativas (se for múltipla escolha)
        3. A alternativa correta
        4. Uma breve explicação sobre a resposta correta
        
        Retorne a questão em formato JSON usando este modelo:
        {{
            "question": "Texto da pergunta",
            "type": "{question_type}",
            "options": [
                "Alternativa A",
                "Alternativa B",
                "Alternativa C",
                "Alternativa D"
            ],
            "correct_answer": "0",  // Índice da resposta correta (0, 1, 2 ou 3)
            "explanation": "Explicação da resposta correta"
        }}
        
        Certifique-se de que a questão:
        - Esteja diretamente relacionada ao conteúdo
        - Seja clara e não ambígua
        - Tenha apenas uma resposta correta
        - Tenha uma explicação precisa e informativa
        """
        
        # Gera a questão
        response = self.generate_content(prompt, temperature=0.7)
        
        # Formata e valida a resposta JSON
        question = self.format_json_response(response)
        
        return question
    
    def ask_assistant(self, question, context=None, user_name=None, user_level=None):
        """Permite que o usuário faça perguntas ao assistente virtual de IA."""
        context_info = ""
        if context:
            context_info = f"Contexto: {context}\n\n"
        
        user_info = ""
        if user_name and user_level:
            user_info = f"O usuário se chama {user_name} e está no nível {user_level}."
        
        prompt = f"""
        Você é um assistente educacional especializado em Inteligência Artificial e Cybersegurança, 
        integrante de uma plataforma de ensino para funcionários de prefeituras.
        
        {context_info}
        {user_info}
        
        Responda à seguinte pergunta de forma didática, clara e concisa:
        
        {question}
        
        Sua resposta deve:
        - Ser educativa e informativa
        - Usar linguagem simples, mas precisa
        - Ter no máximo 3 parágrafos (a menos que seja necessário detalhar um conceito técnico)
        - Incluir exemplos práticos relevantes ao contexto de administração pública, quando possível
        - Priorizar explicações que foquem em aplicações práticas do conhecimento
        """
        
        # Gera a resposta
        response = self.generate_content(prompt, temperature=0.5, max_tokens=2048)
        
        return response
    
    def get_course_recommendations(self, user_profile):
        """Gera recomendações de cursos personalizadas para o usuário."""
        profile_json = json.dumps(user_profile, ensure_ascii=False)
        
        prompt = f"""
        Você é um assistente educacional especializado em recomendar cursos para uma plataforma de ensino.
        
        Aqui está o perfil do usuário em formato JSON:
        {profile_json}
        
        Com base no perfil do usuário, recomende 3 cursos que ele ainda não está matriculado.
        Os cursos devem ser adequados ao nível de experiência do usuário e alinhados com seus interesses.
        
        Os cursos disponíveis na plataforma abrangem:
        - Inteligência Artificial: fundamentos, aprendizado de máquina, processamento de linguagem natural, visão computacional, ética em IA
        - Cybersegurança: segurança de redes, criptografia, análise de vulnerabilidades, resposta a incidentes, segurança no governo digital
        
        Para cada curso, forneça:
        1. Um título realista
        2. Uma breve descrição
        3. Um nível de relevância para o usuário (alta, média, baixa)
        
        Retorne as recomendações em formato JSON:
        [
            {{
                "title": "Título do Curso",
                "description": "Breve descrição do curso",
                "relevance": "alta"
            }},
            // ... mais recomendações
        ]
        """
        
        # Gera as recomendações
        response = self.generate_content(prompt, temperature=0.7)
        
        # Formata e valida a resposta JSON
        recommendations = self.format_json_response(response)
        
        # Se a resposta não for uma lista, tenta encontrar a lista dentro da resposta
        if not isinstance(recommendations, list):
            for key, value in recommendations.items():
                if isinstance(value, list):
                    recommendations = value
                    break
            else:
                # Se ainda não encontrou uma lista, retorna uma lista vazia
                logger.error(f"Não foi possível extrair as recomendações da resposta: {response}")
                return []
        
        return recommendations
    
    def generate_course_overview(self, title, description, lessons):
        """Gera uma visão geral de um curso com base em seu título, descrição e lições."""
        lessons_json = json.dumps(lessons, ensure_ascii=False)
        
        prompt = f"""
        Você é um especialista educacional analisando um curso para uma plataforma de ensino.
        
        Aqui estão as informações do curso:
        
        Título: {title}
        
        Descrição: {description}
        
        Lições do curso (em formato JSON):
        {lessons_json}
        
        Com base nessas informações, gere uma visão geral do curso que inclua:
        1. Um resumo conciso do curso (máximo 3 parágrafos)
        2. 5 pontos-chave que serão aprendidos
        3. 3-5 resultados de aprendizagem esperados após a conclusão do curso
        
        Retorne a visão geral em formato JSON:
        {{
            "summary": "Resumo do curso...",
            "key_points": [
                "Ponto-chave 1",
                "Ponto-chave 2",
                // ...
            ],
            "learning_outcomes": [
                "Resultado de aprendizagem 1",
                "Resultado de aprendizagem 2",
                // ...
            ]
        }}
        """
        
        # Gera a visão geral
        response = self.generate_content(prompt, temperature=0.5)
        
        # Formata e valida a resposta JSON
        overview = self.format_json_response(response)
        
        return overview
    
    def generate_study_recommendations(self, module_title, lessons_content, current_score):
        """Gera recomendações de estudo baseadas no desempenho do usuário em um módulo."""
        prompt = f"""
        Você é um mentor educacional oferecendo recomendações de estudo personalizadas.
        
        O usuário está estudando o seguinte módulo:
        
        Título do módulo: {module_title}
        
        Conteúdo das lições:
        {lessons_content[:5000]}
        
        O usuário obteve uma pontuação de {current_score}% nos testes deste módulo.
        
        Com base nessas informações, forneça:
        1. 3-5 dicas de estudo específicas para melhorar o entendimento
        2. 2-3 recursos adicionais (livros, sites, vídeos) que possam ajudar
        
        Suas recomendações devem ser:
        - Específicas para o conteúdo do módulo
        - Apropriadas para o nível de desempenho atual
        - Acionáveis e práticas
        
        Retorne as recomendações em formato JSON:
        {{
            "tips": [
                "Dica de estudo 1",
                "Dica de estudo 2",
                // ...
            ],
            "resources": [
                "Recurso 1",
                "Recurso 2",
                // ...
            ]
        }}
        """
        
        # Gera as recomendações
        response = self.generate_content(prompt, temperature=0.7)
        
        # Formata e valida a resposta JSON
        recommendations = self.format_json_response(response)
        
        return recommendations
    
    def generate_practice_exercises(self, title, content, difficulty='medium', user_level=None):
        """Gera exercícios práticos personalizados para uma lição."""
        user_info = f"O usuário está no nível {user_level}." if user_level else ""
        
        prompt = f"""
        Você é um instrutor educacional criando exercícios práticos para uma plataforma de ensino.
        
        {user_info}
        
        Gere exercícios práticos para a seguinte lição:
        
        Título: {title}
        
        Conteúdo: {content[:5000]}
        
        Nível de dificuldade: {difficulty}
        
        Crie 3 exercícios práticos que:
        1. Apliquem diretamente o conhecimento da lição
        2. Sejam relevantes para funcionários de prefeituras
        3. Tenham exemplos concretos e aplicáveis ao dia a dia
        4. Incluam respostas ou soluções detalhadas
        
        Para cada exercício, forneça:
        - Enunciado claro
        - Instruções específicas
        - Exemplos ou dados necessários
        - Resposta esperada ou solução
        
        Retorne os exercícios em formato JSON:
        {{
            "exercises": [
                {{
                    "title": "Título do exercício",
                    "description": "Descrição detalhada",
                    "instructions": "Instruções passo a passo",
                    "example": "Exemplos ou dados",
                    "solution": "Solução detalhada"
                }},
                // ... mais exercícios
            ]
        }}
        """
        
        # Gera os exercícios
        response = self.generate_content(prompt, temperature=0.7)
        
        # Formata e valida a resposta JSON
        exercises = self.format_json_response(response)
        
        return exercises