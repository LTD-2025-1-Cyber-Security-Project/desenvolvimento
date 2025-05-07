#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Controlador de quizzes.
Este módulo gerencia as rotas relacionadas aos quizzes, questões e tentativas,
incluindo a geração dinâmica de perguntas via IA.
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, abort
from flask_login import login_required, current_user
from app import db
from app.models.user import User
from app.models.course import Course, Module, Lesson
from app.models.quiz import Quiz, Question, QuizAttempt
from app.models.progress import UserActivity, Progress
from app.services.ai_service import GeminiService
from sqlalchemy import func
from datetime import datetime
import random
import json

# Criação do Blueprint de quizzes
quizzes_bp = Blueprint('quizzes', __name__, url_prefix='/quizzes')

# Instanciação dos serviços
gemini_service = GeminiService()


@quizzes_bp.route('/view/<int:quiz_id>')
@login_required
def quiz_view(quiz_id):
    """Rota para visualizar um quiz."""
    # Obtém o quiz
    quiz = Quiz.query.get_or_404(quiz_id)
    
    # Obtém a lição e verifica se o usuário pode acessar
    lesson = Lesson.query.get_or_404(quiz.lesson_id)
    module = Module.query.get_or_404(lesson.module_id)
    course = Course.query.get_or_404(module.course_id)
    
    # Verifica se o usuário está matriculado no curso
    if course not in current_user.courses and not current_user.is_instructor():
        flash('Você precisa estar matriculado neste curso para acessar os quizzes.', 'warning')
        return redirect(url_for('courses.course_detail', slug=course.slug))
    
    # Obtém as tentativas anteriores do usuário
    previous_attempts = QuizAttempt.query.filter_by(
        user_id=current_user.id,
        quiz_id=quiz.id
    ).order_by(QuizAttempt.completed_at.desc()).all()
    
    # Verifica se o usuário esgotou o número máximo de tentativas
    if quiz.max_attempts and len(previous_attempts) >= quiz.max_attempts:
        flash('Você já utilizou o número máximo de tentativas para este quiz.', 'warning')
        return redirect(url_for('courses.lesson_view', lesson_id=lesson.id))
    
    # Registra a atividade de visualização do quiz
    UserActivity.log_activity(
        user_id=current_user.id,
        activity_type='quiz_view',
        description=f'Visualização do quiz: {quiz.title}',
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string,
        metadata={
            'quiz_id': quiz.id,
            'lesson_id': lesson.id,
            'course_id': course.id
        }
    )
    
    return render_template('quizzes/quiz_view.html',
                          quiz=quiz,
                          lesson=lesson,
                          module=module,
                          course=course,
                          previous_attempts=previous_attempts)


@quizzes_bp.route('/start/<int:quiz_id>', methods=['POST'])
@login_required
def start_quiz(quiz_id):
    """Rota para iniciar um quiz."""
    # Obtém o quiz
    quiz = Quiz.query.get_or_404(quiz_id)
    
    # Obtém a lição e verifica se o usuário pode acessar
    lesson = Lesson.query.get_or_404(quiz.lesson_id)
    module = Module.query.get_or_404(lesson.module_id)
    course = Course.query.get_or_404(module.course_id)
    
    # Verifica se o usuário está matriculado no curso
    if course not in current_user.courses and not current_user.is_instructor():
        flash('Você precisa estar matriculado neste curso para fazer os quizzes.', 'warning')
        return redirect(url_for('courses.course_detail', slug=course.slug))
    
    # Obtém as tentativas anteriores do usuário
    previous_attempts = QuizAttempt.query.filter_by(
        user_id=current_user.id,
        quiz_id=quiz.id
    ).count()
    
    # Verifica se o usuário esgotou o número máximo de tentativas
    if quiz.max_attempts and previous_attempts >= quiz.max_attempts:
        flash('Você já utilizou o número máximo de tentativas para este quiz.', 'warning')
        return redirect(url_for('courses.lesson_view', lesson_id=lesson.id))
    
    # Cria uma nova tentativa
    attempt = QuizAttempt(
        user_id=current_user.id,
        quiz_id=quiz.id,
        started_at=datetime.utcnow()
    )
    db.session.add(attempt)
    db.session.commit()
    
    # Registra a atividade de início do quiz
    UserActivity.log_activity(
        user_id=current_user.id,
        activity_type='quiz_start',
        description=f'Início do quiz: {quiz.title}',
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string,
        metadata={
            'quiz_id': quiz.id,
            'attempt_id': attempt.id,
            'lesson_id': lesson.id,
            'course_id': course.id
        }
    )
    
    return redirect(url_for('quizzes.take_quiz', attempt_id=attempt.id))


@quizzes_bp.route('/take/<int:attempt_id>')
@login_required
def take_quiz(attempt_id):
    """Rota para realizar um quiz."""
    # Obtém a tentativa
    attempt = QuizAttempt.query.get_or_404(attempt_id)
    
    # Verifica se a tentativa pertence ao usuário
    if attempt.user_id != current_user.id:
        abort(403)
    
    # Verifica se a tentativa já foi concluída
    if attempt.completed_at:
        flash('Esta tentativa já foi concluída.', 'warning')
        return redirect(url_for('quizzes.quiz_result', attempt_id=attempt.id))
    
    # Obtém o quiz
    quiz = Quiz.query.get_or_404(attempt.quiz_id)
    
    # Obtém as questões do quiz
    questions = Question.query.filter_by(quiz_id=quiz.id).all()
    
    # Se o quiz for dinâmico, pode gerar questões via IA
    if quiz.quiz_type == 'dynamic' and not questions:
        try:
            # Obtém o contexto para gerar questões
            lesson = Lesson.query.get_or_404(quiz.lesson_id)
            
            # Gera questões com a IA
            generated_questions = gemini_service.generate_quiz_questions(
                lesson.title,
                lesson.content,
                difficulty=quiz.difficulty,
                count=5
            )
            
            # Salva as questões geradas
            questions = []
            for q_data in generated_questions:
                question = Question(
                    quiz_id=quiz.id,
                    text=q_data.get('question'),
                    explanation=q_data.get('explanation'),
                    question_type=q_data.get('type', 'multiple_choice'),
                    options=q_data.get('options'),
                    correct_answer=q_data.get('correct_answer'),
                    difficulty=quiz.difficulty
                )
                db.session.add(question)
                questions.append(question)
            
            db.session.commit()
        except Exception as e:
            flash(f'Erro ao gerar questões: {str(e)}', 'danger')
            return redirect(url_for('courses.lesson_view', lesson_id=quiz.lesson_id))
    
    # Se o quiz não tiver questões, redireciona
    if not questions:
        flash('Este quiz não possui questões cadastradas.', 'warning')
        return redirect(url_for('courses.lesson_view', lesson_id=quiz.lesson_id))
    
    # Embaralha as questões se necessário
    if quiz.shuffle_questions:
        random.shuffle(questions)
    
    # Obtém informações sobre a lição e curso
    lesson = Lesson.query.get_or_404(quiz.lesson_id)
    module = Module.query.get_or_404(lesson.module_id)
    course = Course.query.get_or_404(module.course_id)
    
    return render_template('quizzes/take_quiz.html',
                          attempt=attempt,
                          quiz=quiz,
                          questions=questions,
                          lesson=lesson,
                          module=module,
                          course=course)


@quizzes_bp.route('/submit/<int:attempt_id>', methods=['POST'])
@login_required
def submit_quiz(attempt_id):
    """Rota para submeter as respostas de um quiz."""
    # Obtém a tentativa
    attempt = QuizAttempt.query.get_or_404(attempt_id)
    
    # Verifica se a tentativa pertence ao usuário
    if attempt.user_id != current_user.id:
        abort(403)
    
    # Verifica se a tentativa já foi concluída
    if attempt.completed_at:
        flash('Esta tentativa já foi concluída.', 'warning')
        return redirect(url_for('quizzes.quiz_result', attempt_id=attempt.id))
    
    # Obtém o quiz
    quiz = Quiz.query.get_or_404(attempt.quiz_id)
    
    # Obtém todas as questões do quiz
    questions = Question.query.filter_by(quiz_id=quiz.id).all()
    question_map = {q.id: q for q in questions}
    
    # Processa as respostas
    answers = []
    for key, value in request.form.items():
        if key.startswith('question_'):
            question_id = int(key.split('_')[1])
            if question_id in question_map:
                answers.append({
                    'question_id': question_id,
                    'answer': value,
                    'question_text': question_map[question_id].text
                })
    
    attempt.answers = answers
    
    # Marca o horário de conclusão
    attempt.completed_at = datetime.utcnow()
    
    # Calcula a pontuação
    attempt.calculate_score()
    
    # Atualiza o progresso na lição se o usuário passou no quiz
    if attempt.passed:
        lesson = Lesson.query.get_or_404(quiz.lesson_id)
        progress = Progress.query.filter_by(
            user_id=current_user.id,
            lesson_id=lesson.id
        ).first()
        
        if progress:
            progress.complete()
            
        # Adiciona XP ao usuário
        if quiz.xp_reward:
            current_user.add_xp(quiz.xp_reward)
            
        db.session.commit()
    
    # Registra a atividade de conclusão do quiz
    UserActivity.log_activity(
        user_id=current_user.id,
        activity_type='quiz_complete',
        description=f'Quiz concluído: {quiz.title}',
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string,
        metadata={
            'quiz_id': quiz.id,
            'attempt_id': attempt.id,
            'score': attempt.score,
            'passed': attempt.passed,
            'xp_reward': quiz.xp_reward if attempt.passed else 0
        }
    )
    
    return redirect(url_for('quizzes.quiz_result', attempt_id=attempt.id))


@quizzes_bp.route('/result/<int:attempt_id>')
@login_required
def quiz_result(attempt_id):
    """Rota para visualizar o resultado de uma tentativa de quiz."""
    # Obtém a tentativa
    attempt = QuizAttempt.query.get_or_404(attempt_id)
    
    # Verifica se a tentativa pertence ao usuário ou se é admin/instrutor
    if attempt.user_id != current_user.id and not current_user.is_instructor():
        abort(403)
    
    # Verifica se a tentativa foi concluída
    if not attempt.completed_at:
        flash('Esta tentativa ainda não foi concluída.', 'warning')
        return redirect(url_for('quizzes.take_quiz', attempt_id=attempt.id))
    
    # Obtém o quiz e as questões
    quiz = Quiz.query.get_or_404(attempt.quiz_id)
    questions = Question.query.filter_by(quiz_id=quiz.id).all()
    question_map = {q.id: q for q in questions}
    
    # Obtém informações sobre a lição e curso
    lesson = Lesson.query.get_or_404(quiz.lesson_id)
    module = Module.query.get_or_404(lesson.module_id)
    course = Course.query.get_or_404(module.course_id)
    
    # Prepara os dados das respostas para exibição
    answer_data = []
    for answer in attempt.answers:
        question_id = answer.get('question_id')
        question = question_map.get(question_id)
        if question:
            answer_data.append({
                'question': question,
                'user_answer': answer.get('answer'),
                'is_correct': answer.get('is_correct', False),
                'correct_answer': question.correct_answer
            })
    
    return render_template('quizzes/quiz_result.html',
                          attempt=attempt,
                          quiz=quiz,
                          answer_data=answer_data,
                          lesson=lesson,
                          module=module,
                          course=course,
                          show_answers=quiz.show_answers)


@quizzes_bp.route('/generate/<int:lesson_id>')
@login_required
def generate_quiz(lesson_id):
    """Rota para gerar um quiz dinamicamente para uma lição."""
    # Verifica se o usuário é instrutor
    if not current_user.is_instructor():
        abort(403)
    
    # Obtém a lição
    lesson = Lesson.query.get_or_404(lesson_id)
    
    # Obtém o módulo e o curso
    module = Module.query.get_or_404(lesson.module_id)
    course = Course.query.get_or_404(module.course_id)
    
    # Verifica se a lição já possui quiz
    existing_quiz = Quiz.query.filter_by(lesson_id=lesson.id).first()
    if existing_quiz:
        flash('Esta lição já possui um quiz associado.', 'warning')
        return redirect(url_for('courses.lesson_view', lesson_id=lesson.id))
    
    try:
        # Gera um quiz com a IA
        quiz_data = gemini_service.generate_quiz(
            lesson.title,
            lesson.content,
            difficulty='medium',
            question_count=5
        )
        
        # Cria o quiz
        quiz = Quiz(
            title=f"Quiz - {lesson.title}",
            description=quiz_data.get('description', f"Teste seus conhecimentos sobre {lesson.title}"),
            quiz_type='dynamic',
            difficulty='medium',
            lesson_id=lesson.id,
            created_by_id=current_user.id,
            is_published=True
        )
        db.session.add(quiz)
        db.session.flush()  # Para obter o ID do quiz
        
        # Adiciona as questões
        for q_data in quiz_data.get('questions', []):
            question = Question(
                quiz_id=quiz.id,
                text=q_data.get('question'),
                explanation=q_data.get('explanation'),
                question_type=q_data.get('type', 'multiple_choice'),
                options=q_data.get('options'),
                correct_answer=q_data.get('correct_answer'),
                difficulty='medium'
            )
            db.session.add(question)
        
        db.session.commit()
        
        flash('Quiz gerado com sucesso!', 'success')
        return redirect(url_for('quizzes.quiz_view', quiz_id=quiz.id))
        
    except Exception as e:
        flash(f'Erro ao gerar o quiz: {str(e)}', 'danger')
        return redirect(url_for('courses.lesson_view', lesson_id=lesson.id))


@quizzes_bp.route('/api/analyze-performance/<int:course_id>')
@login_required
def analyze_performance(course_id):
    """API para analisar o desempenho do usuário em quizzes de um curso específico."""
    # Obtém o curso
    course = Course.query.get_or_404(course_id)
    
    # Verifica se o usuário está matriculado no curso
    if course not in current_user.courses and not current_user.is_instructor():
        return jsonify({'error': 'Acesso não autorizado'}), 403
    
    # Coleta dados de todas as tentativas do usuário em quizzes deste curso
    data = []
    
    # Obtém todos os quizzes relacionados ao curso
    quiz_ids = db.session.query(Quiz.id).join(
        Lesson, Quiz.lesson_id == Lesson.id
    ).join(
        Module, Lesson.module_id == Module.id
    ).filter(
        Module.course_id == course.id
    ).all()
    quiz_ids = [q[0] for q in quiz_ids]
    
    # Obtém todas as tentativas do usuário para esses quizzes
    attempts = QuizAttempt.query.filter(
        QuizAttempt.user_id == current_user.id,
        QuizAttempt.quiz_id.in_(quiz_ids),
        QuizAttempt.completed_at != None
    ).all()
    
    for attempt in attempts:
        quiz = Quiz.query.get(attempt.quiz_id)
        lesson = Lesson.query.get(quiz.lesson_id)
        module = Module.query.get(lesson.module_id)
        
        # Análise de acertos por tipo de questão
        question_type_stats = {}
        for answer in attempt.answers:
            question_id = answer.get('question_id')
            question = Question.query.get(question_id)
            if question:
                q_type = question.question_type
                is_correct = answer.get('is_correct', False)
                
                if q_type not in question_type_stats:
                    question_type_stats[q_type] = {'total': 0, 'correct': 0}
                
                question_type_stats[q_type]['total'] += 1
                if is_correct:
                    question_type_stats[q_type]['correct'] += 1
        
        # Calcula porcentagens
        for q_type in question_type_stats:
            stats = question_type_stats[q_type]
            stats['percentage'] = round((stats['correct'] / stats['total']) * 100, 1) if stats['total'] > 0 else 0
        
        data.append({
            'attempt_id': attempt.id,
            'quiz_title': quiz.title,
            'module_title': module.title,
            'score': attempt.score,
            'passed': attempt.passed,
            'date': attempt.completed_at.strftime('%d/%m/%Y %H:%M'),
            'question_type_stats': question_type_stats,
            'duration_minutes': attempt.get_duration()
        })
    
    # Análise das áreas fortes e fracas
    strengths = []
    weaknesses = []
    
    # Calcula média de pontuação por módulo
    module_scores = {}
    for module in course.modules:
        module_quiz_ids = db.session.query(Quiz.id).join(
            Lesson, Quiz.lesson_id == Lesson.id
        ).filter(
            Lesson.module_id == module.id
        ).all()
        module_quiz_ids = [q[0] for q in module_quiz_ids]
        
        module_attempts = [a for a in attempts if a.quiz_id in module_quiz_ids]
        if module_attempts:
            avg_score = sum(a.score for a in module_attempts) / len(module_attempts)
            module_scores[module.id] = {
                'module_title': module.title,
                'avg_score': avg_score
            }
    
    # Identifica áreas fortes e fracas
    if module_scores:
        sorted_modules = sorted(module_scores.values(), key=lambda x: x['avg_score'], reverse=True)
        strengths = [m for m in sorted_modules if m['avg_score'] >= 70][:3]
        weaknesses = [m for m in sorted_modules if m['avg_score'] < 70][-3:]
    
    # Tenta obter recomendações personalizadas da IA
    recommendations = []
    try:
        if weaknesses:
            for weakness in weaknesses:
                module_title = weakness['module_title']
                module = Module.query.filter_by(title=module_title, course_id=course.id).first()
                if module:
                    # Obtém o conteúdo das lições do módulo
                    lessons_content = ""
                    for lesson in Lesson.query.filter_by(module_id=module.id).all():
                        lessons_content += f"{lesson.title}\n"
                    
                    # Gera recomendações baseadas no conteúdo
                    rec = gemini_service.generate_study_recommendations(
                        module_title,
                        lessons_content,
                        weakness['avg_score']
                    )
                    recommendations.append({
                        'module': module_title,
                        'score': weakness['avg_score'],
                        'tips': rec.get('tips', []),
                        'resources': rec.get('resources', [])
                    })
    except Exception as e:
        recommendations = [{
            'error': f"Não foi possível gerar recomendações personalizadas: {str(e)}"
        }]
    
    return jsonify({
        'attempt_history': data,
        'strengths': strengths,
        'weaknesses': weaknesses,
        'recommendations': recommendations
    })


@quizzes_bp.route('/api/get-dynamic-question/<int:lesson_id>', methods=['POST'])
@login_required
def get_dynamic_question(lesson_id):
    """API para obter uma questão gerada dinamicamente pela IA."""
    # Obtém a lição
    lesson = Lesson.query.get_or_404(lesson_id)
    
    # Verifica se o usuário pode acessar a lição
    module = Module.query.get_or_404(lesson.module_id)
    course = Course.query.get_or_404(module.course_id)
    
    if course not in current_user.courses and not current_user.is_instructor():
        return jsonify({'error': 'Acesso não autorizado'}), 403
    
    # Obtém parâmetros
    data = request.json
    difficulty = data.get('difficulty', 'medium')
    question_type = data.get('question_type', 'multiple_choice')
    
    try:
        # Gera uma questão com a IA
        question_data = gemini_service.generate_single_question(
            lesson.title,
            lesson.content,
            difficulty=difficulty,
            question_type=question_type
        )
        
        return jsonify(question_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500