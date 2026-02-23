#!/bin/bash
set -e # Упадёт, в случае ошибки, дальше не пойдёт

git pull # Обновит код репозитория
. venv/bin/activate
pip install -r requirements.txt # Установит библиотеки для Python
npm install # Установит библиотеки для Node.js

systemctl restart star-burger-node # Пересоберёт JS-код(star-burger-node.service запускает сборку Parcel как в примере выше)
python ./manage.py collectstatic --noinput # Пересоберёт статику Django
python ./manage.py makemigrations --dry-run --check 
python ./manage.py migrate --noinput

systemctl restart star-burger-py # Перезапустит сервис в котором запущено django-приложение
echo Website successfully deployed # Сообщит об успешном завершении деплоя
deactivate
