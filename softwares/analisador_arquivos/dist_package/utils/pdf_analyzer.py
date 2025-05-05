import os
from typing import Dict, Any, List
from PyPDF2 import PdfReader
import google.generativeai as genai
from flask import current_app
import re
from collections import Counter
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
import logging

# Configuração básica do NLTK
try:
    import ssl
    try:
        _create_unverified_https_context = ssl._create_unverified_context
    except AttributeError:
        pass
    else:
        ssl._create_default_https_context = _create_unverified_https_context
    
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
except:
    import logging
    logging.warning("Não foi possível baixar dados do NLTK. Funcionalidades de processamento de texto podem ser limitadas.")

class PDFAnalyzer:
    """Analisador de PDF com IA para extrair insights e informações"""
    
    def __init__(self):
        self.api_key = current_app.config.get('GOOGLE_AI_API_KEY')
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-pro')
        
        # Configuração de stopwords
        try:
            self.stop_words = set(stopwords.words('portuguese') + stopwords.words('english'))
        except:
            self.stop_words = set()
            logging.warning("Stopwords do NLTK não disponíveis. Usando conjunto vazio.")
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extrai texto de um arquivo PDF"""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            return text.strip()
        except Exception as e:
            logging.error(f"Erro ao extrair texto do PDF: {str(e)}")
            return ""
    
    def analyze_with_ai(self, text: str) -> Dict[str, Any]:
        """Analisa o texto usando Google Gemini"""
        try:
            prompt = f"""
            Analise o seguinte texto e forneça:
            1. Um resumo executivo (máximo 200 palavras)
            2. Os 5 pontos-chave principais
            3. Análise de sentimento (positivo, neutro, negativo) com pontuação de 0-100
            4. Os 3 tópicos principais abordados
            5. 10 palavras-chave mais relevantes
            6. Uma conclusão breve (máximo 100 palavras)

            Formato da resposta:
            RESUMO: [resumo]
            PONTOS-CHAVE: [lista numerada]
            SENTIMENTO: [classificação] - [pontuação]
            TÓPICOS: [lista]
            PALAVRAS-CHAVE: [lista]
            CONCLUSÃO: [conclusão]

            Texto para análise:
            {text[:4000]}  # Limita o texto para não exceder o limite da API
            """
            
            response = self.model.generate_content(prompt)
            analysis = self.parse_ai_response(response.text)
            
            return analysis
        except Exception as e:
            logging.error(f"Erro na análise com IA: {str(e)}")
            return self.fallback_analysis(text)
    
    def parse_ai_response(self, response_text: str) -> Dict[str, Any]:
        """Parse da resposta da IA para estruturar os dados"""
        analysis = {
            "resumo": "",
            "pontos_chave": [],
            "sentimento": {"classificacao": "neutro", "pontuacao": 50},
            "topicos": [],
            "palavras_chave": [],
            "conclusao": ""
        }
        
        try:
            sections = response_text.split('\n')
            current_section = None
            
            for line in sections:
                line = line.strip()
                
                if line.startswith("RESUMO:"):
                    current_section = "resumo"
                    analysis["resumo"] = line.replace("RESUMO:", "").strip()
                elif line.startswith("PONTOS-CHAVE:"):
                    current_section = "pontos_chave"
                elif line.startswith("SENTIMENTO:"):
                    current_section = "sentimento"
                    sentiment_text = line.replace("SENTIMENTO:", "").strip()
                    if "-" in sentiment_text:
                        parts = sentiment_text.split("-")
                        analysis["sentimento"]["classificacao"] = parts[0].strip().lower()
                        try:
                            analysis["sentimento"]["pontuacao"] = int(parts[1].strip())
                        except:
                            analysis["sentimento"]["pontuacao"] = 50
                elif line.startswith("TÓPICOS:"):
                    current_section = "topicos"
                    topics = line.replace("TÓPICOS:", "").strip()
                    analysis["topicos"] = [t.strip() for t in topics.split(",")]
                elif line.startswith("PALAVRAS-CHAVE:"):
                    current_section = "palavras_chave"
                    keywords = line.replace("PALAVRAS-CHAVE:", "").strip()
                    analysis["palavras_chave"] = [k.strip() for k in keywords.split(",")]
                elif line.startswith("CONCLUSÃO:"):
                    current_section = "conclusao"
                    analysis["conclusao"] = line.replace("CONCLUSÃO:", "").strip()
                elif line and current_section:
                    if current_section == "pontos_chave" and re.match(r'^\d+\.', line):
                        analysis["pontos_chave"].append(re.sub(r'^\d+\.\s*', '', line))
                    elif current_section in ["resumo", "conclusao"]:
                        analysis[current_section] += " " + line
        except Exception as e:
            logging.error(f"Erro ao parsear resposta da IA: {str(e)}")
        
        return analysis
    
    def fallback_analysis(self, text: str) -> Dict[str, Any]:
        """Análise fallback quando a IA falha"""
        try:
            # Tokenização básica
            words = text.lower().split()
            sentences = text.split('.')
            
            # Remove stopwords se disponíveis
            if self.stop_words:
                filtered_words = [w for w in words if w.isalpha() and w not in self.stop_words]
            else:
                filtered_words = [w for w in words if w.isalpha()]
            
            # Análise de frequência
            word_freq = Counter(filtered_words)
            most_common = word_freq.most_common(10)
            
            # Análise básica
            analysis = {
                "resumo": " ".join(sentences[:3]) if sentences else "Texto vazio ou não processável.",
                "pontos_chave": sentences[:5] if sentences else ["Não foi possível extrair pontos-chave"],
                "sentimento": {
                    "classificacao": "neutro",
                    "pontuacao": 50
                },
                "topicos": ["Análise automática não disponível"],
                "palavras_chave": [word for word, _ in most_common],
                "conclusao": "Análise baseada em frequência de palavras. Para uma análise mais profunda, verifique a conexão com a API."
            }
            
            return analysis
        except Exception as e:
            logging.error(f"Erro na análise fallback: {str(e)}")
            return {
                "resumo": "Erro ao processar o documento",
                "pontos_chave": ["Erro no processamento"],
                "sentimento": {"classificacao": "erro", "pontuacao": 0},
                "topicos": ["Erro"],
                "palavras_chave": [],
                "conclusao": "Não foi possível analisar o documento"
            }
    
    def extract_metadata(self, pdf_path: str) -> Dict[str, Any]:
        """Extrai metadados do PDF"""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PdfReader(file)
                metadata = {
                    "num_pages": len(pdf_reader.pages),
                    "info": pdf_reader.metadata,
                    "is_encrypted": pdf_reader.is_encrypted
                }
                
                # Converte metadados para formato serializável
                if metadata["info"]:
                    info_dict = {}
                    for key, value in metadata["info"].items():
                        key = key.replace('/', '')
                        info_dict[key] = str(value) if value else None
                    metadata["info"] = info_dict
                
                return metadata
        except Exception as e:
            logging.error(f"Erro ao extrair metadados: {str(e)}")
            return {"error": str(e)}
    
    def generate_summary(self, text: str, max_length: int = 500) -> str:
        """Gera um resumo do texto usando a IA"""
        try:
            prompt = f"Faça um resumo conciso do seguinte texto em no máximo {max_length} caracteres:\n\n{text[:4000]}"
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            # Fallback para resumo simples
            words = text.split()
            summary = " ".join(words[:max_length // 5])  # Aproximadamente max_length caracteres
            return summary + "..." if len(words) > max_length // 5 else summary
    
    def extract_keywords(self, text: str, num_keywords: int = 10) -> List[str]:
        """Extrai palavras-chave do texto"""
        try:
            prompt = f"Extraia as {num_keywords} palavras-chave mais importantes do seguinte texto:\n\n{text[:4000]}"
            response = self.model.generate_content(prompt)
            keywords = response.text.split(',')
            return [kw.strip() for kw in keywords][:num_keywords]
        except Exception as e:
            # Fallback para extração simples
            words = text.lower().split()
            
            # Remove stopwords se disponíveis
            if self.stop_words:
                filtered_words = [w for w in words if w.isalpha() and w not in self.stop_words]
            else:
                filtered_words = [w for w in words if w.isalpha()]
            
            word_freq = Counter(filtered_words)
            return [word for word, _ in word_freq.most_common(num_keywords)]
    
    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analisa o sentimento do texto"""
        try:
            prompt = f"""
            Analise o sentimento do seguinte texto e forneça:
            1. Classificação (positivo, neutro, negativo)
            2. Pontuação de 0-100
            3. Principais emoções detectadas
            
            Texto: {text[:4000]}
            
            Formato da resposta:
            CLASSIFICAÇÃO: [classificação]
            PONTUAÇÃO: [pontuação]
            EMOÇÕES: [lista de emoções]
            """
            
            response = self.model.generate_content(prompt)
            result = {"classificacao": "neutro", "pontuacao": 50, "emocoes": []}
            
            lines = response.text.split('\n')
            for line in lines:
                if line.startswith("CLASSIFICAÇÃO:"):
                    result["classificacao"] = line.replace("CLASSIFICAÇÃO:", "").strip().lower()
                elif line.startswith("PONTUAÇÃO:"):
                    try:
                        result["pontuacao"] = int(line.replace("PONTUAÇÃO:", "").strip())
                    except:
                        result["pontuacao"] = 50
                elif line.startswith("EMOÇÕES:"):
                    emotions = line.replace("EMOÇÕES:", "").strip()
                    result["emocoes"] = [e.strip() for e in emotions.split(",")]
            
            return result
        except Exception as e:
            logging.error(f"Erro na análise de sentimento: {str(e)}")
            return {"classificacao": "neutro", "pontuacao": 50, "emocoes": ["erro"]}
    
    def extract_topics(self, text: str, num_topics: int = 5) -> List[str]:
        """Extrai os principais tópicos do texto"""
        try:
            prompt = f"Identifique os {num_topics} principais tópicos abordados no seguinte texto:\n\n{text[:4000]}"
            response = self.model.generate_content(prompt)
            topics = response.text.split(',')
            return [topic.strip() for topic in topics][:num_topics]
        except Exception as e:
            logging.error(f"Erro na extração de tópicos: {str(e)}")
            return ["Erro na análise de tópicos"]
    
    def full_analysis(self, pdf_path: str) -> Dict[str, Any]:
        """Realiza uma análise completa do PDF"""
        try:
            # Extrai texto e metadados
            text = self.extract_text_from_pdf(pdf_path)
            metadata = self.extract_metadata(pdf_path)
            
            if not text:
                return {
                    "error": "Não foi possível extrair texto do PDF",
                    "metadata": metadata
                }
            
            # Realiza análise com IA
            ai_analysis = self.analyze_with_ai(text)
            
            # Combina todos os resultados
            result = {
                "metadata": metadata,
                "analysis": ai_analysis,
                "status": "success"
            }
            
            return result
        except Exception as e:
            logging.error(f"Erro na análise completa: {str(e)}")
            return {
                "error": str(e),
                "status": "error"
            }
    
    def extract_tables(self, pdf_path: str) -> List[Dict[str, Any]]:
        """Tenta extrair tabelas do PDF"""
        try:
            # Esta é uma implementação básica
            # Para extração avançada de tabelas, considere usar bibliotecas como tabula-py
            tables = []
            with open(pdf_path, 'rb') as file:
                pdf_reader = PdfReader(file)
                for i, page in enumerate(pdf_reader.pages):
                    text = page.extract_text()
                    # Procura por padrões que parecem tabelas
                    lines = text.split('\n')
                    potential_table = []
                    
                    for line in lines:
                        # Se a linha tem múltiplos espaços ou tabs, pode ser uma linha de tabela
                        if re.search(r'\s{2,}|\t', line):
                            cells = re.split(r'\s{2,}|\t', line)
                            if len(cells) > 1:
                                potential_table.append(cells)
                    
                    if potential_table:
                        tables.append({
                            "page": i + 1,
                            "data": potential_table
                        })
            
            return tables
        except Exception as e:
            logging.error(f"Erro ao extrair tabelas: {str(e)}")
            return []
    
    def extract_images_info(self, pdf_path: str) -> List[Dict[str, Any]]:
        """Extrai informações sobre imagens no PDF"""
        try:
            images_info = []
            with open(pdf_path, 'rb') as file:
                pdf_reader = PdfReader(file)
                for i, page in enumerate(pdf_reader.pages):
                    if '/XObject' in page['/Resources']:
                        xObject = page['/Resources']['/XObject'].get_object()
                        for obj in xObject:
                            if xObject[obj]['/Subtype'] == '/Image':
                                images_info.append({
                                    "page": i + 1,
                                    "name": obj,
                                    "width": xObject[obj]['/Width'],
                                    "height": xObject[obj]['/Height']
                                })
            
            return images_info
        except Exception as e:
            logging.error(f"Erro ao extrair informações de imagens: {str(e)}")
            return []