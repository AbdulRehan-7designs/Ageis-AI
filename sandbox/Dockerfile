FROM python:3.11-slim
RUN useradd --create-home --uid 10001 sandbox
WORKDIR /sandbox
COPY runner.py .
RUN chown -R sandbox:sandbox /sandbox
USER sandbox
EXPOSE 8080
CMD ["python", "-I", "runner.py"]
