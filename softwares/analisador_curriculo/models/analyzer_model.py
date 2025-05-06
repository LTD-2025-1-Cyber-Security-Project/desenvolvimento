import re
import nltk
from nltk.tokenize import word_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

class ResumeAnalyzerModel:
    """
    Modelo alternativo de análise de currículos usando NLTK e scikit-learn
    em vez de spaCy.
    """
    
    def __init__(self):
        # Garantir que os recursos do NLTK estejam disponíveis
        nltk.download('punkt', quiet=True)
        nltk.download('stopwords', quiet=True)
        
        # Carregar stopwords
        from nltk.corpus import stopwords
        try:
            self.stop_words = set(stopwords.words('portuguese') + stopwords.words('english'))
        except:
            self.stop_words = set()
            print("Aviso: Não foi possível carregar as stopwords. A análise pode ser menos precisa.")
        
        # Dicionários de termos por área (expandido para mais áreas)
        self.tech_terms = self._load_tech_terms()
    
    def _load_tech_terms(self):
        """Carrega termos técnicos por área"""
        return {
            'desenvolvimento web': [
                'html', 'css', 'javascript', 'react', 'angular', 'vue', 'node', 'express',
                'django', 'flask', 'php', 'laravel', 'frontend', 'backend', 'fullstack',
                'rest', 'api', 'json', 'xml', 'http', 'responsive', 'web', 'site'
            ],
            'ciência de dados': [
                'python', 'r', 'sql', 'pandas', 'numpy', 'scikit-learn', 'tensorflow',
                'pytorch', 'keras', 'machine learning', 'ia', 'inteligência artificial',
                'estatística', 'análise', 'modelagem', 'predição', 'classificação',
                'regressão', 'clustering', 'big data', 'hadoop', 'spark'
            ],
            'devops': [
                'docker', 'kubernetes', 'aws', 'azure', 'gcp', 'linux', 'unix', 'devops',
                'ci/cd', 'jenkins', 'gitlab', 'github', 'terraform', 'ansible', 'chef',
                'puppet', 'monitoring', 'logging', 'segurança', 'cloud', 'infraestrutura'
            ],
            'mobile': [
                'android', 'ios', 'swift', 'kotlin', 'react native', 'flutter', 'xamarin',
                'mobile', 'app', 'aplicativo', 'firebase', 'push', 'notification',
                'geolocation', 'offline', 'armazenamento', 'ui/ux mobile'
            ],
            'gestão': [
                'gestão', 'gerenciamento', 'liderança', 'scrum', 'agile', 'kanban',
                'projetos', 'equipe', 'time', 'stakeholder', 'orçamento', 'estratégia',
                'planejamento', 'kpi', 'indicadores', 'performance'
            ]
        }
    
    def _tokenize_text(self, text):
        """Tokeniza o texto em palavras"""
        if not text:
            return []
        
        # Tokenização simples de palavras
        try:
            tokens = word_tokenize(text.lower())
            # Remover pontuação e stopwords
            tokens = [word for word in tokens if word.isalnum() and word not in self.stop_words]
            return tokens
        except Exception as e:
            print(f"Erro na tokenização: {e}")
            # Fallback mais simples
            return [w.lower() for w in re.findall(r'\b\w+\b', text)]
    
    def analyze(self, resume_text, area):
        """
        Analisa o texto do currículo para a área específica.
        
        Args:
            resume_text (str): Texto do currículo
            area (str): Área de interesse
            
        Returns:
            dict: Resultado da análise
        """
        if not resume_text:
            return {
                "score": 0,
                "recommendation": "Não foi possível analisar o currículo, texto vazio."
            }
        
        # Processar texto com tokenização
        tokens = self._tokenize_text(resume_text)
        
        # Calcular relevância para a área especificada
        area_terms = self.tech_terms.get(area.lower(), [])
        if not area_terms:
            # Se a área não foi encontrada, usar todos os termos
            area_terms = [term for terms in self.tech_terms.values() for term in terms]
        
        # Calcular pontuação de correspondência de termos
        total_terms = len(area_terms)
        matched_terms = 0
        
        for term in area_terms:
            # Verificar se o termo (ou similar) está presente no texto
            if any(term.lower() == token or term.lower() in token for token in tokens):
                matched_terms += 1
        
        # Calcular pontuação de 0 a 100
        if total_terms > 0:
            term_score = (matched_terms / total_terms) * 100
        else:
            term_score = 0
        
        # Análise de estrutura (parágrafos, seções)
        paragraphs = len(re.split(r'\n\s*\n', resume_text))
        structure_score = min(100, max(0, (paragraphs / 5) * 100))
        
        # Análise de comprimento (nem muito curto, nem muito longo)
        words = len(tokens)
        length_score = 0
        if words < 100:
            length_score = words  # Muito curto
        elif words < 500:
            length_score = 100  # Tamanho ideal
        else:
            length_score = max(0, 100 - ((words - 500) / 10))  # Desconta se for muito longo
        
        # Pontuação final (média ponderada)
        final_score = int((term_score * 0.5) + (structure_score * 0.3) + (length_score * 0.2))
        
        # Gerar recomendações
        recommendations = self._generate_recommendations(
            resume_text, tokens, area, matched_terms, area_terms, paragraphs, words
        )
        
        return {
            "score": final_score,
            "term_relevance": int(term_score),
            "structure_quality": int(structure_score),
            "length_quality": int(length_score),
            "matched_terms": matched_terms,
            "total_area_terms": total_terms,
            "recommendations": recommendations
        }
    
    def _generate_recommendations(self, text, tokens, area, matched_terms, area_terms, paragraphs, words):
        """Gera recomendações específicas baseadas na análise"""
        recommendations = []
        
        # Recomendar termos faltantes importantes
        if matched_terms < len(area_terms) * 0.7:
            missing_important_terms = [term for term in area_terms[:10] 
                                     if not any(term.lower() == token or term.lower() in token 
                                               for token in tokens)]
            if missing_important_terms:
                recommendations.append(f"Considere adicionar termos relevantes para {area}: {', '.join(missing_important_terms[:5])}")
        
        # Recomendar melhorias na estrutura
        if paragraphs < 3:
            recommendations.append("Divida o currículo em mais seções para melhorar a legibilidade e organização.")
        
        # Recomendar ajustes no comprimento
        if words < 100:
            recommendations.append("O currículo está muito curto. Adicione mais detalhes sobre suas experiências e habilidades.")
        elif words > 700:
            recommendations.append("O currículo está muito longo. Considere focar nas experiências mais relevantes.")
        
        # Verificar presença de realizações/conquistas
        achievements_terms = ['concluí', 'implementei', 'criei', 'desenvolvi', 'liderei', 'aumentei', 'reduzi', 'melhorei']
        has_achievements = any(achievement in text.lower() for achievement in achievements_terms)
        if not has_achievements:
            recommendations.append("Adicione realizações quantificáveis para destacar seu impacto nas posições anteriores.")
        
        # Limitar número de recomendações
        return recommendations[:5]