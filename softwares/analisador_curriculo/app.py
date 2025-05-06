from flask import Flask, render_template, request, redirect, url_for, flash, session
import os
import datetime
from werkzeug.utils import secure_filename
import uuid
from dotenv import load_dotenv

from utils.pdf_extractor import extract_text_from_pdf
from utils.resume_analyzer import analyze_resume

# Carregar variáveis de ambiente
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "development_secret_key")

# Verificar a chave da API do Google
if not os.getenv("GOOGLE_API_KEY"):
    print("AVISO: Chave de API do Google Gemini não encontrada. Configure a variável de ambiente GOOGLE_API_KEY.")

# Configurações
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

# Criar pasta de uploads se não existir
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    # Passar o ano atual para o template para exibir no rodapé
    now = datetime.datetime.now()
    return render_template('index.html', now=now)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'resume' not in request.files:
        flash('Nenhum arquivo enviado', 'error')
        return redirect(request.url)
    
    file = request.files['resume']
    
    if file.filename == '':
        flash('Nenhum arquivo selecionado', 'error')
        return redirect(request.url)
    
    if not allowed_file(file.filename):
        flash('Formato de arquivo não permitido. Por favor, envie um PDF.', 'error')
        return redirect(request.url)
    
    # Obter parâmetros de análise
    tipo_analise = request.form.get('tipo_analise', 'geral')
    nivel = request.form.get('nivel', 'junior')
    stack_area = request.form.get('stack_area', 'desenvolvimento web')
    
    # Gerar nome de arquivo único
    filename = secure_filename(file.filename)
    unique_filename = f"{uuid.uuid4()}_{filename}"
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
    
    # Salvar arquivo
    file.save(file_path)
    
    try:
        # Extrair texto do PDF
        resume_text = extract_text_from_pdf(file_path)
        
        # Analisar currículo
        analysis_result = analyze_resume(
            resume_text=resume_text,
            tipo_analise=tipo_analise,
            nivel=nivel,
            stack_area=stack_area
        )
        
        # Armazenar resultado na sessão
        session['analysis_result'] = analysis_result
        
        return redirect(url_for('result'))
    
    except Exception as e:
        flash(f'Erro ao processar o currículo: {str(e)}', 'error')
        return redirect(url_for('index'))
    finally:
        # Limpar o arquivo após o processamento
        if os.path.exists(file_path):
            os.remove(file_path)

@app.route('/result')
def result():
    analysis_result = session.get('analysis_result')
    if not analysis_result:
        flash('Nenhuma análise encontrada. Por favor, envie um currículo.', 'error')
        return redirect(url_for('index'))
    
    # Adicionar a variável now para o template
    now = datetime.datetime.now()
    return render_template('result.html', analysis=analysis_result, now=now)

@app.errorhandler(413)
def too_large(e):
    flash('O arquivo é muito grande. O tamanho máximo é 16MB.', 'error')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.getenv("PORT", 5000)))