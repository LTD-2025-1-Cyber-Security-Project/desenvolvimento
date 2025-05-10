import os
import google.generativeai as genai
from datetime import datetime

def analyze_resume(resume_text, tipo_analise='geral', nivel='junior', stack_area='desenvolvimento web'):
    
    # Configurar API do Google
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise Exception("Chave de API do Google Gemini não configurada")
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-pro')
    
    # Construir prompt para o Gemini
    prompt = f'''
    Analise este currículo para uma vaga de {nivel} em {stack_area}.
    Tipo de análise: {tipo_analise}
    
    Currículo:
    {resume_text}
    
    Forneça uma análise estruturada nos seguintes tópicos:
    1. Resumo de habilidades e experiência
    2. Pontos fortes
    3. Áreas para desenvolvimento
    4. Adequação para a vaga de {nivel} em {stack_area}
    5. Recomendações para melhorar o currículo
    '''
    
    try:
        # Gerar resposta
        response = model.generate_content(prompt)
        result = response.text
        
        # Formatar resultado
        analysis = {
            'resumo': result,
            'tipo_analise': tipo_analise,
            'nivel': nivel,
            'stack_area': stack_area,
            'data_analise': datetime.now().strftime('%d/%m/%Y %H:%M')
        }
        
        return analysis
        
    except Exception as e:
        raise Exception(f"Erro na análise com Gemini API: {str(e)}")