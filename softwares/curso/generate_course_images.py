#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Gerador de imagens SVG para cursos.
Este script gera imagens SVG para os cursos da plataforma EdTech IA & Cyber.
"""

import os
import svgwrite
import random
import math  # Importando o módulo math no escopo global
import colorsys
from pathlib import Path

# Configurações
OUTPUT_DIR = Path('app/views/static/img/courses')
WIDTH = 800
HEIGHT = 450
COLORS = {
    'ai': {
        'primary': '#1565c0',       # Azul escuro
        'secondary': '#42a5f5',     # Azul médio
        'accent': '#bbdefb',        # Azul claro
        'text': '#ffffff',          # Branco
        'highlight': '#ffeb3b'      # Amarelo
    },
    'cyber': {
        'primary': '#2e7d32',       # Verde escuro
        'secondary': '#66bb6a',     # Verde médio
        'accent': '#c8e6c9',        # Verde claro
        'text': '#ffffff',          # Branco
        'highlight': '#ff9800'      # Laranja
    }
}


def create_directory():
    """Cria o diretório de saída se não existir."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"Diretório criado: {OUTPUT_DIR}")


def generate_random_shapes(dwg, category, count=15):
    """Gera formas aleatórias para o fundo."""
    shapes = dwg.g()
    colors = COLORS[category]
    
    # Adiciona formas geométricas aleatórias
    for _ in range(count):
        # Tamanho aleatório
        size = random.randint(20, 100)
        x = random.randint(0, WIDTH)
        y = random.randint(0, HEIGHT)
        opacity = random.uniform(0.1, 0.3)
        shape_type = random.choice(['circle', 'rect', 'polygon'])
        
        if shape_type == 'circle':
            shapes.add(dwg.circle(center=(x, y), r=size/2, 
                                  fill=random.choice([colors['secondary'], colors['accent']]),
                                  fill_opacity=opacity))
        elif shape_type == 'rect':
            shapes.add(dwg.rect(insert=(x, y), size=(size, size),
                                fill=random.choice([colors['secondary'], colors['accent']]),
                                fill_opacity=opacity,
                                transform=f"rotate({random.randint(0, 45)}, {x}, {y})"))
        else:  # polygon
            points = []
            sides = random.randint(3, 6)
            for i in range(sides):
                angle = i * (360 / sides)
                rad = angle * (math.pi / 180)
                px = x + (size/2) * math.cos(rad)
                py = y + (size/2) * math.sin(rad)
                points.append((px, py))
            
            shapes.add(dwg.polygon(points=points,
                                 fill=random.choice([colors['secondary'], colors['accent']]),
                                 fill_opacity=opacity))
    
    return shapes


def create_ai_icon(dwg, x, y, size=100, color='#ffffff'):
    """Cria um ícone representando IA."""
    icon = dwg.g()
    
    # Círculo central representando um "cérebro" ou "nó central"
    icon.add(dwg.circle(center=(x, y), r=size/4, fill=color, fill_opacity=0.9))
    
    # Linhas e nós conectados (representando uma rede neural)
    for i in range(8):
        angle = i * (360 / 8)
        rad = angle * (math.pi / 180)
        end_x = x + (size/2) * math.cos(rad)
        end_y = y + (size/2) * math.sin(rad)
        
        # Linha de conexão
        icon.add(dwg.line(start=(x, y), end=(end_x, end_y), 
                        stroke=color, stroke_width=2, stroke_opacity=0.7))
        
        # Nó conectado
        icon.add(dwg.circle(center=(end_x, end_y), r=size/12, 
                          fill=color, fill_opacity=0.8))
    
    return icon


def create_cyber_icon(dwg, x, y, size=100, color='#ffffff'):
    """Cria um ícone representando Cybersegurança."""
    icon = dwg.g()
    
    # Escudo (base de segurança)
    shield_points = [
        (x, y - size/2),  # Topo
        (x + size/2, y - size/4),  # Direita superior
        (x + size/2, y + size/4),  # Direita inferior
        (x, y + size/2),  # Base
        (x - size/2, y + size/4),  # Esquerda inferior
        (x - size/2, y - size/4),  # Esquerda superior
    ]
    icon.add(dwg.polygon(points=shield_points, 
                       fill='none', stroke=color, stroke_width=3))
    
    # Cadeado dentro do escudo
    lock_x = x
    lock_y = y
    lock_size = size / 3
    
    # Base do cadeado
    icon.add(dwg.rect(insert=(lock_x - lock_size/2, lock_y),
                    size=(lock_size, lock_size),
                    rx=lock_size/5, ry=lock_size/5,
                    fill=color, fill_opacity=0.8))
    
    # Arco do cadeado
    arc_radius = lock_size / 2
    icon.add(dwg.path(d=f"M{lock_x - arc_radius/2},{lock_y} " + 
                      f"A{arc_radius/2},{arc_radius/2} 0 1,1 {lock_x + arc_radius/2},{lock_y}",
                    fill="none", stroke=color, stroke_width=3))
    
    return icon


def generate_course_image(category, course_name):
    """Gera uma imagem SVG para um curso específico."""
    filename = f"{category}-{course_name}.svg"
    filepath = os.path.join(OUTPUT_DIR, filename)
    
    # Configurações de cores
    colors = COLORS[category]
    
    # Cria o desenho SVG
    dwg = svgwrite.Drawing(filepath, size=(f"{WIDTH}px", f"{HEIGHT}px"))
    
    # Adiciona um fundo
    dwg.add(dwg.rect(insert=(0, 0), size=('100%', '100%'), 
                  fill=colors['primary']))
    
    # Adiciona um gradiente de fundo
    gradient = dwg.defs.add(dwg.linearGradient(id=f"{category}_gradient", 
                                              x1=0, y1=0, x2=1, y2=1))
    gradient.add_stop_color(offset='0%', color=colors['primary'], opacity=1)
    gradient.add_stop_color(offset='100%', color=colors['secondary'], opacity=0.7)
    
    dwg.add(dwg.rect(insert=(0, 0), size=('100%', '100%'), 
                  fill=f"url(#{category}_gradient)"))
    
    # Adiciona formas aleatórias para o fundo
    shapes = generate_random_shapes(dwg, category)
    dwg.add(shapes)
    
    # Adiciona um ícone apropriado para a categoria
    if category == 'ai':
        icon = create_ai_icon(dwg, WIDTH/2, HEIGHT/2, size=HEIGHT/2, color=colors['text'])
    else:  # cyber
        icon = create_cyber_icon(dwg, WIDTH/2, HEIGHT/2, size=HEIGHT/2, color=colors['text'])
        
    dwg.add(icon)
    
    # Adiciona o nome do curso
    # Converte o nome do curso para formato legível
    display_name = course_name.replace('-', ' ').title()
    
    # Texto do título
    title = dwg.text(display_name, insert=(WIDTH/2, HEIGHT - 60),
                  font_family="Arial, sans-serif", font_size=40,
                  font_weight="bold", fill=colors['text'],
                  text_anchor="middle")
    
    # Adiciona um contorno ao título para melhor legibilidade
    title_shadow = dwg.text(display_name, insert=(WIDTH/2, HEIGHT - 60),
                         font_family="Arial, sans-serif", font_size=40,
                         font_weight="bold", fill="none", stroke=colors['primary'],
                         stroke_width=2, text_anchor="middle")
    
    dwg.add(title_shadow)
    dwg.add(title)
    
    # Salva o arquivo SVG
    dwg.save()
    print(f"Imagem criada: {filepath}")


def generate_course_hero():
    """Gera uma imagem de hero para a página inicial de cursos."""
    filename = "course-hero.svg"
    filepath = os.path.join(OUTPUT_DIR, filename)
    
    # Cria o desenho SVG
    dwg = svgwrite.Drawing(filepath, size=(f"{WIDTH}px", f"{HEIGHT}px"))
    
    # Define um gradiente para o fundo
    gradient = dwg.defs.add(dwg.linearGradient(id="hero_gradient", 
                                              x1=0, y1=0, x2=1, y2=1))
    gradient.add_stop_color(offset='0%', color="#1a237e", opacity=1)  # Azul profundo
    gradient.add_stop_color(offset='50%', color="#3949ab", opacity=1)  # Azul médio
    gradient.add_stop_color(offset='100%', color="#1b5e20", opacity=1)  # Verde profundo
    
    # Adiciona o fundo com gradiente
    dwg.add(dwg.rect(insert=(0, 0), size=('100%', '100%'), 
                  fill="url(#hero_gradient)"))
    
    # Adiciona padrão de grid (representando tecnologia/digital)
    grid = dwg.g(id='grid', stroke="#ffffff", stroke_width=0.5, stroke_opacity=0.2)
    
    # Linhas horizontais
    for y in range(0, HEIGHT, 40):
        grid.add(dwg.line(start=(0, y), end=(WIDTH, y)))
    
    # Linhas verticais
    for x in range(0, WIDTH, 40):
        grid.add(dwg.line(start=(x, 0), end=(x, HEIGHT)))
    
    dwg.add(grid)
    
    # Adiciona círculos e pontos conectados (representando rede/dados)
    network = dwg.g(id='network')
    
    # Cria nós de rede
    nodes = []
    for _ in range(15):
        x = random.randint(WIDTH//4, 3*WIDTH//4)
        y = random.randint(HEIGHT//4, 3*HEIGHT//4)
        r = random.randint(3, 8)
        nodes.append((x, y, r))
        network.add(dwg.circle(center=(x, y), r=r, 
                             fill="#ffffff", fill_opacity=random.uniform(0.5, 0.9)))
    
    # Conecta alguns nós com linhas
    for i in range(len(nodes)):
        for j in range(i+1, len(nodes)):
            # Conecta aproximadamente 30% dos nós
            if random.random() < 0.3:
                x1, y1, _ = nodes[i]
                x2, y2, _ = nodes[j]
                # Calcula a distância
                dist = math.sqrt((x2-x1)**2 + (y2-y1)**2)
                # Só conecta se estiverem razoavelmente próximos
                if dist < 200:
                    network.add(dwg.line(start=(x1, y1), end=(x2, y2),
                                       stroke="#ffffff", stroke_width=1, 
                                       stroke_opacity=0.4))
    
    dwg.add(network)
    
    # Adiciona o título
    title_text = "Aprenda IA & Cybersegurança"
    title = dwg.text(title_text, insert=(WIDTH/2, HEIGHT/2 - 20),
                  font_family="Arial, sans-serif", font_size=48,
                  font_weight="bold", fill="#ffffff",
                  text_anchor="middle")
    
    # Adiciona sombra/contorno para melhor legibilidade
    title_shadow = dwg.text(title_text, insert=(WIDTH/2, HEIGHT/2 - 20),
                         font_family="Arial, sans-serif", font_size=48,
                         font_weight="bold", fill="none", 
                         stroke="#000000", stroke_width=2, stroke_opacity=0.5,
                         text_anchor="middle")
    
    dwg.add(title_shadow)
    dwg.add(title)
    
    # Adiciona subtítulo
    subtitle_text = "Trilhas de aprendizado para profissionais municipais"
    subtitle = dwg.text(subtitle_text, insert=(WIDTH/2, HEIGHT/2 + 40),
                     font_family="Arial, sans-serif", font_size=24,
                     fill="#ffffff", fill_opacity=0.9,
                     text_anchor="middle")
    
    dwg.add(subtitle)
    
    # Salva o arquivo SVG
    dwg.save()
    print(f"Imagem hero criada: {filepath}")


def create_jpg_version(svg_path):
    """Cria uma versão JPG do arquivo SVG."""
    try:
        from cairosvg import svg2png
        from PIL import Image
        import io
        
        # Obtém o nome do arquivo sem extensão
        basename = os.path.basename(svg_path)
        filename_without_ext = os.path.splitext(basename)[0]
        jpg_path = os.path.join(OUTPUT_DIR, f"{filename_without_ext}.jpg")
        
        # Converte SVG para PNG em memória
        png_data = svg2png(url=svg_path, output_width=WIDTH, output_height=HEIGHT)
        
        # Converte PNG para JPG
        image = Image.open(io.BytesIO(png_data))
        rgb_image = image.convert('RGB')
        rgb_image.save(jpg_path, 'JPEG', quality=95)
        
        print(f"Versão JPG criada: {jpg_path}")
        return True
        
    except ImportError:
        print("Aviso: As bibliotecas 'cairosvg' e/ou 'PIL' não estão instaladas.")
        print("Para criar versões JPG, instale-as com: pip install cairosvg pillow")
        return False


def main():
    """Função principal que gera todas as imagens."""
    # Cria o diretório de saída
    create_directory()
    
    # Lista de cursos a serem gerados
    ai_courses = [
        'fundamentos',
        'machine-learning',
        'aplicacoes',
        'nlp',
        'projetos',
        'etica'
    ]
    
    cyber_courses = [
        'fundamentos',
        'ataques',
        'redes',
        'dados',
        'incidentes',
        'forense'
    ]
    
    # Gera imagens para cursos de IA
    for course in ai_courses:
        generate_course_image('ai', course)
    
    # Gera imagens para cursos de Cybersegurança
    for course in cyber_courses:
        generate_course_image('cyber', course)
    
    # Gera imagem de hero
    generate_course_hero()
    
    # Tenta gerar versões JPG
    try:
        print("\nTentando gerar versões JPG dos arquivos SVG...")
        
        # Verifica se temos as bibliotecas necessárias
        for filename in os.listdir(OUTPUT_DIR):
            if filename.endswith('.svg'):
                svg_path = os.path.join(OUTPUT_DIR, filename)
                create_jpg_version(svg_path)
    except Exception as e:
        print(f"Erro ao gerar versões JPG: {str(e)}")
        print("Continuando apenas com as versões SVG.")
    
    print("\nGeração de imagens concluída!")


if __name__ == '__main__':
    # Verifica se a biblioteca svgwrite está instalada
    try:
        import svgwrite
    except ImportError:
        print("A biblioteca 'svgwrite' não está instalada.")
        print("Por favor, instale-a usando: pip install svgwrite")
        exit(1)
    
    main()