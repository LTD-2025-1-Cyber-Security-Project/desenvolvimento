#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Serviço de envio de emails.
Este módulo implementa o serviço de envio de emails utilizando Flask-Mail.
"""

from flask import current_app, render_template
from flask_mail import Message
from app import mail
import logging

logger = logging.getLogger(__name__)

class EmailService:
    """Classe de serviço para envio de emails."""
    
    @staticmethod
    def send_email(to, subject, template, **kwargs):
        """
        Envia um email usando um template HTML.
        
        Args:
            to: Destinatário ou lista de destinatários
            subject: Assunto do email
            template: Nome do arquivo de template (sem a extensão)
            **kwargs: Variáveis para o template
            
        Returns:
            True se enviado com sucesso, False em caso de erro
        """
        try:
            # Cria o objeto Message
            msg = Message(
                subject=subject,
                recipients=[to] if isinstance(to, str) else to,
                sender=current_app.config.get('MAIL_DEFAULT_SENDER')
            )
            
            # Renderiza o template HTML
            msg.html = render_template(f'emails/{template}.html', **kwargs)
            
            # Renderiza a versão texto (opcional)
            try:
                msg.body = render_template(f'emails/{template}.txt', **kwargs)
            except:
                # Se não encontrar o template de texto, cria uma versão simplificada
                msg.body = "Por favor, visualize este email em um cliente que suporte HTML."
            
            # Envia o email
            mail.send(msg)
            logger.info(f"Email enviado para {to}: {subject}")
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao enviar email para {to}: {str(e)}")
            return False
    
    @staticmethod
    def send_welcome_email(user):
        """
        Envia email de boas-vindas para novos usuários.
        
        Args:
            user: Objeto do modelo User
            
        Returns:
            True se enviado com sucesso, False em caso de erro
        """
        return EmailService.send_email(
            to=user.email,
            subject=f"Bem-vindo(a) à plataforma EdTech IA & Cyber",
            template="welcome",
            user=user
        )
    
    @staticmethod
    def send_password_reset_email(user, token):
        """
        Envia email com link para redefinição de senha.
        
        Args:
            user: Objeto do modelo User
            token: Token de redefinição
            
        Returns:
            True se enviado com sucesso, False em caso de erro
        """
        reset_url = current_app.config.get('BASE_URL', '') + f"/auth/reset-password/{token}"
        
        return EmailService.send_email(
            to=user.email,
            subject="Redefinição de Senha - EdTech IA & Cyber",
            template="password_reset",
            user=user,
            reset_url=reset_url,
            expiry_hours=24
        )
    
    @staticmethod
    def send_course_completion_email(user, course, certificate):
        """
        Envia email de conclusão de curso com certificado.
        
        Args:
            user: Objeto do modelo User
            course: Objeto do modelo Course
            certificate: Objeto do modelo Certificate
            
        Returns:
            True se enviado com sucesso, False em caso de erro
        """
        certificate_url = current_app.config.get('BASE_URL', '') + f"/certificate/{certificate.id}"
        
        return EmailService.send_email(
            to=user.email,
            subject=f"Parabéns pela conclusão do curso: {course.title}",
            template="course_completion",
            user=user,
            course=course,
            certificate=certificate,
            certificate_url=certificate_url
        )
    
    @staticmethod
    def send_course_enrollment_email(user, course):
        """
        Envia email de confirmação de matrícula em curso.
        
        Args:
            user: Objeto do modelo User
            course: Objeto do modelo Course
            
        Returns:
            True se enviado com sucesso, False em caso de erro
        """
        course_url = current_app.config.get('BASE_URL', '') + f"/course/{course.slug}"
        
        return EmailService.send_email(
            to=user.email,
            subject=f"Confirmação de matrícula: {course.title}",
            template="course_enrollment",
            user=user,
            course=course,
            course_url=course_url
        )
    
    @staticmethod
    def send_inactivity_reminder(user, days_inactive):
        """
        Envia email lembrando o usuário de continuar seus estudos após inatividade.
        
        Args:
            user: Objeto do modelo User
            days_inactive: Número de dias de inatividade
            
        Returns:
            True se enviado com sucesso, False em caso de erro
        """
        dashboard_url = current_app.config.get('BASE_URL', '') + "/dashboard"
        
        # Obtém cursos em progresso
        courses_in_progress = []
        for course in user.courses:
            progress = user.get_course_progress(course.id)
            if 0 < progress < 100:
                courses_in_progress.append({
                    'title': course.title,
                    'progress': progress,
                    'url': current_app.config.get('BASE_URL', '') + f"/course/{course.slug}"
                })
        
        return EmailService.send_email(
            to=user.email,
            subject="Sentimos sua falta! Continue seus estudos",
            template="inactivity_reminder",
            user=user,
            days_inactive=days_inactive,
            dashboard_url=dashboard_url,
            courses_in_progress=courses_in_progress[:3]  # Limita a 3 cursos
        )
    
    @staticmethod
    def send_new_course_notification(users, course):
        """
        Envia notificação sobre novo curso para vários usuários.
        
        Args:
            users: Lista de objetos User
            course: Objeto do modelo Course
            
        Returns:
            Número de emails enviados com sucesso
        """
        course_url = current_app.config.get('BASE_URL', '') + f"/course/{course.slug}"
        
        success_count = 0
        for user in users:
            success = EmailService.send_email(
                to=user.email,
                subject=f"Novo curso disponível: {course.title}",
                template="new_course",
                user=user,
                course=course,
                course_url=course_url
            )
            
            if success:
                success_count += 1
        
        return success_count
    
    @staticmethod
    def send_bulk_email(users, subject, content, template="generic"):
        """
        Envia um email em massa para vários usuários.
        
        Args:
            users: Lista de objetos User
            subject: Assunto do email
            content: Conteúdo do email
            template: Nome do template (padrão: "generic")
            
        Returns:
            Número de emails enviados com sucesso
        """
        success_count = 0
        
        for user in users:
            success = EmailService.send_email(
                to=user.email,
                subject=subject,
                template=template,
                user=user,
                content=content
            )
            
            if success:
                success_count += 1
        
        return success_count