"""Utilities."""

import functools

from datetime import datetime
from enum import Enum
from gettext import gettext as _

import jinja2

from babel.numbers import format_number
from babel.support import Translations
from foreground import get_foreground
from starlette.exceptions import HTTPException
from starlette.responses import Response, RedirectResponse
from starlette.templating import Jinja2Templates
from rcssmin import cssmin
from rjsmin import jsmin


class Mode(Enum):
    """Site modes."""

    ART = 'art'
    IMAGE = 'image'


class ExtendedJinja2Templates(Jinja2Templates):
    """Jinja environment with extensions."""

    def get_env(self, directory):
        """Get environment with i18n extension."""
        return jinja2.Environment(
            loader=jinja2.FileSystemLoader(directory),
            autoescape=True,
            extensions=['jinja2.ext.i18n']
        )


#TEMPLATES = ExtendedJinja2Templates(directory='templates')

ENV = jinja2.Environment(
    loader=jinja2.FileSystemLoader("templates"),
    autoescape=True,
    extensions=['jinja2.ext.i18n']
)
TEMPLATES = Jinja2Templates(env=ENV)


METADATA_QUERY = """
    select *
    from site
    where active=true order by year_started
"""

SOURCE_COUNT_QUERY = """
    select count(*) as count
    from source
    join image on source.id=image.source_id
    join art_site on image.art_id=art_site.art_id
    where site_id=:site_id and source.hidden = false
"""


async def metadata(database):
    """Get site metadata."""
    sites = {}
    for data in await database.fetch_all(METADATA_QUERY):
        source_count = await database.fetch_one(SOURCE_COUNT_QUERY, dict(site_id=data['id']))
        sites[data['domain']] = dict(data, show_source_page=source_count['count'] > 0)
    return sites


def domain(request):
    """Get domain name from request."""
    if request.app.state.emulate:
        return request.app.state.emulate
    return request.url.hostname


def site(request, field):
    """Helper for site metadata."""
    value = request.app.state.metadata[domain(request)][field]
    if field == 'mode':
        return Mode(value)
    return value


async def favicon(_):
    """Favicon route."""
    return RedirectResponse('/assets/favicon.ico')


async def css(request):
    """CSS route."""
    return Response(
        cssmin(TEMPLATES.get_template('medieval.css').render(
            primary_color=site(request, 'primary_color'),
            foreground=get_foreground(site(request, 'primary_color')),
            domain=site(request, 'domain')
        )),
        media_type='text/css'
    )


async def javascript(_):
    """Javascript route."""
    return Response(
        jsmin(TEMPLATES.get_template('medieval.js').render()),
        media_type='text/javascript'
    )


def get_locales(request):
    """Get `accept-language` locales."""
    return [
        lang.split(';')[0][:2]
        for lang in request.headers.get('accept-language', '').split(',')
        if not lang.startswith('*') and lang != ''
    ] + ['en']


def get_menu(minimal=False, sources=True):
    """Get menu links."""
    links = [
        {'title': _('Home'), 'href': '/'},
    ]
    if not minimal:
        links += [
            {'title': _('Search'), 'href': '/search'},
            {'title': _('Tags'), 'href': '/tags'},
        ]
        if sources:
            links.append({'title': _('Sources'), 'href': '/sources'})
    else:
        links.append({'title': _('Gallery'), 'href': '/gallery'})
    links.append({'title': _('About'), 'href': '/about'})
    return links


async def template(request, filename, **kwargs):
    """Render a template response."""
    if domain(request) not in request.app.state.metadata:
        raise HTTPException(status_code=404)

    locales = get_locales(request)
    translations = Translations.load('translations', locales=locales)
    TEMPLATES.env.install_gettext_translations(translations)
    TEMPLATES.env.filters['format_number'] = functools.partial(format_number, locale=locales[0])

    return TEMPLATES.TemplateResponse(request, filename, dict(
        active=request.url.path,
        metadata=request.app.state.metadata[domain(request)],
        year_current=datetime.today().year,
        sites=request.app.state.metadata.values(),
        links=get_menu(site(request, 'minimal'), site(request, 'show_source_page')),
        **kwargs
    ))
