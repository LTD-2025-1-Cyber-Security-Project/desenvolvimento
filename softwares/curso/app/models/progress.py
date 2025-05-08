#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Modelo de progresso e atividades educacionais dos usuários.
Este módulo define o modelo de dados para rastrear o progresso dos usuários nos cursos.
"""

from app import db
from datetime import datetime

class Progress(db.Model):
    """Modelo para rastreamento do progresso dos usuários nos cursos."""
    
    __tablename__ = 'progress'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Relações
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    module_id = db.Column(db.Integer, db.ForeignKey('modules.id'), nullable=False)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lessons.id'), nullable=False)
    
    # Status de conclusão
    status = db.Column(db.String(20), default='not_started')  # not_started, in_progress, completed
    progress_percentage = db.Column(db.Float, default=0.0)  # Porcentagem de conclusão (0-100)
    
    # Metadados
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)
    completion_date = db.Column(db.DateTime)
    time_spent_seconds = db.Column(db.Integer, default=0)  # Tempo gasto em segundos
    notes = db.Column(db.Text)  # Notas do usuário para esta lição
    
    # Campos de rastreamento
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    module = db.relationship('Module', backref='progress_records')
    lesson = db.relationship('Lesson', backref='progress_records')
    course = db.relationship('Course', backref='progress_records')
    
    # Índices
    __table_args__ = (
        db.Index('idx_progress_user_course', 'user_id', 'course_id'),
        db.Index('idx_progress_user_lesson', 'user_id', 'lesson_id'),
        db.UniqueConstraint('user_id', 'lesson_id', name='_user_lesson_progress_uc'),
    )
    
    def complete(self):
        """Marca a lição como concluída."""
        self.status = 'completed'
        self.progress_percentage = 100.0
        self.completion_date = datetime.utcnow()
        
        # Adiciona recompensa de XP ao usuário
        from app.models.user import User
        user = User.query.get(self.user_id)
        if user and self.lesson:
            user.add_xp(self.lesson.xp_reward)
            db.session.commit()
    
    def mark_in_progress(self, percentage=None):
        """Marca a lição como em progresso."""
        self.status = 'in_progress'
        if percentage is not None:
            self.progress_percentage = min(max(0.0, percentage), 99.9)
        self.last_activity = datetime.utcnow()
    
    def add_time_spent(self, seconds):
        """Adiciona tempo gasto na lição."""
        if seconds > 0:
            self.time_spent_seconds += seconds
            self.last_activity = datetime.utcnow()
    
    def to_dict(self):
        """Converte o objeto para um dicionário."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'course_id': self.course_id,
            'module_id': self.module_id,
            'lesson_id': self.lesson_id,
            'status': self.status,
            'progress_percentage': self.progress_percentage,
            'last_activity': self.last_activity.isoformat() if self.last_activity else None,
            'completion_date': self.completion_date.isoformat() if self.completion_date else None,
            'time_spent_seconds': self.time_spent_seconds,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        """Representação em string do objeto."""
        return f'<Progress {self.id} - User {self.user_id} - Lesson {self.lesson_id}>'


class UserActivity(db.Model):
    """Modelo para rastreamento das atividades gerais dos usuários no sistema."""
    
    __tablename__ = 'user_activities'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Relações
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Detalhes da atividade
    activity_type = db.Column(db.String(50), nullable=False)  # login, course_start, lesson_complete, quiz_complete, etc.
    description = db.Column(db.String(255))
    activity_data = db.Column(db.JSON)  # Metadados adicionais sobre a atividade - RENOMEADO DE 'metadata'
    
    # Campos de rastreamento
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(255))
    
    # Índices
    __table_args__ = (
        db.Index('idx_user_activities_user_type', 'user_id', 'activity_type'),
        db.Index('idx_user_activities_timestamp', 'timestamp'),
    )
    
    @classmethod
    def log_activity(cls, user_id, activity_type, description=None, metadata=None, ip_address=None, user_agent=None):
        """Registra uma nova atividade para um usuário."""
        activity = cls(
            user_id=user_id,
            activity_type=activity_type,
            description=description,
            activity_data=metadata,  # Usando o campo renomeado
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.session.add(activity)
        db.session.commit()
        return activity
    
    def to_dict(self):
        """Converte o objeto para um dicionário."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'activity_type': self.activity_type,
            'description': self.description,
            'metadata': self.activity_data,  # Mantém o nome original na saída do dicionário
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent
        }
    
    def __repr__(self):
        """Representação em string do objeto."""
        return f'<UserActivity {self.id} - User {self.user_id} - {self.activity_type}>'


class Certificate(db.Model):
    """Modelo para certificados obtidos por usuários após concluírem cursos."""
    
    __tablename__ = 'certificates'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Relações
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    
    # Detalhes do certificado
    certificate_number = db.Column(db.String(50), unique=True, nullable=False)
    issue_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    expiry_date = db.Column(db.DateTime)  # NULL para certificados que não expiram
    status = db.Column(db.String(20), default='valid')  # valid, expired, revoked
    
    # Metadados
    pdf_url = db.Column(db.String(255))  # URL para o PDF do certificado
    revocation_reason = db.Column(db.Text)  # Razão para revogação, se houver
    
    # Campos de rastreamento
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    user = db.relationship('User', backref='certificates')
    course = db.relationship('Course', backref='certificates')
    
    # Índices
    __table_args__ = (
        db.Index('idx_certificates_user', 'user_id'),
        db.UniqueConstraint('user_id', 'course_id', name='_user_course_certificate_uc'),
    )
    
    def is_valid(self):
        """Verifica se o certificado é válido atualmente."""
        if self.status != 'valid':
            return False
            
        if self.expiry_date and self.expiry_date < datetime.utcnow():
            self.status = 'expired'
            db.session.commit()
            return False
            
        return True
        
    def revoke(self, reason=None):
        """Revoga o certificado."""
        self.status = 'revoked'
        self.revocation_reason = reason
        db.session.commit()
    
    def to_dict(self):
        """Converte o objeto para um dicionário."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'course_id': self.course_id,
            'certificate_number': self.certificate_number,
            'issue_date': self.issue_date.isoformat() if self.issue_date else None,
            'expiry_date': self.expiry_date.isoformat() if self.expiry_date else None,
            'status': self.status,
            'pdf_url': self.pdf_url,
            'revocation_reason': self.revocation_reason,
            'is_valid': self.is_valid(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        """Representação em string do objeto."""
        return f'<Certificate {self.certificate_number}>'