FROM python:3.9

# Установите рабочий каталог
WORKDIR /app

# Копируйте файлы проекта
COPY . /app/

# Установите зависимости
RUN pip install -r requirements.txt

# Выполните collectstatic
RUN python manage.py collectstatic --noinput

# Запустите сервер
CMD ["python", "manage.py", "runserver", "127.0.0.1:8000"]