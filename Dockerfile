FROM python:3.12-slim
WORKDIR /app
COPY . /app
# Aquí usará tu requirements.txt original para instalar todo
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 8080
CMD ["python", "app.py"]
