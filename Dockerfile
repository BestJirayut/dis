FROM python:3.12-slim

WORKDIR /app

# ติดตั้ง dependencies ก่อน เพื่อใช้ layer cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# คัดลอกซอร์สโค้ด
COPY . .

# Fly.io จะตรวจ health check ที่พอร์ตนี้
EXPOSE 8080

CMD ["python", "bot.py"]
