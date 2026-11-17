FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /srv

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app ./app

# 키와 설정은 이미지에 넣지 않는다. 실행할 때 환경변수(또는 --env-file)로 주입한다.
RUN useradd --create-home --uid 10001 appuser
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/ai/v1/health', timeout=2).status == 200 else 1)"

# 워커 1개: 메모리를 아끼기 위해. 요청은 async 로 처리한다.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
