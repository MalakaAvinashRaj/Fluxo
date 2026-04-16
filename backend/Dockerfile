FROM python:3.11-slim

WORKDIR /app

# System deps needed for ChromaDB / numpy
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Sessions and Flutter build output are volume-mounted at runtime
RUN mkdir -p ./sessions ./flutter_output ./chroma_db

EXPOSE 8080

CMD ["python", "main.py"]
