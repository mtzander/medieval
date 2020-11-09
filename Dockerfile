FROM python:3.9.1
EXPOSE 8000
WORKDIR /medieval
COPY . .
RUN pip3 install --upgrade pip wheel
RUN pip3 install --no-cache-dir -e .
RUN pybabel compile -d translations
CMD ["uvicorn", "medieval.main:APP", "--host", "0.0.0.0"]
