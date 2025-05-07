#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Modelo de cursos e módulos educacionais.
Este módulo define os modelos de dados para cursos, módulos e conteúdos educacionais.
"""

from app import db
from datetime import datetime
from sqlalchemy import event
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.sql import func
from slugify import slugify

class Course(db.Model):
    """Modelo de curso educacional."""
    
    __tablename__ = 'courses'
    
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(200), unique=True)
    
    # Informações básicas
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    short_description = db.Column(db.String(255))
    category = db.Column(db.String(50), nullable=False)  # IA ou Cybersegurança
    level = db.Column(db.String(20), nullable=False)  # Básico, Intermediário, Avançado
    duration_hours = db.Column(db.Integer)  # Duração estimada em horas
    thumbnail = db.Column(db.String(255))
    
    # Metadados
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    is_published = db.Column(db.Boolean, default=False)
    is_featured = db.Column(db.Boolean, default=False)
    tags = db.Column(db.JSON)
    prerequisite_courses = db.Column(db.JSON)  # Lista de IDs de cursos pré-requisitos
    
    # Campos de rastreamento
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    modules = db.relationship('Module', backref='course', lazy='dynamic', cascade='all, delete-orphan')
    created_by = db.relationship('User', foreign_keys=[created_by_id], backref='created_courses')
    
    @hybrid_property
    def module_count(self):
        """Retorna o número de módulos no curso."""
        return self.modules.count()
    
    @hybrid_property
    def enrollment_count(self):
        """Retorna o número de usuários matriculados."""
        return self.enrolled_users.count()
    
    def to_dict(self):
        """Converte o objeto para um dicionário."""
        return {
            'id': self.id,
            'slug': self.slug,
            'title': self.title,
            'description': self.description,
            'short_description': self.short_description,
            'category': self.category,
            'level': self.level,
            'duration_hours': self.duration_hours,
            'thumbnail': self.thumbnail,
            'created_by_id': self.created_by_id,
            'is_published': self.is_published,
            'is_featured': self.is_featured,
            'tags': self.tags,
            'prerequisite_courses': self.prerequisite_courses,
            'module_count': self.module_count,
            'enrollment_count': self.enrollment_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        """Representação em string do objeto."""
        return f'<Course {self.title}>'


class Module(db.Model):
    """Modelo de módulo de curso."""
    
    __tablename__ = 'modules'
    
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(200))
    
    # Informações básicas
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    order = db.Column(db.Integer, nullable=False)  # Ordem do módulo no curso
    
    # Relação com o curso
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    
    # Campos de rastreamento
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    lessons = db.relationship('Lesson', backref='module', lazy='dynamic', cascade='all, delete-orphan')
    
    # Índices
    __table_args__ = (
        db.UniqueConstraint('course_id', 'order', name='_course_module_order_uc'),
        db.UniqueConstraint('course_id', 'slug', name='_course_module_slug_uc'),
    )
    
    @hybrid_property
    def lesson_count(self):
        """Retorna o número de lições no módulo."""
        return self.lessons.count()

    def to_dict(self):
        """Converte o objeto para um dicionário."""
        return {
            'id': self.id,
            'slug': self.slug,
            'title': self.title,
            'description': self.description,
            'order': self.order,
            'course_id': self.course_id,
            'lesson_count': self.lesson_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        """Representação em string do objeto."""
        return f'<Module {self.title}>'


class Lesson(db.Model):
    """Modelo de lição dentro de um módulo."""
    
    __tablename__ = 'lessons'
    
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(200))
    
    # Informações básicas
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    order = db.Column(db.Integer, nullable=False)  # Ordem da lição no módulo
    duration_minutes = db.Column(db.Integer)  # Duração estimada em minutos
    
    # Tipo de lição
    lesson_type = db.Column(db.String(20), default='text')  # text, video, interactive
    
    # Metadados
    video_url = db.Column(db.String(255))  # URL do vídeo se for lição tipo vídeo
    attachment_url = db.Column(db.String(255))  # URL de material complementar
    xp_reward = db.Column(db.Integer, default=50)  # Recompensa de XP por concluir a lição
    
    # Relação com o módulo
    module_id = db.Column(db.Integer, db.ForeignKey('modules.id'), nullable=False)
    
    # Campos de rastreamento
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    quizzes = db.relationship('Quiz', backref='lesson', lazy='dynamic', cascade='all, delete-orphan')
    
    # Índices
    __table_args__ = (
        db.UniqueConstraint('module_id', 'order', name='_module_lesson_order_uc'),
        db.UniqueConstraint('module_id', 'slug', name='_module_lesson_slug_uc'),
    )
    
    def has_quiz(self):
        """Verifica se a lição possui quiz."""
        return self.quizzes.count() > 0
    
    def to_dict(self):
        """Converte o objeto para um dicionário."""
        return {
            'id': self.id,
            'slug': self.slug,
            'title': self.title,
            'content': self.content,
            'order': self.order,
            'duration_minutes': self.duration_minutes,
            'lesson_type': self.lesson_type,
            'video_url': self.video_url,
            'attachment_url': self.attachment_url,
            'xp_reward': self.xp_reward,
            'module_id': self.module_id,
            'has_quiz': self.has_quiz(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        """Representação em string do objeto."""
        return f'<Lesson {self.title}>'


# Triggers para gerar slugs automaticamente
@event.listens_for(Course.title, 'set')
def set_course_slug(target, value, oldvalue, initiator):
    """Gera o slug quando o título do curso é definido ou alterado."""
    if value and (not target.slug or value != oldvalue):
        target.slug = slugify(value)


@event.listens_for(Module.title, 'set')
def set_module_slug(target, value, oldvalue, initiator):
    """Gera o slug quando o título do módulo é definido ou alterado."""
    if value and (not target.slug or value != oldvalue):
        target.slug = slugify(value)


@event.listens_for(Lesson.title, 'set')
def set_lesson_slug(target, value, oldvalue, initiator):
    """Gera o slug quando o título da lição é definido ou alterado."""
    if value and (not target.slug or value != oldvalue):
        target.slug = slugify(value)