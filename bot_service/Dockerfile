FROM python:3.11-slim

WORKDIR /PythonProject

COPY bot_service/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "-m", "bot_service.main"]