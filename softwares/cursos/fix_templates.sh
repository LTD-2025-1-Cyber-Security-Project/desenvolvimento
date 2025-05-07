#!/bin/bash

# Criar a estrutura padrão do Flask
mkdir -p app/templates/errors
mkdir -p app/templates/auth
mkdir -p app/templates/courses
mkdir -p app/templates/quizzes
mkdir -p app/templates/admin

# Estrutura para arquivos estáticos
mkdir -p app/static/css
mkdir -p app/static/js
mkdir -p app/static/img
mkdir -p app/static/uploads/profile_pics
mkdir -p app/static/uploads/course_thumbnails
mkdir -p app/static/uploads/lesson_attachments

# Mover os templates para a localização correta (se existirem)
if [ -d "app/views/templates" ]; then
    echo "Movendo templates da pasta views/templates para templates..."
    cp -r app/views/templates/* app/templates/
    echo "Templates movidos com sucesso!"
else
    echo "Diretório app/views/templates não encontrado. Criando estrutura do zero."
fi

# Criar arquivos CSS e JS básicos se não existirem
if [ ! -f "app/static/css/style.css" ]; then
    echo "Criando arquivo CSS básico..."
    touch app/static/css/style.css
fi

if [ ! -f "app/static/js/main.js" ]; then
    echo "Criando arquivo JavaScript básico..."
    touch app/static/js/main.js
fi

echo "Estrutura de diretórios reorganizada com sucesso!"