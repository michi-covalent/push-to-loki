FROM python:3-slim AS builder
COPY . /app
WORKDIR /app
RUN pip install --target=/app -r requirements.txt

FROM gcr.io/distroless/python3
COPY --from=builder /app /app
ENTRYPOINT ["python", "/app/push.py"]
