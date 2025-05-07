#!/bin/bash

# Criar estrutura de diretórios para templates
mkdir -p app/views/templates/errors
mkdir -p app/views/templates/auth
mkdir -p app/views/templates/courses
mkdir -p app/views/templates/quizzes
mkdir -p app/views/templates/admin

# Criar estrutura de diretórios para arquivos estáticos
mkdir -p app/static/css
mkdir -p app/static/js
mkdir -p app/static/img
mkdir -p app/static/uploads/profile_pics
mkdir -p app/static/uploads/course_thumbnails
mkdir -p app/static/uploads/lesson_attachments

# Criar os arquivos CSS e JS básicos
touch app/static/css/style.css
touch app/static/js/main.js

# Copiar os templates criados para o local correto
# Você precisará fazer isso manualmente ou criar os arquivos nos locais corretos