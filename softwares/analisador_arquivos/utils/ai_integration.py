import google.generativeai as genai
from flask import current_app
import logging
from typing import Dict, Any, List, Optional
import json

class AIIntegration:
    """Integração com Google Gemini AI para processamento avançado de texto"""
    
    def __init__(self):
        self.api_key = current_app.config.get('GOOGLE_AI_API_KEY')
        if not self.api_key:
            raise ValueError("Google AI API key não configurada")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-pro')
    
    def generate_content(self, prompt: str) -> str:
        """Gera conteúdo baseado em um prompt"""
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            logging.error(f"Erro ao gerar conteúdo: {str(e)}")
            raise
    
    def analyze_document(self, text: str) -> Dict[str, Any]:
        """Analisa um documento e retorna insights estruturados"""
        prompt = f"""
        Analise o seguinte documento e forneça uma análise detalhada:
        
        1. Resumo executivo (máximo 300 palavras)
        2. Principais pontos-chave (5-7 pontos)
        3. Temas e tópicos abordados
        4. Análise de sentimento geral
        5. Recomendações ou ações sugeridas
        6. Palavras-chave relevantes
        
        Documento:
        {text[:5000]}
        
        Formate a resposta em JSON válido.
        """
        
        try:
            response = self.model.generate_content(prompt)
            return self._parse_json_response(response.text)
        except Exception as e:
            logging.error(f"Erro na análise do documento: {str(e)}")
            return {"error": str(e)}
    
    def summarize_text(self, text: str, max_length: int = 500) -> str:
        """Gera um resumo do texto"""
        prompt = f"Resuma o seguinte texto em no máximo {max_length} caracteres, mantendo os pontos principais:\n\n{text[:5000]}"
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            logging.error(f"Erro ao resumir texto: {str(e)}")
            return "Erro ao gerar resumo"
    
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extrai entidades nomeadas do texto"""
        prompt = f"""
        Extraia as seguintes entidades do texto:
        - Pessoas
        - Organizações
        - Locais
        - Datas
        - Valores monetários
        - Percentagens
        
        Texto:
        {text[:5000]}
        
        Formate a resposta como JSON com as categorias acima.
        """
        
        try:
            response = self.model.generate_content(prompt)
            return self._parse_json_response(response.text)
        except Exception as e:
            logging.error(f"Erro ao extrair entidades: {str(e)}")
            return {"error": str(e)}
    
    def generate_questions(self, text: str, num_questions: int = 5) -> List[str]:
        """Gera perguntas sobre o conteúdo do texto"""
        prompt = f"""
        Gere {num_questions} perguntas relevantes sobre o seguinte texto.
        As perguntas devem testar a compreensão do conteúdo e cobrir os principais pontos.
        
        Texto:
        {text[:5000]}
        
        Formate cada pergunta em uma linha separada.
        """
        
        try:
            response = self.model.generate_content(prompt)
            questions = [q.strip() for q in response.text.split('\n') if q.strip()]
            return questions[:num_questions]
        except Exception as e:
            logging.error(f"Erro ao gerar perguntas: {str(e)}")
            return []
    
    def classify_document(self, text: str, categories: List[str]) -> Dict[str, float]:
        """Classifica o documento em categorias predefinidas"""
        prompt = f"""
        Classifique o seguinte documento nas categorias abaixo.
        Forneça uma pontuação de 0 a 1 para cada categoria indicando o quão bem o documento se encaixa.
        
        Categorias: {', '.join(categories)}
        
        Documento:
        {text[:5000]}
        
        Formate a resposta como JSON com cada categoria e sua pontuação.
        """
        
        try:
            response = self.model.generate_content(prompt)
            return self._parse_json_response(response.text)
        except Exception as e:
            logging.error(f"Erro ao classificar documento: {str(e)}")
            return {"error": str(e)}
    
    def extract_action_items(self, text: str) -> List[Dict[str, str]]:
        """Extrai itens de ação do texto"""
        prompt = f"""
        Identifique todos os itens de ação ou tarefas mencionadas no texto.
        Para cada item, forneça:
        - Descrição da ação
        - Responsável (se mencionado)
        - Prazo (se mencionado)
        - Prioridade (alta, média, baixa)
        
        Texto:
        {text[:5000]}
        
        Formate a resposta como JSON com uma lista de itens de ação.
        """
        
        try:
            response = self.model.generate_content(prompt)
            result = self._parse_json_response(response.text)
            return result.get('action_items', []) if isinstance(result, dict) else []
        except Exception as e:
            logging.error(f"Erro ao extrair itens de ação: {str(e)}")
            return []
    
    def translate_text(self, text: str, target_language: str = "en") -> str:
        """Traduz texto para o idioma especificado"""
        prompt = f"Traduza o seguinte texto para {target_language}:\n\n{text[:5000]}"
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            logging.error(f"Erro ao traduzir texto: {str(e)}")
            return "Erro na tradução"
    
    def check_grammar(self, text: str) -> Dict[str, Any]:
        """Verifica gramática e sugere correções"""
        prompt = f"""
        Verifique a gramática do seguinte texto e forneça:
        1. Lista de erros encontrados
        2. Sugestões de correção
        3. Texto corrigido
        
        Texto:
        {text[:5000]}
        
        Formate a resposta como JSON.
        """
        
        try:
            response = self.model.generate_content(prompt)
            return self._parse_json_response(response.text)
        except Exception as e:
            logging.error(f"Erro ao verificar gramática: {str(e)}")
            return {"error": str(e)}
    
    def generate_title(self, text: str) -> str:
        """Gera um título apropriado para o texto"""
        prompt = f"Gere um título conciso e descritivo para o seguinte texto:\n\n{text[:5000]}"
        
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            logging.error(f"Erro ao gerar título: {str(e)}")
            return "Documento sem título"
    
    def compare_documents(self, doc1: str, doc2: str) -> Dict[str, Any]:
        """Compara dois documentos e identifica similaridades e diferenças"""
        prompt = f"""
        Compare os dois documentos abaixo e forneça:
        1. Similaridades principais
        2. Diferenças principais
        3. Pontuação de similaridade (0-100)
        4. Tópicos únicos em cada documento
        
        Documento 1:
        {doc1[:2500]}
        
        Documento 2:
        {doc2[:2500]}
        
        Formate a resposta como JSON.
        """
        
        try:
            response = self.model.generate_content(prompt)
            return self._parse_json_response(response.text)
        except Exception as e:
            logging.error(f"Erro ao comparar documentos: {str(e)}")
            return {"error": str(e)}
    
    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """Parse de resposta JSON da IA"""
        try:
            # Tenta encontrar JSON no texto
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx != -1 and end_idx != 0:
                json_str = response_text[start_idx:end_idx]
                return json.loads(json_str)
            else:
                # Se não encontrar JSON, tenta criar uma estrutura básica
                return {"raw_response": response_text}
        except json.JSONDecodeError:
            logging.error("Erro ao decodificar JSON da resposta da IA")
            return {"raw_response": response_text}
        except Exception as e:
            logging.error(f"Erro ao processar resposta da IA: {str(e)}")
            return {"error": str(e)}
    
    def batch_process(self, texts: List[str], operation: str, **kwargs) -> List[Dict[str, Any]]:
        """Processa múltiplos textos em lote"""
        results = []
        
        for i, text in enumerate(texts):
            try:
                if operation == "summarize":
                    result = {"id": i, "summary": self.summarize_text(text, **kwargs)}
                elif operation == "analyze":
                    result = {"id": i, "analysis": self.analyze_document(text)}
                elif operation == "extract_entities":
                    result = {"id": i, "entities": self.extract_entities(text)}
                elif operation == "classify":
                    result = {"id": i, "classification": self.classify_document(text, **kwargs)}
                else:
                    result = {"id": i, "error": f"Operação desconhecida: {operation}"}
                
                results.append(result)
            except Exception as e:
                results.append({"id": i, "error": str(e)})
        
        return results