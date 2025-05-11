#!/usr/bin/env python3
"""
Aplicativo de teste mínimo para verificar dependências do NexusInfo.
Este é um teste extremamente simplificado apenas para verificar
se as bibliotecas básicas funcionam.
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox

print("Iniciando teste mínimo...")
print(f"Python versão: {sys.version}")
print(f"Tkinter versão: {tk.TkVersion}")
print("Verificando dependências...")

# Verificar ttkbootstrap
try:
    import ttkbootstrap
    print("- ttkbootstrap: INSTALADO")
except ImportError:
    print("- ttkbootstrap: NÃO ENCONTRADO")

# Verificar API Gemini
try:
    from google import genai
    print("- google-genai (novo SDK): INSTALADO")
except ImportError:
    try:
        import google.generativeai
        print("- google.generativeai (SDK antigo): INSTALADO")
    except ImportError:
        print("- API Gemini: NÃO ENCONTRADA")

# Verificar Pillow
try:
    from PIL import Image
    print("- Pillow: INSTALADO")
except ImportError:
    print("- Pillow: NÃO ENCONTRADO")

# Função básica para verificar o Tkinter
def test_tkinter():
    # Criar janela
    root = tk.Tk()
    root.title("Teste Básico do Tkinter")
    root.geometry("400x300")
    
    # Adicionar um rótulo
    label = ttk.Label(root, text="Se você consegue ver esta janela, o Tkinter está funcionando!")
    label.pack(pady=20)
    
    # Botão para testar interação
    btn = ttk.Button(root, text="Clique para fechar", command=root.destroy)
    btn.pack(pady=10)
    
    # Iniciar loop
    print("Abrindo janela de teste Tkinter...")
    root.mainloop()
    print("Janela fechada.")

# Verificar se estamos no script principal
if __name__ == "__main__":
    print("\nIniciando teste básico do Tkinter...")
    test_tkinter()
    print("Teste concluído.")