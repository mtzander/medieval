# medieval

This project is a web application that powers several websites, including [Effigies & Brasses](https://effigiesandbrasses.com).

## Development

Preferably clone the repository, create a Python 3.9.x virtual environment, and install project in editable mode.

```bash
git clone https://github.com/mtzander/medieval.git
python39 -m venv <env-name>
source <env-name/bin/activate
pip install -e .
```

Create a configuration file named `.env` with content as follows.

```
DATABASE_URL=<postgresql-connection=string>
IMAGE_PATH=images
DEBUG=true
```

Launch development server with hot reload.

```bash
uvicorn medieval.main:APP --reload
```

## Deployment

Deploy into production with Docker. Configuration assumes that the database is populated and art images are in a directory called `images` relative to the code root.

```bash
docker build --rm -t medieval .
POSTGRES_PASSWORD=<password> docker-compose up -d
```

## Translation

Translatable strings are noted as follows:

| File | Notation | Note |
|------|----------|------|
| html | `{% trans %}text{% endtrans %}` |
| py | `_(text)` | `from gettext import gettext as _` |


Extract translation strings from templates and python code.

```bash
pybabel extract -F babel-mapping.ini -o translations/messages.pot ./
```

Add a new language based on message extraction.

```bash
pybabel init -d translations -l <ISO 639-1 code> -i translations/messages.pot
```

Compile all translations (this step is done automatically for deployments).

```bash
pybabel compile -d translations
```
