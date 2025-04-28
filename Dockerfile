FROM python:3.13.0
EXPOSE 8000
WORKDIR /medieval
COPY . .
RUN pip install --upgrade pip wheel
RUN pip install --no-cache-dir -e .
RUN pybabel compile -d translations
CMD ["uvicorn", "medieval.main:APP", "--host", "0.0.0.0", "--workers", "2"]
