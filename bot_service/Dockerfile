FROM python:3.11-slim

WORKDIR /PythonProject

# сначала скопируем requirements для кеша
COPY bot_service/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# копируем весь проект внутрь контейнера
COPY . .

CMD ["python", "-m", "bot_service.main"]