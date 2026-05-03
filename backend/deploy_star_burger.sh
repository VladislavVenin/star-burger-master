#!/bin/bash
set -e # Упадёт, в случае ошибки, дальше не пойдёт

docker compose down
git pull # Обновит код репозитория
docker image rm sb_frontend
docker build -t sb_frontend ./frontend # Пересоберёт фронтенд
docker image rm sb_app
docker build -t sb_app . # Соберёт новый образ с новыми библиотеками
docker compose up -d # Соберёт статику в отдельную папку и запустит сервер
docker compose exec web python ./manage.py makemigrations --dry-run --check
docker compose exec web python ./manage.py migrate --noinput

echo Website successfully deployed # Сообщит об успешном завершении деплоя
