FROM python:3.12-alpine
ARG INTEGRATION_COMMIT=local
LABEL org.opencontainers.image.revision=$INTEGRATION_COMMIT
WORKDIR /service
COPY tutor_engine/server.py ./
COPY OnlineJudge/ai_tutor/services/output_guard.py ./guard.py
COPY OnlineJudge/ai_tutor/ml/runtime.py ./classifier_runtime.py
COPY OnlineJudge/utils/bounded_http.py ./
USER 65534:65534
HEALTHCHECK --interval=10s --timeout=3s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/health', timeout=2)"
CMD ["python", "server.py"]
