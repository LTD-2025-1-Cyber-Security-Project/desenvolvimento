from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, flash
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import logging
from logging.handlers import RotatingFileHandler
import json
import shutil

from config import Config
from utils.security import SecurityManager
from utils.file_converter import FileConverter
from utils.pdf_analyzer import PDFAnalyzer
from utils.ai_integration import AIIntegration

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
CORS(app)
db = SQLAlchemy(app)
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# Create necessary directories
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['PROCESSED_FOLDER'], exist_ok=True)

# Set up logging
if not app.debug:
    file_handler = RotatingFileHandler('app.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)

# Database models
class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(50))
    file_size = db.Column(db.Integer)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    category = db.Column(db.String(50))
    tags = db.Column(db.String(255))
    processed = db.Column(db.Boolean, default=False)
    file_hash = db.Column(db.String(64))
    user_id = db.Column(db.String(50))  # For future user authentication

class ProcessedDocument(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('document.id'))
    process_type = db.Column(db.String(50))
    result_file = db.Column(db.String(255))
    process_date = db.Column(db.DateTime, default=datetime.utcnow)
    process_metadata = db.Column(db.Text)  # JSON string - renamed from metadata

# Routes
@app.route('/')
def index():
    recent_files = Document.query.order_by(Document.upload_date.desc()).limit(10).all()
    return render_template('index.html', recent_files=recent_files)

@app.route('/upload')
def upload():
    return render_template('upload.html')

@app.route('/converter')
def converter():
    user_files = Document.query.order_by(Document.upload_date.desc()).all()
    return render_template('converter.html', user_files=user_files)

@app.route('/analyzer')
def analyzer():
    user_files = Document.query.order_by(Document.upload_date.desc()).all()
    selected_file_id = request.args.get('file_id')
    return render_template('analyzer.html', user_files=user_files, selected_file_id=selected_file_id)

@app.route('/analyze_file/<int:file_id>')
def analyze_file(file_id):
    """Rota de compatibilidade que redireciona para o analyzer com o file_id"""
    return redirect(url_for('analyzer', file_id=file_id))

@app.route('/ocr')
def ocr():
    user_files = Document.query.order_by(Document.upload_date.desc()).all()
    return render_template('ocr.html', user_files=user_files)

@app.route('/pdf_tools')
def pdf_tools():
    user_files = Document.query.order_by(Document.upload_date.desc()).all()
    return render_template('pdf_tools.html', user_files=user_files)

@app.route('/pdf_security')
def pdf_security():
    user_files = Document.query.order_by(Document.upload_date.desc()).all()
    return render_template('pdf_security.html', user_files=user_files)

# API Routes
@app.route('/api/upload', methods=['POST'])
@limiter.limit("10 per minute")
def api_upload():
    try:
        if 'files' not in request.files and 'files[]' not in request.files:
            return jsonify({'success': False, 'error': 'Nenhum arquivo enviado'}), 400
        
        files = request.files.getlist('files') or request.files.getlist('files[]')
        uploaded_files = []
        
        for file in files:
            if file and SecurityManager.allowed_file(file.filename):
                # Check file size
                if not SecurityManager.check_file_size(file):
                    return jsonify({'success': False, 'error': f'Arquivo {file.filename} excede o tamanho máximo permitido'}), 400
                
                # Save file securely
                filename, filepath = SecurityManager.secure_save_file(file)
                
                # Get file info
                file_size = os.path.getsize(filepath)
                file_hash = SecurityManager.get_file_hash(filepath)
                
                # Save to database
                doc = Document(
                    filename=filename,
                    original_filename=file.filename,
                    file_type=file.filename.rsplit('.', 1)[1].lower(),
                    file_size=file_size,
                    category=request.form.get('category'),
                    tags=request.form.get('tags'),
                    file_hash=file_hash
                )
                db.session.add(doc)
                db.session.commit()  # Commit to get the ID
                
                uploaded_files.append({
                    'id': doc.id,
                    'filename': doc.original_filename,
                    'size': file_size
                })
        
        # Auto-process if requested
        if request.form.get('autoProcess') == 'true':
            # Queue for processing (implement with Celery later)
            pass
        
        return jsonify({
            'success': True,
            'files': uploaded_files
        })
    
    except Exception as e:
        app.logger.error(f"Upload error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/convert', methods=['POST'])
@limiter.limit("5 per minute")
def api_convert():
    try:
        data = request.json
        file_id = data.get('file_id')
        output_format = data.get('output_format')
        
        if not file_id or not output_format:
            return jsonify({'success': False, 'error': 'Parâmetros inválidos'}), 400
        
        # Get file from database
        doc = Document.query.get(file_id)
        if not doc:
            return jsonify({'success': False, 'error': 'Arquivo não encontrado'}), 404
        
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], doc.filename)
        output_filename = f"{os.path.splitext(doc.filename)[0]}.{output_format}"
        output_path = os.path.join(app.config['PROCESSED_FOLDER'], output_filename)
        
        # Perform conversion
        result_path = FileConverter.convert_file(input_path, output_format, output_path=output_path)
        
        # Save to database
        processed_doc = ProcessedDocument(
            document_id=doc.id,
            process_type=f'convert_to_{output_format}',
            result_file=os.path.basename(result_path)
        )
        db.session.add(processed_doc)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'result_file': url_for('download_file', file_id=processed_doc.id, type='processed')
        })
    
    except Exception as e:
        app.logger.error(f"Conversion error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/analyze', methods=['POST'])
@limiter.limit("3 per minute")
def api_analyze():
    try:
        data = request.json
        file_id = data.get('file_id')
        
        if not file_id:
            return jsonify({'success': False, 'error': 'ID do arquivo não fornecido'}), 400
        
        # Get file from database
        doc = Document.query.get(file_id)
        if not doc:
            return jsonify({'success': False, 'error': 'Arquivo não encontrado'}), 404
        
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], doc.filename)
        
        # Analyze PDF
        analyzer = PDFAnalyzer()
        result = analyzer.full_analysis(file_path)
        
        # Save analysis result
        processed_doc = ProcessedDocument(
            document_id=doc.id,
            process_type='ai_analysis',
            process_metadata=json.dumps(result)
        )
        db.session.add(processed_doc)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'analysis': result
        })
    
    except Exception as e:
        app.logger.error(f"Analysis error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/ocr', methods=['POST'])
@limiter.limit("3 per minute")
def api_ocr():
    try:
        data = request.json
        file_id = data.get('file_id')
        language = data.get('language', 'por+eng')
        
        if not file_id:
            return jsonify({'success': False, 'error': 'ID do arquivo não fornecido'}), 400
        
        # Get file from database
        doc = Document.query.get(file_id)
        if not doc:
            return jsonify({'success': False, 'error': 'Arquivo não encontrado'}), 404
        
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], doc.filename)
        
        # Perform OCR
        text = FileConverter.ocr_pdf(file_path, language)
        
        # Save OCR result
        output_filename = f"{os.path.splitext(doc.filename)[0]}_ocr.txt"
        output_path = os.path.join(app.config['PROCESSED_FOLDER'], output_filename)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(text)
        
        processed_doc = ProcessedDocument(
            document_id=doc.id,
            process_type='ocr',
            result_file=output_filename
        )
        db.session.add(processed_doc)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'text': text,
            'download_url': url_for('download_file', file_id=processed_doc.id, type='processed')
        })
    
    except Exception as e:
        app.logger.error(f"OCR error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/recent-uploads')
def api_recent_uploads():
    try:
        files = Document.query.order_by(Document.upload_date.desc()).limit(10).all()
        return jsonify({
            'files': [{
                'id': f.id,
                'name': f.original_filename,
                'type': f.file_type,
                'size': f.file_size,
                'date': f.upload_date.strftime('%Y-%m-%d %H:%M')
            } for f in files]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/storage-info')
def api_storage_info():
    try:
        total_size = sum(f.file_size for f in Document.query.all())
        max_size = 1024 * 1024 * 1024  # 1GB
        
        return jsonify({
            'used': f"{total_size / (1024 * 1024):.2f} MB",
            'total': "1 GB",
            'percentage': int((total_size / max_size) * 100) if max_size > 0 else 0
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/delete-file/<int:file_id>', methods=['DELETE'])
def api_delete_file(file_id):
    try:
        doc = Document.query.get(file_id)
        if not doc:
            return jsonify({'success': False, 'error': 'Arquivo não encontrado'}), 404
        
        # Delete physical file
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], doc.filename)
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # Delete processed files
        processed_docs = ProcessedDocument.query.filter_by(document_id=doc.id).all()
        for pdoc in processed_docs:
            if pdoc.result_file:
                pfile_path = os.path.join(app.config['PROCESSED_FOLDER'], pdoc.result_file)
                if os.path.exists(pfile_path):
                    os.remove(pfile_path)
            db.session.delete(pdoc)
        
        # Delete from database
        db.session.delete(doc)
        db.session.commit()
        
        return jsonify({'success': True})
    
    except Exception as e:
        app.logger.error(f"Delete error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/clear-storage', methods=['POST'])
def api_clear_storage():
    try:
        # Clear old files (older than 24 hours)
        SecurityManager.cleanup_old_files(app.config['UPLOAD_FOLDER'])
        SecurityManager.cleanup_old_files(app.config['PROCESSED_FOLDER'])
        
        return jsonify({'success': True})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/download/<int:file_id>')
def download_file(file_id):
    try:
        doc_type = request.args.get('type', 'original')
        
        if doc_type == 'original':
            doc = Document.query.get(file_id)
            if not doc:
                flash('Arquivo não encontrado', 'error')
                return redirect(url_for('index'))
            
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], doc.filename)
            if not os.path.exists(file_path):
                flash('Arquivo não encontrado no servidor', 'error')
                return redirect(url_for('index'))
                
            return send_file(file_path, as_attachment=True, download_name=doc.original_filename)
        
        elif doc_type == 'processed':
            pdoc = ProcessedDocument.query.get(file_id)
            if not pdoc:
                flash('Arquivo processado não encontrado', 'error')
                return redirect(url_for('index'))
            
            file_path = os.path.join(app.config['PROCESSED_FOLDER'], pdoc.result_file)
            if not os.path.exists(file_path):
                flash('Arquivo processado não encontrado no servidor', 'error')
                return redirect(url_for('index'))
                
            return send_file(file_path, as_attachment=True)
    
    except Exception as e:
        app.logger.error(f"Download error: {str(e)}")
        flash('Erro ao baixar arquivo', 'error')
        return redirect(url_for('index'))

@app.route('/api/merge-pdfs', methods=['POST'])
@limiter.limit("5 per minute")
def api_merge_pdfs():
    try:
        data = request.json
        file_ids = data.get('file_ids', [])
        output_name = data.get('output_name', 'merged.pdf')
        
        if len(file_ids) < 2:
            return jsonify({'success': False, 'error': 'Selecione pelo menos 2 arquivos'}), 400
        
        # Get files from database
        files_to_merge = []
        for file_id in file_ids:
            doc = Document.query.get(file_id)
            if doc and doc.file_type == 'pdf':
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], doc.filename)
                if os.path.exists(file_path):
                    files_to_merge.append(file_path)
        
        if len(files_to_merge) < 2:
            return jsonify({'success': False, 'error': 'Arquivos insuficientes para mesclar'}), 400
        
        # Merge PDFs
        output_path = os.path.join(app.config['PROCESSED_FOLDER'], output_name)
        FileConverter.merge_pdfs(files_to_merge, output_path)
        
        # Create document record
        doc = Document(
            filename=os.path.basename(output_path),
            original_filename=output_name,
            file_type='pdf',
            file_size=os.path.getsize(output_path),
            file_hash=SecurityManager.get_file_hash(output_path)
        )
        db.session.add(doc)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'download_url': url_for('download_file', file_id=doc.id)
        })
    
    except Exception as e:
        app.logger.error(f"Merge error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/split-pdf', methods=['POST'])
@limiter.limit("5 per minute")
def api_split_pdf():
    try:
        data = request.json
        file_id = data.get('file_id')
        method = data.get('method', 'pages')
        
        if not file_id:
            return jsonify({'success': False, 'error': 'ID do arquivo não fornecido'}), 400
        
        doc = Document.query.get(file_id)
        if not doc or doc.file_type != 'pdf':
            return jsonify({'success': False, 'error': 'Arquivo PDF não encontrado'}), 404
        
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], doc.filename)
        output_dir = os.path.join(app.config['PROCESSED_FOLDER'], f"split_{doc.id}")
        
        if method == 'pages':
            pages_per_file = data.get('pages_per_file', 1)
            output_files = FileConverter.split_pdf(input_path, output_dir, pages_per_file)
        else:
            return jsonify({'success': False, 'error': 'Método não suportado'}), 400
        
        # Create zip file with all split PDFs
        import zipfile
        zip_path = os.path.join(app.config['PROCESSED_FOLDER'], f"split_{doc.id}.zip")
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for file in output_files:
                zipf.write(file, os.path.basename(file))
        
        # Create document record for the zip
        zip_doc = Document(
            filename=os.path.basename(zip_path),
            original_filename=f"split_{doc.original_filename}.zip",
            file_type='zip',
            file_size=os.path.getsize(zip_path),
            file_hash=SecurityManager.get_file_hash(zip_path)
        )
        db.session.add(zip_doc)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'download_url': url_for('download_file', file_id=zip_doc.id)
        })
    
    except Exception as e:
        app.logger.error(f"Split error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/compress-pdf', methods=['POST'])
@limiter.limit("5 per minute")
def api_compress_pdf():
    try:
        data = request.json
        file_id = data.get('file_id')
        compression_level = data.get('compression_level', 'medium')
        
        if not file_id:
            return jsonify({'success': False, 'error': 'ID do arquivo não fornecido'}), 400
        
        doc = Document.query.get(file_id)
        if not doc or doc.file_type != 'pdf':
            return jsonify({'success': False, 'error': 'Arquivo PDF não encontrado'}), 404
        
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], doc.filename)
        output_filename = f"{os.path.splitext(doc.filename)[0]}_compressed.pdf"
        output_path = os.path.join(app.config['PROCESSED_FOLDER'], output_filename)
        
        # Compress PDF
        FileConverter.compress_pdf(input_path, output_path)
        
        # Calculate size reduction
        original_size = os.path.getsize(input_path)
        compressed_size = os.path.getsize(output_path)
        size_reduction = int(((original_size - compressed_size) / original_size) * 100)
        
        # Save to database
        processed_doc = ProcessedDocument(
            document_id=doc.id,
            process_type='compress',
            result_file=output_filename
        )
        db.session.add(processed_doc)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'size_reduction': size_reduction,
            'download_url': url_for('download_file', file_id=processed_doc.id, type='processed')
        })
    
    except Exception as e:
        app.logger.error(f"Compression error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/protect-pdf', methods=['POST'])
@limiter.limit("5 per minute")
def api_protect_pdf():
    try:
        data = request.json
        file_id = data.get('file_id')
        password = data.get('permission_password')
        
        if not file_id or not password:
            return jsonify({'success': False, 'error': 'Parâmetros inválidos'}), 400
        
        doc = Document.query.get(file_id)
        if not doc or doc.file_type != 'pdf':
            return jsonify({'success': False, 'error': 'Arquivo PDF não encontrado'}), 404
        
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], doc.filename)
        output_filename = f"{os.path.splitext(doc.filename)[0]}_protected.pdf"
        output_path = os.path.join(app.config['PROCESSED_FOLDER'], output_filename)
        
        # Protect PDF
        FileConverter.protect_pdf(input_path, password, output_path)
        
        # Save to database
        processed_doc = ProcessedDocument(
            document_id=doc.id,
            process_type='protect',
            result_file=output_filename
        )
        db.session.add(processed_doc)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'download_url': url_for('download_file', file_id=processed_doc.id, type='processed')
        })
    
    except Exception as e:
        app.logger.error(f"Protection error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/add-watermark', methods=['POST'])
@limiter.limit("5 per minute")
def api_add_watermark():
    try:
        data = request.json
        file_id = data.get('file_id')
        watermark_text = data.get('text', 'CONFIDENTIAL')
        
        if not file_id:
            return jsonify({'success': False, 'error': 'ID do arquivo não fornecido'}), 400
        
        doc = Document.query.get(file_id)
        if not doc or doc.file_type != 'pdf':
            return jsonify({'success': False, 'error': 'Arquivo PDF não encontrado'}), 404
        
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], doc.filename)
        output_filename = f"{os.path.splitext(doc.filename)[0]}_watermarked.pdf"
        output_path = os.path.join(app.config['PROCESSED_FOLDER'], output_filename)
        
        # Add watermark
        FileConverter.add_watermark(input_path, watermark_text, output_path)
        
        # Save to database
        processed_doc = ProcessedDocument(
            document_id=doc.id,
            process_type='watermark',
            result_file=output_filename
        )
        db.session.add(processed_doc)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'download_url': url_for('download_file', file_id=processed_doc.id, type='processed')
        })
    
    except Exception as e:
        app.logger.error(f"Watermark error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

# CLI Commands
@app.cli.command('init-db')
def init_db():
    """Initialize the database."""
    db.create_all()
    print('Database initialized!')

@app.cli.command('clear-uploads')
def clear_uploads():
    """Clear all uploaded files."""
    try:
        shutil.rmtree(app.config['UPLOAD_FOLDER'])
        shutil.rmtree(app.config['PROCESSED_FOLDER'])
        os.makedirs(app.config['UPLOAD_FOLDER'])
        os.makedirs(app.config['PROCESSED_FOLDER'])
        
        # Clear database
        Document.query.delete()
        ProcessedDocument.query.delete()
        db.session.commit()
        
        print('All uploads cleared!')
    except Exception as e:
        print(f'Error clearing uploads: {str(e)}')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)