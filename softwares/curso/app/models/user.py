#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Modelo de usuário.
Este módulo define o modelo de dados para usuários do sistema.
"""

from app import db, bcrypt
from flask_login import UserMixin
from datetime import datetime
import uuid

class UserRoles:
    """Enum para os níveis de acesso dos usuários."""
    ADMIN = 'admin'
    INSTRUCTOR = 'instructor'
    STUDENT = 'student'
    
    ALL_ROLES = [ADMIN, INSTRUCTOR, STUDENT]


# Tabela de associação entre usuário e cursos
user_courses = db.Table('user_courses',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('course_id', db.Integer, db.ForeignKey('courses.id'), primary_key=True),
    db.Column('enrolled_date', db.DateTime, default=datetime.utcnow)
)


class User(db.Model, UserMixin):
    """Modelo de usuário do sistema."""
    
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, default=lambda: str(uuid.uuid4()))
    
    # Campos de autenticação
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), default=UserRoles.STUDENT)
    is_active = db.Column(db.Boolean, default=True)
    
    # Campos de perfil
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    profile_pic = db.Column(db.String(255))
    bio = db.Column(db.Text)
    
    # Campos profissionais
    department = db.Column(db.String(100))
    job_title = db.Column(db.String(100))
    municipality = db.Column(db.String(50))  # Florianópolis ou São José
    
    # Campos de gamificação
    xp_points = db.Column(db.Integer, default=0)
    level = db.Column(db.Integer, default=1)
    badges = db.Column(db.JSON, default=list)
    
    # Campos de rastreamento
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    courses = db.relationship('Course', secondary=user_courses, 
                            backref=db.backref('enrolled_users', lazy='dynamic'))
    progress_records = db.relationship('Progress', backref='user', lazy='dynamic')
    quiz_attempts = db.relationship('QuizAttempt', backref='user', lazy='dynamic')
    
    # Token para redefinição de senha
    reset_token = db.Column(db.String(100), unique=True)
    reset_token_expiry = db.Column(db.DateTime)
    
    def __init__(self, **kwargs):
        """Inicializa uma nova instância de usuário."""
        super(User, self).__init__(**kwargs)
        if 'password' in kwargs:
            self.set_password(kwargs['password'])
    
    def set_password(self, password):
        """Define a senha do usuário, convertendo-a para hash."""
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    
    def check_password(self, password):
        """Verifica se a senha informada corresponde ao hash armazenado."""
        return bcrypt.check_password_hash(self.password_hash, password)
    
    def get_full_name(self):
        """Retorna o nome completo do usuário."""
        return f"{self.first_name} {self.last_name}"
    
    def add_xp(self, points):
        """Adiciona pontos de experiência e atualiza o nível se necessário."""
        self.xp_points += points
        
        # Calcula o novo nível com base nos pontos
        new_level = 1 + (self.xp_points // 1000)
        
        # Se o nível aumentou, atualiza e retorna True
        if new_level > self.level:
            self.level = new_level
            return True
        
        return False
    
    def add_badge(self, badge_id, badge_name, badge_description):
        """Adiciona uma nova medalha ao usuário."""
        if self.badges is None:
            self.badges = []
            
        badge = {
            'id': badge_id,
            'name': badge_name,
            'description': badge_description,
            'earned_at': datetime.utcnow().isoformat()
        }
        
        self.badges.append(badge)
    
    def get_course_progress(self, course_id):
        """Calcula a porcentagem de progresso em um curso específico."""
        from app.models.progress import Progress
        
        # Obtém todos os módulos do curso
        from app.models.course import Module
        modules = Module.query.filter_by(course_id=course_id).all()
        
        if not modules:
            return 0
            
        # Conta os módulos concluídos
        completed_modules = Progress.query.filter_by(
            user_id=self.id,
            course_id=course_id,
            status='completed'
        ).count()
        
        # Calcula a porcentagem de progresso
        progress_percentage = (completed_modules / len(modules)) * 100
        return round(progress_percentage, 1)
    
    def is_admin(self):
        """Verifica se o usuário é um administrador."""
        return self.role == UserRoles.ADMIN
        
    def is_instructor(self):
        """Verifica se o usuário é um instrutor."""
        return self.role == UserRoles.INSTRUCTOR or self.role == UserRoles.ADMIN
    
    def to_dict(self):
        """Converte o objeto para um dicionário."""
        return {
            'id': self.id,
            'uuid': self.uuid,
            'email': self.email,
            'role': self.role,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.get_full_name(),
            'profile_pic': self.profile_pic,
            'bio': self.bio,
            'department': self.department,
            'job_title': self.job_title,
            'municipality': self.municipality,
            'xp_points': self.xp_points,
            'level': self.level,
            'badges': self.badges,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }
    
    def __repr__(self):
        """Representação em string do objeto."""
        return f'<User {self.email}>'