"""Search route."""

import asyncio
import json

from babel.support import Locale
from natsort import natsorted

from medieval.util import site, template, get_locales, Mode


COUNTRY_QUERY = """
    select country.id, country.code, country.name from country
    join place on country.id=place.country_id
    join art on art.place_id=place.id
    join art_site on art_site.art_id=art.id
    where art_site.site_id=:site_id
    group by country.id, country.code, country.name
    order by country.name
"""

INSTITUTION_QUERY = """
    select institution.id, institution.name from institution
    join art on art.institution_id=institution.id
    join art_site on art_site.art_id=art.id
    where art_site.site_id=:site_id
    group by institution.id, institution.name
    order by institution.name
"""

MEDIUM_QUERY = """
    select medium.id, medium.name from medium
    join art on art.medium_id=medium.id
    join art_site on art_site.art_id=art.id
    where art_site.site_id=:site_id
    group by medium.id, medium.name
    order by medium.name
"""

ART_QUERY = """
    select art.id, name, shelfmark, year_start, year_end from art
    join art_site on art_site.art_id=art.id
    where art_site.site_id=:site_id and art.name is not null
    order by shelfmark, name, year_start
"""

ATTR_BY_ART_QUERY = """
    select {attr}.id, {attr}.name from {attr}
    join art_{attr} on {attr}.id=art_{attr}.{attr}_id
    join art_site on art_{attr}.art_id=art_site.art_id
    where art_site.site_id=:site_id
    group by {attr}.id, {attr}.name
    order by {attr}.name
"""

ATTR_BY_IMAGE_QUERY = """
    select {attr}.id, {attr}.name from {attr}
    join image_{attr} on {attr}.id=image_{attr}.{attr}_id
    join image on image_{attr}.image_id=image.id
    join art_site on image.art_id=art_site.art_id
    where art_site.site_id=:site_id
    group by {attr}.id, {attr}.name
    order by {attr}.name
"""

REPR_ART_QUERY = """
    select image.art_id as key, image.id, source.attribution, source.rights from (
        select
            row_number() over (
                partition by art_id
                order by representative desc nulls last
            ) as number,
            art_id, id, source_id
        from image
        where art_id = any(:ids)
    ) as image
    left join source on image.source_id=source.id
    where image.number=1
"""

REPR_IMAGE_QUERY = """
    select image.id as key, image.id, source.attribution, source.rights
    from image
    left join source on image.source_id=source.id
    where image.id = any(:ids)
"""

SEARCH_RESULT_QUERY = """
    select
        distinct {mode}.id as key, art_site.art_id, shelfmark,
        year_start, year_end, country.name as country,
        medium.name as medium, form.name as form,
        art.name, latitude, longitude
    from {joins}
    {where}
    order by year_start, art_id, {mode}.id
    limit {limit} offset {offset}
"""

SEARCH_COUNT_QUERY = """
    select count(distinct {mode}.id) as count
    from {joins}
    {where}
"""

TAG_NAME_QUERY = """
    select id, name as value
    from tag
    where id = any(:ids)
"""


def get_clause(field, comparison='eq'):
    """Get SQL comparison."""
    if comparison == 'eq':
        return f'{field} = :{field}'
    if comparison == 'in':
        return f'{field} = any(:{field})'
    if comparison == 'gte':
        return f'{field} >= :{field}'
    if comparison == 'lte':
        return f'{field} <= :{field}'
    return None


def get_param_list(params, field):
    """Get multi-valued field."""
    for value in params.getlist(field):
        yield from value.split(',')


def builder(params, site_id, mode): # pylint: disable=too-many-branches
    """Build search query parts."""
    joins = [
        "join art_site on art.id=art_site.art_id",
        "join image on art.id=image.art_id",
        "left join place on art.place_id=place.id",
        "left join country on place.country_id=country.id",
        "left join medium on art.medium_id=medium.id",
        "left join form on art.form_id=form.id"
    ]
    values = dict(site_id=site_id)
    clauses = ['site_id = :site_id']
    if 'year_start' in params and params['year_start']:
        values['year_start'] = int(params['year_start'])
        if 'year_end' in params and params['year_end']:
            values['year_end'] = int(params['year_end'])
            clauses.append(get_clause('year_end', 'lte'))
            clauses.append(get_clause('year_start', 'gte'))
        else:
            clauses.append(get_clause('year_start'))
    if 'country' in params:
        values['country_id'] = list(map(int, get_param_list(params, 'country')))
        clauses.append(get_clause('country_id', 'in'))
    if 'costume' in params:
        values['costume_id'] = list(map(int, get_param_list(params, 'costume')))
        clauses.append(get_clause('costume_id', 'in'))
        if mode is Mode.IMAGE:
            joins.append("join image_costume on image.id=image_costume.image_id")
        else:
            joins.append("join art_costume on art.id=art_costume.art_id")
    if 'gender' in params:
        values['gender_id'] = list(map(int, get_param_list(params, 'gender')))
        clauses.append(get_clause('gender_id', 'in'))
        if mode is Mode.IMAGE:
            joins.append("join image_gender on image.id=image_gender.image_id")
        else:
            joins.append("join art_gender on art.id=art_gender.art_id")
    for field in ['institution', 'medium', 'form', 'artist', 'source', 'place']:
        if field in params and params[field]:
            values[f'{field}_id'] = int(params[field])
            clauses.append(get_clause(f'{field}_id'))
    if 'art' in params and params['art']:
        values['art_id'] = int(params['art'])
        clauses.append('art.id = :art_id')
    if 'tag' in params and params['tag']:
        values['tag_id'] = list(map(int, params['tag'].split(',')))
        clauses.append(get_clause('tag_id', 'in'))
        if mode is Mode.IMAGE:
            joins.append("join image_tag on image.id=image_tag.image_id")
        else:
            joins.append("join art_tag on art.id=art_tag.art_id")
    if 'map' in params:
        clauses.append("latitude is not null and longitude is not null")
    where = ' and '.join(clauses)
    if where:
        where = f'where {where}'
    return 'art {}'.format(' '.join(joins)), where, values


def get_attr_query(mode, attr):
    """Get query for many-to-many attribute."""
    if mode is Mode.ART:
        return ATTR_BY_ART_QUERY.format(attr=attr)
    return ATTR_BY_IMAGE_QUERY.format(attr=attr)


async def country_choices(request, countries):
    """Localized country choices."""
    languages = get_locales(request)
    return natsorted([
        dict(country, name=Locale(languages[0]).territories.get(
            country['code'], country['name']
        ))
        for country in countries
    ], key=lambda country: country['name'])


async def update_tag_values(request, values):
    """Update tag values with tag name for display."""
    if 'tag_id' in values:
        values['tag_id'] = json.dumps([
            dict(tag)
            for tag in await request.app.state.database.fetch_all(
                TAG_NAME_QUERY, dict(ids=values['tag_id'])
            )
        ])
    return values


async def append_representative_image(request, results, mode):
    """Append a representative image to each result."""
    reps = {}
    if 'map' not in request.query_params:
        query = REPR_ART_QUERY if mode is Mode.ART else REPR_IMAGE_QUERY
        ids = [r['key'] for r in results]
        for image in await request.app.state.database.fetch_all(query, dict(ids=ids)):
            reps[image['key']] = image
    return [
        dict(result, image=reps.get(result['key']))
        for result in results
    ]


async def search(request): # pylint: disable=too-many-locals
    """Fetch search form and results."""
    limit = 20
    page = int(request.query_params.get('page', 1))
    offset = (page - 1) * limit
    mode = site(request, 'mode')
    search_mode = mode
    site_id = site(request, 'id')
    if request.query_params.get('source'):
        search_mode = Mode.IMAGE
    if 'map' in request.query_params:
        search_mode = Mode.ART
        limit = None
        offset = None
    site_value = dict(site_id=site_id)
    joins, where, values = builder(request.query_params, site_id, mode)
    countries, costumes, genders, institutions, mediums, art_options, results, count = await asyncio.gather(
        request.app.state.database.fetch_all(COUNTRY_QUERY, site_value),
        request.app.state.database.fetch_all(get_attr_query(mode, 'costume'), site_value),
        request.app.state.database.fetch_all(get_attr_query(mode, 'gender'), site_value),
        request.app.state.database.fetch_all(INSTITUTION_QUERY, site_value),
        request.app.state.database.fetch_all(MEDIUM_QUERY, site_value),
        request.app.state.database.fetch_all(ART_QUERY, site_value),
        request.app.state.database.fetch_all(SEARCH_RESULT_QUERY.format(
            joins=joins,
            where=where,
            limit=limit if limit else 'null',
            offset=offset if offset else 'null',
            mode=search_mode.value
        ), values),
        request.app.state.database.fetch_one(SEARCH_COUNT_QUERY.format(
            joins=joins,
            where=where,
            mode=search_mode.value
        ), values)
    )
    countries, results, values = await asyncio.gather(
        country_choices(request, countries),
        append_representative_image(request, results, search_mode),
        update_tag_values(request, values)
    )
    return await template(request, 'search.html',
        countries=countries,
        costumes=costumes,
        genders=genders,
        institutions=institutions,
        mediums=mediums,
        art=art_options,
        results=results,
        count=count['count'],
        page=page,
        pages=round(count['count']/limit) if limit else None,
        query=request.url.remove_query_params(['page']).query,
        values=values,
        map='map' in request.query_params
    )
