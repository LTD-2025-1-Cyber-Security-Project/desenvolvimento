#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Implementação atualizada da função de matrícula e acesso a cursos.
Este arquivo contém correções para o controlador de cursos.
"""

from flask import redirect, url_for, flash
from flask_login import current_user, login_required
from app import db
from app.models.course import Course
from app.models.progress import UserActivity

@login_required
def enroll(course_id):
    """
    Função atualizada para matricular um usuário em um curso.
    
    Args:
        course_id: ID do curso
        
    Returns:
        Redirecionamento para a página de detalhes do curso ou primeira lição
    """
    # Obtém o curso
    course = Course.query.get_or_404(course_id)
    
    # Verifica se o curso está publicado
    if not course.is_published:
        flash('Este curso não está disponível para matrícula.', 'danger')
        return redirect(url_for('courses.course_list'))
    
    # Verifica se o usuário já está matriculado
    if course in current_user.courses:
        flash('Você já está matriculado neste curso. Iniciando o curso...', 'info')
        
        # Redirecionamento direto para a primeira lição
        first_module = course.modules.order_by(Module.order).first()
        if first_module:
            first_lesson = first_module.lessons.order_by(Lesson.order).first()
            if first_lesson:
                return redirect(url_for('courses.lesson_view', lesson_id=first_lesson.id))
                
        return redirect(url_for('courses.course_detail', slug=course.slug))
    
    # Verifica pré-requisitos do curso
    if course.prerequisite_courses:
        for prereq_id in course.prerequisite_courses:
            prereq_course = Course.query.get(prereq_id)
            if prereq_course and prereq_course not in current_user.courses:
                flash(f'Você precisa concluir o curso "{prereq_course.title}" antes de se matricular neste curso.', 'warning')
                return redirect(url_for('courses.course_detail', slug=course.slug))
    
    # Matricula o usuário
    current_user.courses.append(course)
    db.session.commit()
    
    # Registra a atividade de matrícula
    UserActivity.log_activity(
        user_id=current_user.id,
        activity_type='course_enrollment',
        description=f'Matrícula no curso: {course.title}',
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string,
        metadata={'course_id': course.id}
    )
    
    flash(f'Você foi matriculado com sucesso no curso: {course.title}', 'success')
    
    # Redireciona diretamente para a primeira lição
    first_module = course.modules.order_by(Module.order).first()
    if first_module:
        first_lesson = first_module.lessons.order_by(Lesson.order).first()
        if first_lesson:
            flash('Iniciando sua primeira lição!', 'info')
            return redirect(url_for('courses.lesson_view', lesson_id=first_lesson.id))
    
    return redirect(url_for('courses.course_detail', slug=course.slug))