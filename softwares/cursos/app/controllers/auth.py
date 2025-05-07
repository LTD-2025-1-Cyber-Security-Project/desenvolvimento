#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Controlador de autenticação.
Este módulo gerencia as rotas relacionadas à autenticação, como login, registro,
recuperação de senha e gerenciamento de perfil.
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_user, logout_user, login_required, current_user
from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt_identity, jwt_required
from app import db, bcrypt, mail
from app.models.user import User, UserRoles
from app.models.progress import UserActivity
from app.utils.validators import validate_password, validate_email
from app.utils.security import generate_confirmation_token, confirm_token
from flask_mail import Message
import uuid
from datetime import datetime, timedelta

# Criação do Blueprint de autenticação
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Rota para registro de novos usuários."""
    if current_user.is_authenticated:
        return redirect(url_for('courses.dashboard'))
        
    if request.method == 'POST':
        # Obtém os dados do formulário
        data = request.form
        email = data.get('email')
        password = data.get('password')
        confirm_password = data.get('confirm_password')
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        municipality = data.get('municipality')
        department = data.get('department')
        job_title = data.get('job_title')
        
        # Validação de dados
        errors = []
        
        # Verifica se o email já está em uso
        if User.query.filter_by(email=email).first():
            errors.append('Este e-mail já está cadastrado.')
        
        # Validação de e-mail
        if not validate_email(email):
            errors.append('E-mail inválido.')
        
        # Validação de senha
        if password != confirm_password:
            errors.append('As senhas não coincidem.')
        
        password_errors = validate_password(password)
        if password_errors:
            errors.extend(password_errors)
        
        # Validação de nome
        if not first_name:
            errors.append('O nome é obrigatório.')
        if not last_name:
            errors.append('O sobrenome é obrigatório.')
            
        # Validação de município
        if not municipality or municipality not in ['Florianópolis', 'São José']:
            errors.append('Selecione um município válido (Florianópolis ou São José).')
            
        # Validação de departamento e cargo
        if not department:
            errors.append('O departamento é obrigatório.')
        if not job_title:
            errors.append('O cargo é obrigatório.')
            
        # Se não houver erros, cria o novo usuário
        if not errors:
            # Cria o novo usuário
            new_user = User(
                email=email,
                first_name=first_name,
                last_name=last_name,
                municipality=municipality,
                department=department,
                job_title=job_title,
                role=UserRoles.STUDENT  # padrão é aluno
            )
            
            # Define a senha (importante: é preciso chamar este método separadamente)
            new_user.set_password(password)
            
            # Salva o usuário no banco de dados
            db.session.add(new_user)
            db.session.commit()
            
            # Registra a atividade
            UserActivity.log_activity(
                user_id=new_user.id,
                activity_type='register',
                description='Registro de nova conta',
                ip_address=request.remote_addr,
                user_agent=request.user_agent.string
            )
            
            # Em ambiente de desenvolvimento, não enviar e-mail
            # Apenas simular o envio e mostrar mensagem no console
            token = generate_confirmation_token(new_user.email)
            confirm_url = url_for('auth.confirm_email', token=token, _external=True)
            
            # Exibe no console em vez de enviar e-mail
            print(f"==================== SIMULAÇÃO DE ENVIO DE EMAIL ====================")
            print(f"Para: {new_user.email}")
            print(f"Assunto: Confirme seu e-mail - EdTech IA & Cyber")
            print(f"Corpo: Olá {new_user.first_name},")
            print(f"")
            print(f"Obrigado por se cadastrar na plataforma EdTech IA & Cyber. Para confirmar seu e-mail, clique no link abaixo:")
            print(f"")
            print(f"{confirm_url}")
            print(f"")
            print(f"Se você não se cadastrou nesta plataforma, por favor ignore este e-mail.")
            print(f"")
            print(f"Atenciosamente,")
            print(f"Equipe EdTech IA & Cyber")
            print(f"===================================================================")
            
            # Faz login do usuário automaticamente
            login_user(new_user)
            
            flash('Cadastro realizado com sucesso! Em um ambiente de produção, um e-mail de confirmação seria enviado.', 'success')
            return redirect(url_for('courses.dashboard'))
        else:
            # Se houver erros, exibe mensagem
            for error in errors:
                flash(error, 'danger')
                
    # Renderiza o template de registro
    return render_template('auth/register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Rota para login de usuários."""
    if current_user.is_authenticated:
        return redirect(url_for('courses.dashboard'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False
        
        # Busca o usuário pelo email
        user = User.query.filter_by(email=email).first()
        
        # Verifica se o usuário existe e a senha está correta
        if user and user.check_password(password):
            # Verifica se o usuário está ativo
            if not user.is_active:
                flash('Sua conta está desativada. Entre em contato com o administrador.', 'danger')
                return redirect(url_for('auth.login'))
                
            # Faz login do usuário
            login_user(user, remember=remember)
            
            # Atualiza o último login
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            # Registra a atividade
            UserActivity.log_activity(
                user_id=user.id,
                activity_type='login',
                description='Login bem-sucedido',
                ip_address=request.remote_addr,
                user_agent=request.user_agent.string
            )
            
            # Redireciona para a página solicitada ou para o dashboard
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            else:
                flash('Login realizado com sucesso!', 'success')
                return redirect(url_for('courses.dashboard'))
        else:
            flash('E-mail ou senha inválidos. Tente novamente.', 'danger')
            
    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """Rota para logout de usuários."""
    # Registra a atividade antes de fazer logout
    if current_user.is_authenticated:
        UserActivity.log_activity(
            user_id=current_user.id,
            activity_type='logout',
            description='Logout',
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string
        )
    
    logout_user()
    flash('Você foi desconectado com sucesso.', 'success')
    return redirect(url_for('auth.login'))


@auth_bp.route('/confirm/<token>')
def confirm_email(token):
    """Rota para confirmar e-mail após o registro."""
    try:
        email = confirm_token(token)
    except:
        flash('O link de confirmação é inválido ou expirou.', 'danger')
        return redirect(url_for('auth.login'))
        
    user = User.query.filter_by(email=email).first()
    if not user:
        flash('Usuário não encontrado.', 'danger')
        return redirect(url_for('auth.login'))
        
    # Registra a atividade
    UserActivity.log_activity(
        user_id=user.id,
        activity_type='email_confirm',
        description='E-mail confirmado com sucesso',
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string
    )
    
    flash('Seu e-mail foi confirmado com sucesso!', 'success')
    return redirect(url_for('courses.dashboard'))


@auth_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password_request():
    """Rota para solicitar redefinição de senha."""
    if current_user.is_authenticated:
        return redirect(url_for('courses.dashboard'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        
        user = User.query.filter_by(email=email).first()
        if user:
            # Gera token para redefinição de senha
            token = str(uuid.uuid4())
            user.reset_token = token
            user.reset_token_expiry = datetime.utcnow() + timedelta(hours=24)
            db.session.commit()
            
            # Em ambiente de desenvolvimento, não enviar e-mail
            # Apenas simular o envio e mostrar mensagem no console
            reset_url = url_for('auth.reset_password', token=token, _external=True)
            
            # Exibe no console em vez de enviar e-mail
            print(f"==================== SIMULAÇÃO DE ENVIO DE EMAIL ====================")
            print(f"Para: {user.email}")
            print(f"Assunto: Redefinição de Senha - EdTech IA & Cyber")
            print(f"Corpo: Olá {user.first_name},")
            print(f"")
            print(f"Você solicitou a redefinição de sua senha. Para criar uma nova senha, clique no link abaixo:")
            print(f"")
            print(f"{reset_url}")
            print(f"")
            print(f"Este link expira em 24 horas. Se você não solicitou esta redefinição, por favor ignore este e-mail.")
            print(f"")
            print(f"Atenciosamente,")
            print(f"Equipe EdTech IA & Cyber")
            print(f"===================================================================")
            
            # Registra a atividade
            UserActivity.log_activity(
                user_id=user.id,
                activity_type='password_reset_request',
                description='Solicitação de redefinição de senha',
                ip_address=request.remote_addr,
                user_agent=request.user_agent.string
            )
        
        flash('Se um e-mail correspondente existir no sistema, você receberá instruções para redefinir sua senha.', 'info')
        return redirect(url_for('auth.login'))
        
    return render_template('auth/reset_password_request.html')


@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Rota para redefinir a senha com token."""
    if current_user.is_authenticated:
        return redirect(url_for('courses.dashboard'))
        
    # Verifica se o token é válido
    user = User.query.filter_by(reset_token=token).first()
    if not user or not user.reset_token_expiry or user.reset_token_expiry < datetime.utcnow():
        flash('O link de redefinição é inválido ou expirou.', 'danger')
        return redirect(url_for('auth.login'))
        
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validação de senha
        errors = []
        
        if password != confirm_password:
            errors.append('As senhas não coincidem.')
        
        password_errors = validate_password(password)
        if password_errors:
            errors.extend(password_errors)
            
        if not errors:
            # Atualiza a senha
            user.set_password(password)
            user.reset_token = None
            user.reset_token_expiry = None
            db.session.commit()
            
            # Registra a atividade
            UserActivity.log_activity(
                user_id=user.id,
                activity_type='password_reset',
                description='Senha redefinida com sucesso',
                ip_address=request.remote_addr,
                user_agent=request.user_agent.string
            )
            
            flash('Sua senha foi atualizada com sucesso!', 'success')
            return redirect(url_for('auth.login'))
        else:
            for error in errors:
                flash(error, 'danger')
                
    return render_template('auth/reset_password.html')


@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """Rota para visualizar e editar o perfil do usuário."""
    if request.method == 'POST':
        # Obtém os dados do formulário
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        department = request.form.get('department')
        job_title = request.form.get('job_title')
        bio = request.form.get('bio')
        
        # Upload de foto de perfil, se houver
        if 'profile_pic' in request.files:
            file = request.files['profile_pic']
            if file and file.filename:
                from werkzeug.utils import secure_filename
                import os
                
                # Gera um nome seguro e único para o arquivo
                filename = secure_filename(file.filename)
                extension = os.path.splitext(filename)[1]
                new_filename = f"{current_user.uuid}{extension}"
                
                # Salva o arquivo
                upload_folder = current_app.config['UPLOAD_FOLDER']
                file_path = os.path.join(upload_folder, 'profile_pics', new_filename)
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                file.save(file_path)
                
                # Atualiza o caminho da foto no usuário
                current_user.profile_pic = f"/static/uploads/profile_pics/{new_filename}"
        
        # Atualiza os dados do usuário
        current_user.first_name = first_name
        current_user.last_name = last_name
        current_user.department = department
        current_user.job_title = job_title
        current_user.bio = bio
        
        db.session.commit()
        
        # Registra a atividade
        UserActivity.log_activity(
            user_id=current_user.id,
            activity_type='profile_update',
            description='Atualização de perfil',
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string
        )
        
        flash('Seu perfil foi atualizado com sucesso!', 'success')
        return redirect(url_for('auth.profile'))
        
    return render_template('auth/profile.html', user=current_user)


@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Rota para alterar a senha do usuário."""
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # Validação
        errors = []
        
        # Verifica se a senha atual está correta
        if not current_user.check_password(current_password):
            errors.append('Senha atual incorreta.')
            
        # Verifica se as novas senhas coincidem
        if new_password != confirm_password:
            errors.append('As novas senhas não coincidem.')
            
        # Validação da nova senha
        password_errors = validate_password(new_password)
        if password_errors:
            errors.extend(password_errors)
            
        if not errors:
            # Atualiza a senha
            current_user.set_password(new_password)
            db.session.commit()
            
            # Registra a atividade
            UserActivity.log_activity(
                user_id=current_user.id,
                activity_type='password_change',
                description='Alteração de senha',
                ip_address=request.remote_addr,
                user_agent=request.user_agent.string
            )
            
            flash('Sua senha foi alterada com sucesso!', 'success')
            return redirect(url_for('auth.profile'))
        else:
            for error in errors:
                flash(error, 'danger')
                
    return render_template('auth/change_password.html')


# API para autenticação via JWT (para integração com apps móveis ou externos)
@auth_bp.route('/api/token', methods=['POST'])
def get_token():
    """API para obter token JWT."""
    if not request.is_json:
        return jsonify({"msg": "Missing JSON in request"}), 400
        
    email = request.json.get('email', None)
    password = request.json.get('password', None)
    
    if not email or not password:
        return jsonify({"msg": "Missing username or password"}), 400
        
    user = User.query.filter_by(email=email).first()
    
    if not user or not user.check_password(password) or not user.is_active:
        return jsonify({"msg": "Bad username or password"}), 401
        
    # Atualiza o último login
    user.last_login = datetime.utcnow()
    db.session.commit()
    
    # Registra a atividade
    UserActivity.log_activity(
        user_id=user.id,
        activity_type='token_request',
        description='Solicitação de token JWT',
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string
    )
    
    # Cria o token JWT
    access_token = create_access_token(identity=user.id)
    refresh_token = create_refresh_token(identity=user.id)
    
    return jsonify({
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": user.to_dict()
    }), 200


@auth_bp.route('/api/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh_token():
    """API para renovar token JWT."""
    current_user_id = get_jwt_identity()
    
    # Verifica se o usuário ainda está ativo
    user = User.query.get(current_user_id)
    if not user or not user.is_active:
        return jsonify({"msg": "User not found or inactive"}), 401
    
    # Cria novo token de acesso
    access_token = create_access_token(identity=current_user_id)
    
    # Registra a atividade
    UserActivity.log_activity(
        user_id=current_user_id,
        activity_type='token_refresh',
        description='Renovação de token JWT',
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string
    )
    
    return jsonify({"access_token": access_token}), 200