"""
DocMaster Pro - Criador de Executável
Este script cria um executável autônomo para o DocMaster Pro compatível com Windows.
"""

import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path

def main():
    print("\n" + "="*70)
    print("    CRIADOR DE EXECUTÁVEL DO DOCMASTER PRO")
    print("="*70)
    
    base_dir = Path(__file__).parent.absolute()
    
    # Verifica se o PyInstaller está instalado
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
        print("[OK] PyInstaller instalado")
    except Exception as e:
        print(f"[ERRO] Falha ao instalar PyInstaller: {e}")
        input("Pressione Enter para sair...")
        return
    
    # Verifica se os diretórios necessários existem
    missing_dirs = []
    for dir_name in ['templates', 'static']:
        if not (base_dir / dir_name).exists():
            missing_dirs.append(dir_name)
    
    if missing_dirs:
        print(f"[AVISO] Os seguintes diretórios estão faltando: {', '.join(missing_dirs)}")
        print("Estes diretórios são necessários para o funcionamento da aplicação.")
        cont = input("Deseja continuar mesmo assim? (s/n): ").lower()
        if cont != 's':
            print("Operação cancelada.")
            return
    
    # Verifica se o arquivo run.py existe
    if not (base_dir / "run.py").exists():
        print("[ERRO] O arquivo run.py não foi encontrado na pasta atual.")
        input("Pressione Enter para sair...")
        return
    
    # Cria o arquivo .spec para o PyInstaller
    print("Criando arquivo de configuração para o PyInstaller...")
    
    # Adiciona os diretórios de recursos
    data_entries = []
    if (base_dir / 'templates').exists():
        data_entries.append("('templates', 'templates')")
    if (base_dir / 'static').exists():
        data_entries.append("('static', 'static')")
    if (base_dir / 'utils').exists():
        data_entries.append("('utils', 'utils')")
    if (base_dir / '.env.example').exists():
        data_entries.append("('.env.example', '.')")
    
    # Verifica o ícone
    icon_path = base_dir / 'static' / 'images' / 'icon.ico'
    icon_statement = f"icon=r'{icon_path}'" if icon_path.exists() else "icon=None"
    
    # Conteúdo do arquivo .spec
    spec_content = f"""# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['run.py'],
    pathex=[],
    binaries=[],
    datas=[{', '.join(data_entries)}],
    hiddenimports=[
        'flask',
        'flask_cors',
        'flask_sqlalchemy',
        'werkzeug',
        'logging',
        'PyPDF2',
        'PIL',
        'google.generativeai',
        'reportlab',
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='DocMaster',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    {icon_statement},
)
"""
    
    spec_file = base_dir / "DocMaster.spec"
    with open(spec_file, 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    print("[OK] Arquivo DocMaster.spec criado")
    
    # Executa o PyInstaller
    print("Criando executável...(isso pode levar alguns minutos)")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "PyInstaller", "DocMaster.spec"],
            cwd=str(base_dir),
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print("[ERRO] Falha ao criar o executável.")
            print(f"Detalhes do erro:\n{result.stderr}")
            input("Pressione Enter para sair...")
            return
            
        print("[OK] Executável criado com sucesso!")
        exe_path = base_dir / "dist" / "DocMaster.exe"
        
        # Verifica se o executável realmente foi criado
        if exe_path.exists():
            print(f"O executável está localizado em: {exe_path}")
            
            # Cria um atalho na área de trabalho
            try:
                desktop_dir = os.path.join(os.path.expanduser("~"), "Desktop")
                
                # Verifica se o diretório "Desktop" existe (isso pode mudar dependendo da localização)
                if not os.path.exists(desktop_dir):
                    desktop_dir = os.path.join(os.path.expanduser("~"), "Área de Trabalho")
                
                if os.path.exists(desktop_dir):
                    # Cria um arquivo .bat que executa o executável
                    batch_content = f'@echo off\nstart "" "{exe_path}"'
                    batch_file = os.path.join(desktop_dir, "DocMaster.bat")
                    
                    with open(batch_file, 'w') as f:
                        f.write(batch_content)
                    
                    print(f"[OK] Atalho criado na área de trabalho: {batch_file}")
                    
                    # Instruções para o usuário
                    print("\nPara executar o DocMaster Pro, você pode:")
                    print(f"1. Clicar no atalho 'DocMaster' na área de trabalho")
                    print(f"2. Executar diretamente o arquivo: {exe_path}")
            except Exception as e:
                print(f"[AVISO] Não foi possível criar o atalho na área de trabalho: {e}")
                print(f"Você ainda pode executar diretamente o arquivo: {exe_path}")
        else:
            print("[AVISO] O arquivo executável não foi encontrado no local esperado.")
            
    except Exception as e:
        print(f"[ERRO] Exceção ao criar o executável: {e}")
        input("Pressione Enter para sair...")
        return
    
    # Perguntar se deseja executar o programa agora
    run_now = input("\nDeseja executar o DocMaster Pro agora? (s/n): ").lower()
    if run_now == 's':
        print("Iniciando o DocMaster Pro...")
        try:
            # Inicia o programa em um novo processo
            subprocess.Popen([str(exe_path)], creationflags=subprocess.CREATE_NEW_CONSOLE)
            print("DocMaster Pro iniciado!")
        except Exception as e:
            print(f"[ERRO] Não foi possível iniciar o programa: {e}")
    
    print("\nProcesso de criação do executável concluído!")
    input("Pressione Enter para sair...")

if __name__ == "__main__":
    main()