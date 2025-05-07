#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Controlador de API.
Este módulo gerencia as rotas da API para integração e funcionalidades acessadas via AJAX.
"""

from flask import Blueprint, request, jsonify, current_app
from flask_login import current_user, login_required
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db, cache
from app.models.user import User, UserRoles
from app.models.course import Course, Module, Lesson
from app.models.quiz import Quiz, Question, QuizAttempt
from app.models.progress import Progress, UserActivity, Certificate
from app.services.ai_service import GeminiService
from app.services.youtube_service import YouTubeService
from sqlalchemy import func
from datetime import datetime, timedelta
import json

# Criação do Blueprint de API
api_bp = Blueprint('api', __name__)

# Instanciação dos serviços
gemini_service = GeminiService()
youtube_service = YouTubeService()


# ===== Rotas de usuário =====

@api_bp.route('/user/profile', methods=['GET'])
@jwt_required()
def get_user_profile():
    """API para obter perfil do usuário autenticado via JWT."""
    # Obtém o ID do usuário a partir do token JWT
    user_id = get_jwt_identity()
    
    # Obtém o usuário
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    
    # Retorna o perfil do usuário
    return jsonify(user.to_dict())


@api_bp.route('/user/progress', methods=['GET'])
@jwt_required()
def get_user_progress():
    """API para obter progresso do usuário em todos os cursos."""
    # Obtém o ID do usuário a partir do token JWT
    user_id = get_jwt_identity()
    
    # Obtém o usuário
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    
    # Obtém o progresso em cada curso
    progress_data = []
    for course in user.courses:
        progress = user.get_course_progress(course.id)
        
        # Verifica se o usuário tem certificado do curso
        certificate = Certificate.query.filter_by(
            user_id=user.id,
            course_id=course.id
        ).first()
        
        progress_data.append({
            'course_id': course.id,
            'course_title': course.title,
            'course_category': course.category,
            'progress_percentage': progress,
            'completed': progress == 100,
            'has_certificate': certificate is not None,
            'certificate_id': certificate.id if certificate else None,
            'certificate_date': certificate.issue_date.isoformat() if certificate else None
        })
    
    return jsonify(progress_data)


@api_bp.route('/user/activities', methods=['GET'])
@jwt_required()
def get_user_activities():
    """API para obter histórico de atividades do usuário."""
    # Obtém o ID do usuário a partir do token JWT
    user_id = get_jwt_identity()
    
    # Obtém o usuário
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    
    # Parâmetros de filtragem
    limit = request.args.get('limit', 20, type=int)
    activity_type = request.args.get('type')
    
    # Query base
    query = UserActivity.query.filter_by(user_id=user.id)
    
    # Filtro por tipo
    if activity_type:
        query = query.filter_by(activity_type=activity_type)
    
    # Executa a query
    activities = query.order_by(UserActivity.timestamp.desc()).limit(limit).all()
    
    # Prepara os dados para retorno
    activity_data = []
    for activity in activities:
        activity_data.append(activity.to_dict())
    
    return jsonify(activity_data)


# ===== Rotas de cursos =====

@api_bp.route('/courses', methods=['GET'])
def get_courses():
    """API para obter lista de cursos."""
    # Parâmetros de filtragem
    category = request.args.get('category')
    level = request.args.get('level')
    search = request.args.get('search')
    limit = request.args.get('limit', 10, type=int)
    
    # Query base - apenas cursos publicados
    query = Course.query.filter_by(is_published=True)
    
    # Aplicação de filtros
    if category:
        query = query.filter_by(category=category)
    if level:
        query = query.filter_by(level=level)
    if search:
        query = query.filter(
            Course.title.ilike(f'%{search}%') | 
            Course.description.ilike(f'%{search}%')
        )
    
    # Executa a query
    courses = query.limit(limit).all()
    
    # Prepara os dados para retorno
    course_data = []
    for course in courses:
        course_data.append(course.to_dict())
    
    return jsonify(course_data)


@api_bp.route('/course/<int:course_id>', methods=['GET'])
def get_course(course_id):
    """API para obter detalhes de um curso específico."""
    # Obtém o curso
    course = Course.query.get_or_404(course_id)
    
    # Verifica se o curso está publicado
    if not course.is_published:
        # Se o usuário estiver autenticado, verifica se é instrutor
        if current_user.is_authenticated and current_user.is_instructor():
            pass  # Permite acesso
        else:
            return jsonify({'error': 'Curso não encontrado ou não publicado'}), 404
    
    # Obtém os módulos do curso
    modules = Module.query.filter_by(course_id=course.id).order_by(Module.order).all()
    module_data = []
    
    for module in modules:
        # Obtém as lições do módulo
        lessons = Lesson.query.filter_by(module_id=module.id).order_by(Lesson.order).all()
        lesson_data = []
        
        for lesson in lessons:
            # Verifica se a lição tem quiz
            has_quiz = Quiz.query.filter_by(lesson_id=lesson.id).first() is not None
            
            lesson_data.append({
                'id': lesson.id,
                'title': lesson.title,
                'lesson_type': lesson.lesson_type,
                'duration_minutes': lesson.duration_minutes,
                'has_quiz': has_quiz
            })
        
        module_data.append({
            'id': module.id,
            'title': module.title,
            'description': module.description,
            'order': module.order,
            'lessons': lesson_data
        })
    
    # Adiciona dados do curso e módulos
    result = course.to_dict()
    result['modules'] = module_data
    
    return jsonify(result)


@api_bp.route('/course/<int:course_id>/enroll', methods=['POST'])
@jwt_required()
def enroll_course(course_id):
    """API para matricular o usuário em um curso."""
    # Obtém o ID do usuário a partir do token JWT
    user_id = get_jwt_identity()
    
    # Obtém o usuário
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    
    # Obtém o curso
    course = Course.query.get_or_404(course_id)
    
    # Verifica se o curso está publicado
    if not course.is_published:
        return jsonify({'error': 'Este curso não está disponível para matrícula'}), 400
    
    # Verifica se o usuário já está matriculado
    if course in user.courses:
        return jsonify({'message': 'Usuário já está matriculado neste curso'}), 400
    
    # Matricula o usuário
    user.courses.append(course)
    db.session.commit()
    
    # Registra a atividade
    UserActivity.log_activity(
        user_id=user.id,
        activity_type='course_enrollment',
        description=f'Matrícula no curso: {course.title}',
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string,
        metadata={'course_id': course.id}
    )
    
    return jsonify({'message': 'Matrícula realizada com sucesso'})


@api_bp.route('/lesson/<int:lesson_id>', methods=['GET'])
@jwt_required()
def get_lesson(lesson_id):
    """API para obter detalhes de uma lição específica."""
    # Obtém o ID do usuário a partir do token JWT
    user_id = get_jwt_identity()
    
    # Obtém o usuário
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    
    # Obtém a lição
    lesson = Lesson.query.get_or_404(lesson_id)
    
    # Obtém o módulo e o curso
    module = Module.query.get_or_404(lesson.module_id)
    course = Course.query.get_or_404(module.course_id)
    
    # Verifica se o usuário está matriculado no curso
    if course not in user.courses and not user.is_instructor():
        return jsonify({'error': 'Acesso não autorizado a esta lição'}), 403
    
    # Obtém as informações da lição
    lesson_data = lesson.to_dict()
    
    # Obtém informações de progresso, se existir
    progress = Progress.query.filter_by(
        user_id=user.id,
        lesson_id=lesson.id
    ).first()
    
    if progress:
        lesson_data['progress'] = progress.to_dict()
    else:
        # Cria um novo registro de progresso
        new_progress = Progress(
            user_id=user.id,
            course_id=course.id,
            module_id=module.id,
            lesson_id=lesson.id,
            status='not_started',
            progress_percentage=0.0
        )
        db.session.add(new_progress)
        db.session.commit()
        
        lesson_data['progress'] = new_progress.to_dict()
    
    # Obtém informações sobre o quiz, se existir
    quiz = Quiz.query.filter_by(lesson_id=lesson.id).first()
    if quiz:
        lesson_data['quiz'] = {
            'id': quiz.id,
            'title': quiz.title,
            'description': quiz.description,
            'question_count': quiz.get_question_count()
        }
    
    # Registra a atividade de visualização da lição
    UserActivity.log_activity(
        user_id=user.id,
        activity_type='lesson_view',
        description=f'Visualização da lição: {lesson.title}',
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string,
        metadata={
            'course_id': course.id,
            'module_id': module.id,
            'lesson_id': lesson.id
        }
    )
    
    return jsonify(lesson_data)


@api_bp.route('/lesson/<int:lesson_id>/complete', methods=['POST'])
@jwt_required()
def complete_lesson(lesson_id):
    """API para marcar uma lição como concluída."""
    # Obtém o ID do usuário a partir do token JWT
    user_id = get_jwt_identity()
    
    # Obtém o usuário
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    
    # Obtém a lição
    lesson = Lesson.query.get_or_404(lesson_id)
    
    # Obtém o módulo e o curso
    module = Module.query.get_or_404(lesson.module_id)
    course = Course.query.get_or_404(module.course_id)
    
    # Verifica se o usuário está matriculado no curso
    if course not in user.courses:
        return jsonify({'error': 'Acesso não autorizado a esta lição'}), 403
    
    # Atualiza ou cria o registro de progresso
    progress = Progress.query.filter_by(
        user_id=user.id,
        lesson_id=lesson.id
    ).first()
    
    if not progress:
        progress = Progress(
            user_id=user.id,
            course_id=course.id,
            module_id=module.id,
            lesson_id=lesson.id
        )
        db.session.add(progress)
    
    # Marca como concluída
    progress.complete()
    db.session.commit()
    
    # Registra a atividade de conclusão da lição
    UserActivity.log_activity(
        user_id=user.id,
        activity_type='lesson_complete',
        description=f'Lição concluída: {lesson.title}',
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string,
        metadata={
            'course_id': course.id,
            'module_id': module.id,
            'lesson_id': lesson.id,
            'xp_reward': lesson.xp_reward
        }
    )
    
    # Verifica se o usuário concluiu todo o curso
    course_progress = user.get_course_progress(course.id)
    
    result = {
        'message': 'Lição concluída com sucesso',
        'xp_reward': lesson.xp_reward,
        'course_progress': course_progress,
        'course_completed': False
    }
    
    if course_progress == 100:
        # Gera certificado se todas as lições forem concluídas
        existing_certificate = Certificate.query.filter_by(
            user_id=user.id,
            course_id=course.id
        ).first()
        
        if not existing_certificate:
            from uuid import uuid4
            
            certificate = Certificate(
                user_id=user.id,
                course_id=course.id,
                certificate_number=f"CERT-{course.id}-{user.id}-{uuid4().hex[:8].upper()}",
                issue_date=datetime.utcnow()
            )
            db.session.add(certificate)
            db.session.commit()
            
            result['course_completed'] = True
            result['certificate_id'] = certificate.id
            
            # Registra a atividade de conclusão do curso
            UserActivity.log_activity(
                user_id=user.id,
                activity_type='course_complete',
                description=f'Curso concluído: {course.title}',
                ip_address=request.remote_addr,
                user_agent=request.user_agent.string,
                metadata={
                    'course_id': course.id,
                    'certificate_id': certificate.id
                }
            )
    
    return jsonify(result)


# ===== Rotas de quizzes =====

@api_bp.route('/quiz/<int:quiz_id>', methods=['GET'])
@jwt_required()
def get_quiz(quiz_id):
    """API para obter detalhes de um quiz."""
    # Obtém o ID do usuário a partir do token JWT
    user_id = get_jwt_identity()
    
    # Obtém o usuário
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    
    # Obtém o quiz
    quiz = Quiz.query.get_or_404(quiz_id)
    
    # Obtém a lição e verifica se o usuário pode acessar
    lesson = Lesson.query.get_or_404(quiz.lesson_id)
    module = Module.query.get_or_404(lesson.module_id)
    course = Course.query.get_or_404(module.course_id)
    
    # Verifica se o usuário está matriculado no curso
    if course not in user.courses and not user.is_instructor():
        return jsonify({'error': 'Acesso não autorizado a este quiz'}), 403
    
    # Obtém as tentativas anteriores do usuário
    previous_attempts = QuizAttempt.query.filter_by(
        user_id=user.id,
        quiz_id=quiz.id
    ).order_by(QuizAttempt.completed_at.desc()).all()
    
    previous_attempts_data = []
    for attempt in previous_attempts:
        previous_attempts_data.append({
            'id': attempt.id,
            'score': attempt.score,
            'passed': attempt.passed,
            'started_at': attempt.started_at.isoformat(),
            'completed_at': attempt.completed_at.isoformat() if attempt.completed_at else None,
            'duration_minutes': attempt.get_duration()
        })
    
    # Verifica se o usuário esgotou o número máximo de tentativas
    can_attempt = True
    if quiz.max_attempts and len(previous_attempts) >= quiz.max_attempts:
        can_attempt = False
    
    # Obtém as informações do quiz
    quiz_data = quiz.to_dict()
    quiz_data['previous_attempts'] = previous_attempts_data
    quiz_data['can_attempt'] = can_attempt
    
    # Informações da lição e curso
    quiz_data['lesson'] = {
        'id': lesson.id,
        'title': lesson.title,
        'module_id': module.id
    }
    quiz_data['module'] = {
        'id': module.id,
        'title': module.title,
        'course_id': course.id
    }
    quiz_data['course'] = {
        'id': course.id,
        'title': course.title
    }
    
    # Registra a atividade de visualização do quiz
    UserActivity.log_activity(
        user_id=user.id,
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
    
    return jsonify(quiz_data)


@api_bp.route('/quiz/<int:quiz_id>/start', methods=['POST'])
@jwt_required()
def start_quiz_attempt(quiz_id):
    """API para iniciar uma tentativa de quiz."""
    # Obtém o ID do usuário a partir do token JWT
    user_id = get_jwt_identity()
    
    # Obtém o usuário
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    
    # Obtém o quiz
    quiz = Quiz.query.get_or_404(quiz_id)
    
    # Obtém a lição e verifica se o usuário pode acessar
    lesson = Lesson.query.get_or_404(quiz.lesson_id)
    module = Module.query.get_or_404(lesson.module_id)
    course = Course.query.get_or_404(module.course_id)
    
    # Verifica se o usuário está matriculado no curso
    if course not in user.courses and not user.is_instructor():
        return jsonify({'error': 'Acesso não autorizado a este quiz'}), 403
    
    # Obtém as tentativas anteriores do usuário
    previous_attempts = QuizAttempt.query.filter_by(
        user_id=user.id,
        quiz_id=quiz.id
    ).count()
    
    # Verifica se o usuário esgotou o número máximo de tentativas
    if quiz.max_attempts and previous_attempts >= quiz.max_attempts:
        return jsonify({'error': 'Número máximo de tentativas excedido'}), 400
    
    # Cria uma nova tentativa
    attempt = QuizAttempt(
        user_id=user.id,
        quiz_id=quiz.id,
        started_at=datetime.utcnow()
    )
    db.session.add(attempt)
    db.session.commit()
    
    # Obtém todas as questões do quiz
    questions = Question.query.filter_by(quiz_id=quiz.id).all()
    
    # Se o quiz for dinâmico, pode gerar questões via IA
    if quiz.quiz_type == 'dynamic' and not questions:
        try:
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
            return jsonify({'error': f'Erro ao gerar questões: {str(e)}'}), 500
    
    # Se o quiz não tiver questões, retorna erro
    if not questions:
        return jsonify({'error': 'Este quiz não possui questões cadastradas'}), 400
    
    # Embaralha as questões se necessário
    if quiz.shuffle_questions:
        import random
        random.shuffle(questions)
    
    # Prepara os dados das questões (sem a resposta correta)
    questions_data = []
    for question in questions:
        questions_data.append({
            'id': question.id,
            'text': question.text,
            'question_type': question.question_type,
            'options': question.options,
            'points': question.points
        })
    
    # Registra a atividade de início do quiz
    UserActivity.log_activity(
        user_id=user.id,
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
    
    return jsonify({
        'attempt_id': attempt.id,
        'quiz': {
            'id': quiz.id,
            'title': quiz.title,
            'description': quiz.description,
            'time_limit_minutes': quiz.time_limit_minutes
        },
        'questions': questions_data
    })


@api_bp.route('/quiz/attempt/<int:attempt_id>/submit', methods=['POST'])
@jwt_required()
def submit_quiz_attempt(attempt_id):
    """API para submeter respostas de uma tentativa de quiz."""
    # Obtém o ID do usuário a partir do token JWT
    user_id = get_jwt_identity()
    
    # Obtém o usuário
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    
    # Obtém a tentativa
    attempt = QuizAttempt.query.get_or_404(attempt_id)
    
    # Verifica se a tentativa pertence ao usuário
    if attempt.user_id != user.id:
        return jsonify({'error': 'Tentativa não pertence a este usuário'}), 403
    
    # Verifica se a tentativa já foi concluída
    if attempt.completed_at:
        return jsonify({'error': 'Esta tentativa já foi concluída'}), 400
    
    # Obtém o quiz
    quiz = Quiz.query.get_or_404(attempt.quiz_id)
    
    # Obtém todas as questões do quiz
    questions = Question.query.filter_by(quiz_id=quiz.id).all()
    question_map = {q.id: q for q in questions}
    
    # Obtém as respostas enviadas
    answers_data = request.json.get('answers', [])
    
    # Processa as respostas
    answers = []
    for answer_data in answers_data:
        question_id = answer_data.get('question_id')
        answer_value = answer_data.get('answer')
        
        if question_id in question_map:
            answers.append({
                'question_id': question_id,
                'answer': answer_value,
                'question_text': question_map[question_id].text
            })
    
    # Salva as respostas na tentativa
    attempt.answers = answers
    
    # Marca o horário de conclusão
    attempt.completed_at = datetime.utcnow()
    
    # Calcula a pontuação
    attempt.calculate_score()
    
    # Atualiza o progresso na lição se o usuário passou no quiz
    if attempt.passed:
        lesson = Lesson.query.get_or_404(quiz.lesson_id)
        progress = Progress.query.filter_by(
            user_id=user.id,
            lesson_id=lesson.id
        ).first()
        
        if progress:
            progress.complete()
            
        # Adiciona XP ao usuário
        if quiz.xp_reward:
            user.add_xp(quiz.xp_reward)
            
        db.session.commit()
    
    # Registra a atividade de conclusão do quiz
    UserActivity.log_activity(
        user_id=user.id,
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
    
    # Prepara os resultados para resposta
    lesson = Lesson.query.get_or_404(quiz.lesson_id)
    module = Module.query.get_or_404(lesson.module_id)
    course = Course.query.get_or_404(module.course_id)
    
    # Prepara os dados das respostas para o resultado
    answer_data = []
    for answer in attempt.answers:
        question_id = answer.get('question_id')
        question = question_map.get(question_id)
        if question:
            answer_data.append({
                'question_id': question_id,
                'question_text': question.text,
                'user_answer': answer.get('answer'),
                'is_correct': answer.get('is_correct', False),
                'correct_answer': question.correct_answer if quiz.show_answers else None,
                'explanation': question.explanation if quiz.show_answers else None
            })
    
    return jsonify({
        'attempt_id': attempt.id,
        'score': attempt.score,
        'passed': attempt.passed,
        'passing_score': quiz.passing_score,
        'duration_minutes': attempt.get_duration(),
        'xp_reward': quiz.xp_reward if attempt.passed else 0,
        'answers': answer_data if quiz.show_answers else None,
        'course': {
            'id': course.id,
            'title': course.title
        },
        'module': {
            'id': module.id,
            'title': module.title
        },
        'lesson': {
            'id': lesson.id,
            'title': lesson.title
        }
    })


# ===== Rotas de inteligência artificial =====

@api_bp.route('/ai/ask-assistant', methods=['POST'])
@jwt_required()
def ask_ai_assistant():
    """API para fazer perguntas ao assistente virtual de IA."""
    # Obtém o ID do usuário a partir do token JWT
    user_id = get_jwt_identity()
    
    # Obtém o usuário
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    
    # Obtém a pergunta do usuário
    data = request.json
    question = data.get('question')
    course_id = data.get('course_id')
    lesson_id = data.get('lesson_id')
    
    if not question:
        return jsonify({'error': 'A pergunta não foi fornecida'}), 400
    
    # Contexto para a IA
    context = "Você é um assistente educacional especializado em IA e Cybersegurança."
    
    # Se houver curso/lição específica, adiciona ao contexto
    if lesson_id:
        lesson = Lesson.query.get(lesson_id)
        if lesson:
            context += f"\nContexto da lição: {lesson.title}\n{lesson.content[:500]}..."
    elif course_id:
        course = Course.query.get(course_id)
        if course:
            context += f"\nContexto do curso: {course.title}\n{course.description}"
    
    try:
        # Obtém resposta da IA
        response = gemini_service.ask_assistant(
            question=question,
            context=context,
            user_name=user.get_full_name(),
            user_level=user.level
        )
        
        # Registra a atividade
        UserActivity.log_activity(
            user_id=user.id,
            activity_type='ai_assistant',
            description=f'Pergunta ao assistente: {question[:50]}...' if len(question) > 50 else question,
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string,
            metadata={
                'question': question,
                'course_id': course_id,
                'lesson_id': lesson_id
            }
        )
        
        return jsonify({'response': response})
    except Exception as e:
        return jsonify({'error': f'Erro ao processar a pergunta: {str(e)}'}), 500


@api_bp.route('/ai/generate-practice', methods=['POST'])
@jwt_required()
def generate_practice():
    """API para gerar exercícios práticos personalizados."""
    # Obtém o ID do usuário a partir do token JWT
    user_id = get_jwt_identity()
    
    # Obtém o usuário
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    
    # Obtém os parâmetros
    data = request.json
    lesson_id = data.get('lesson_id')
    difficulty = data.get('difficulty', 'medium')
    
    if not lesson_id:
        return jsonify({'error': 'ID da lição não fornecido'}), 400
    
    # Obtém a lição
    lesson = Lesson.query.get_or_404(lesson_id)
    
    try:
        # Gera exercícios práticos
        practice = gemini_service.generate_practice_exercises(
            title=lesson.title,
            content=lesson.content,
            difficulty=difficulty,
            user_level=user.level
        )
        
        # Registra a atividade
        UserActivity.log_activity(
            user_id=user.id,
            activity_type='generate_practice',
            description=f'Geração de exercícios práticos para a lição: {lesson.title}',
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string,
            metadata={
                'lesson_id': lesson_id,
                'difficulty': difficulty
            }
        )
        
        return jsonify(practice)
    except Exception as e:
        return jsonify({'error': f'Erro ao gerar exercícios: {str(e)}'}), 500


# ===== Rotas de multimídia =====

@api_bp.route('/youtube/search', methods=['GET'])
def search_youtube_videos():
    """API para buscar vídeos relacionados no YouTube."""
    # Parâmetros de busca
    query = request.args.get('query')
    max_results = request.args.get('max_results', 5, type=int)
    
    if not query:
        return jsonify({'error': 'Termo de busca não fornecido'}), 400
    
    try:
        # Busca vídeos
        videos = youtube_service.search_videos(query, max_results=max_results)
        return jsonify(videos)
    except Exception as e:
        return jsonify({'error': f'Erro ao buscar vídeos: {str(e)}'}), 500


@api_bp.route('/youtube/related/<string:lesson_slug>', methods=['GET'])
def get_related_videos(lesson_slug):
    """API para obter vídeos relacionados a uma lição específica."""
    # Obtém a lição pelo slug
    lesson = Lesson.query.filter_by(slug=lesson_slug).first_or_404()
    
    # Obtém o módulo e o curso
    module = Module.query.get_or_404(lesson.module_id)
    course = Course.query.get_or_404(module.course_id)
    
    # Define a consulta de busca com base no título da lição e categoria do curso
    query = f"{course.category} {lesson.title}"
    max_results = request.args.get('max_results', 3, type=int)
    
    try:
        # Busca vídeos relacionados
        videos = youtube_service.search_videos(query, max_results=max_results)
        
        # Armazena em cache por 24 horas
        cache_key = f'youtube_videos_{lesson.id}'
        cache.set(cache_key, videos, timeout=86400)  # 24 horas
        
        return jsonify(videos)
    except Exception as e:
        # Tenta recuperar do cache se a busca falhar
        cache_key = f'youtube_videos_{lesson.id}'
        cached_videos = cache.get(cache_key)
        
        if cached_videos:
            return jsonify(cached_videos)
        else:
            return jsonify({'error': f'Erro ao buscar vídeos: {str(e)}'}), 500