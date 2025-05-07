#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Modelo de quizzes e questões.
Este módulo define os modelos de dados para quizzes, questões e tentativas.
"""

from app import db
from datetime import datetime
import json
import uuid

class Quiz(db.Model):
    """Modelo de quiz para avaliação de conhecimento."""
    
    __tablename__ = 'quizzes'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    time_limit_minutes = db.Column(db.Integer)  # Limite de tempo em minutos, None para sem limite
    passing_score = db.Column(db.Integer, default=70)  # Porcentagem mínima para passar
    
    # Tipo de quiz
    quiz_type = db.Column(db.String(20), default='standard')  # standard, certification, dynamic
    difficulty = db.Column(db.String(20), default='medium')  # easy, medium, hard
    shuffle_questions = db.Column(db.Boolean, default=True)
    
    # Metadados
    is_published = db.Column(db.Boolean, default=False)
    xp_reward = db.Column(db.Integer, default=100)  # Recompensa de XP por concluir o quiz
    max_attempts = db.Column(db.Integer, default=3)  # Máximo de tentativas, None para ilimitado
    show_answers = db.Column(db.Boolean, default=True)  # Mostrar respostas corretas após tentativa
    
    # Relações
    lesson_id = db.Column(db.Integer, db.ForeignKey('lessons.id'))
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Campos de rastreamento
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    questions = db.relationship('Question', backref='quiz', lazy='dynamic', cascade='all, delete-orphan')
    attempts = db.relationship('QuizAttempt', backref='quiz', lazy='dynamic')
    created_by = db.relationship('User', backref='created_quizzes')
    
    def get_question_count(self):
        """Retorna o número de questões no quiz."""
        return self.questions.count()
    
    def get_average_score(self):
        """Calcula a pontuação média de todas as tentativas."""
        attempts = self.attempts.with_entities(db.func.avg(QuizAttempt.score)).scalar()
        return round(attempts or 0, 2)
    
    def get_completion_rate(self):
        """Calcula a taxa de conclusão do quiz (porcentagem de estudantes que passaram)."""
        total_attempts = self.attempts.count()
        if total_attempts == 0:
            return 0
            
        successful_attempts = self.attempts.filter(QuizAttempt.score >= self.passing_score).count()
        return round((successful_attempts / total_attempts) * 100, 2)
    
    def to_dict(self):
        """Converte o objeto para um dicionário."""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'time_limit_minutes': self.time_limit_minutes,
            'passing_score': self.passing_score,
            'quiz_type': self.quiz_type,
            'difficulty': self.difficulty,
            'shuffle_questions': self.shuffle_questions,
            'is_published': self.is_published,
            'xp_reward': self.xp_reward,
            'max_attempts': self.max_attempts,
            'show_answers': self.show_answers,
            'lesson_id': self.lesson_id,
            'created_by_id': self.created_by_id,
            'question_count': self.get_question_count(),
            'average_score': self.get_average_score(),
            'completion_rate': self.get_completion_rate(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        """Representação em string do objeto."""
        return f'<Quiz {self.title}>'


class Question(db.Model):
    """Modelo de questão para quizzes."""
    
    __tablename__ = 'questions'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Conteúdo da questão
    text = db.Column(db.Text, nullable=False)
    explanation = db.Column(db.Text)  # Explicação da resposta correta
    
    # Tipo de questão
    question_type = db.Column(db.String(20), default='multiple_choice')  # multiple_choice, true_false, fill_blank, matching
    difficulty = db.Column(db.String(20), default='medium')  # easy, medium, hard
    
    # Opções e resposta correta
    options = db.Column(db.JSON)  # Lista de opções
    correct_answer = db.Column(db.String(255))  # Valor da resposta correta
    
    # Metadados
    points = db.Column(db.Integer, default=10)  # Pontos atribuídos à questão
    tags = db.Column(db.JSON)  # Tags para categorização
    
    # Relações
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False)
    
    # Campos de rastreamento
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def validate_answer(self, user_answer):
        """Valida uma resposta de usuário e retorna se está correta."""
        if self.question_type == 'multiple_choice':
            return user_answer == self.correct_answer
        elif self.question_type == 'true_false':
            return user_answer.lower() == self.correct_answer.lower()
        elif self.question_type == 'fill_blank':
            # Para questões de preenchimento, ignora maiúsculas/minúsculas e espaços
            return user_answer.lower().strip() == self.correct_answer.lower().strip()
        elif self.question_type == 'matching':
            # Para questões de correspondência, compara as respostas com um formato específico
            try:
                user_matches = json.loads(user_answer) if isinstance(user_answer, str) else user_answer
                correct_matches = json.loads(self.correct_answer) if isinstance(self.correct_answer, str) else self.correct_answer
                return user_matches == correct_matches
            except (json.JSONDecodeError, TypeError):
                return False
        
        return False
    
    def to_dict(self):
        """Converte o objeto para um dicionário."""
        return {
            'id': self.id,
            'text': self.text,
            'explanation': self.explanation,
            'question_type': self.question_type,
            'difficulty': self.difficulty,
            'options': self.options,
            'points': self.points,
            'tags': self.tags,
            'quiz_id': self.quiz_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        """Representação em string do objeto."""
        return f'<Question {self.id}>'


class QuizAttempt(db.Model):
    """Modelo de tentativa de quiz por um usuário."""
    
    __tablename__ = 'quiz_attempts'
    
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, default=lambda: str(uuid.uuid4()))
    
    # Relações
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False)
    
    # Resultados
    score = db.Column(db.Float)  # Pontuação em porcentagem
    passed = db.Column(db.Boolean)  # Se passou no quiz ou não
    answers = db.Column(db.JSON)  # Respostas do usuário
    
    # Campos de rastreamento
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    # Índices
    __table_args__ = (
        db.Index('idx_quiz_attempts_user_quiz', 'user_id', 'quiz_id'),
    )
    
    def calculate_score(self):
        """Calcula a pontuação da tentativa com base nas respostas."""
        if not self.answers:
            self.score = 0.0
            self.passed = False
            return
        
        # Obtém as questões do quiz
        questions = Question.query.filter_by(quiz_id=self.quiz_id).all()
        question_map = {q.id: q for q in questions}
        
        # Se não houver questões, a pontuação é zero
        if not questions:
            self.score = 0.0
            self.passed = False
            return
        
        # Contador para questões corretas
        correct_count = 0
        total_points = sum(q.points for q in questions)
        earned_points = 0
        
        # Verifica cada resposta
        for answer in self.answers:
            question_id = answer.get('question_id')
            user_answer = answer.get('answer')
            
            # Obtém a questão correspondente
            question = question_map.get(question_id)
            if question and question.validate_answer(user_answer):
                correct_count += 1
                earned_points += question.points
                answer['is_correct'] = True
            else:
                answer['is_correct'] = False
        
        # Calcula a pontuação em porcentagem
        self.score = (earned_points / total_points * 100) if total_points > 0 else 0
        self.score = round(self.score, 2)
        
        # Determina se passou com base na pontuação mínima para aprovação
        quiz = Quiz.query.get(self.quiz_id)
        if quiz:
            self.passed = self.score >= quiz.passing_score
        else:
            self.passed = False
        
        # Atualiza o campo answers com as informações de correção
        db.session.commit()
    
    def get_duration(self):
        """Retorna a duração da tentativa em minutos."""
        if not self.completed_at:
            return None
            
        duration = self.completed_at - self.started_at
        return round(duration.total_seconds() / 60, 2)
    
    def to_dict(self):
        """Converte o objeto para um dicionário."""
        return {
            'id': self.id,
            'uuid': self.uuid,
            'user_id': self.user_id,
            'quiz_id': self.quiz_id,
            'score': self.score,
            'passed': self.passed,
            'answers': self.answers,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'duration_minutes': self.get_duration()
        }
    
    def __repr__(self):
        """Representação em string do objeto."""
        return f'<QuizAttempt {self.id}>'