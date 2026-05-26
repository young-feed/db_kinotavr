FROM python:3.11-slim

# Устанавливаем postgresql-client, чтобы внутри контейнера была утилита pg_isready
RUN apt-get update && apt-get install -y postgresql-client && rm -rf /var/lib/apt/lists/*

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Сначала копируем зависимости и устанавливаем их (для кеширования слоев Docker)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем сам скрипт автонаполнения
COPY fill_db.py .

# Перед запуском скрипта в цикле проверяем готовность базы данных.
# Как только база ответит, запустится fill_db.py
CMD while ! pg_isready -h $DB_HOST -p 5432 -U $DB_USER; do sleep 1; done; python fill_db.py