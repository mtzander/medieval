"""Tag routes."""

import asyncpg

from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse

from medieval.util import template, site, Mode


TAGS_BY_ART = """
    select tag.id, tag.name, count(art_site.art_id) as count from tag
    join art_tag on tag.id=art_tag.tag_id
    join art_site on art_site.art_id=art_tag.art_id
    where art_site.site_id=:site_id
    group by tag.id, tag.name
    order by tag.name
"""

TAGS_BY_IMAGE = """
    select tag.id, tag.name, count(art_site.art_id) as count from tag
    join image_tag on tag.id=image_tag.tag_id
    join image on image_tag.image_id=image.id
    join art_site on art_site.art_id=image.art_id
    where art_site.site_id=:site_id
    group by tag.id, tag.name
    order by tag.name
"""

TAG_ART_SUGGEST = """
    select distinct tag.id, tag.name as value from tag
    join art_tag on tag.id=art_tag.tag_id
    join art_site on art_site.art_id=art_tag.art_id
    where name ilike :input and art_site.site_id=:site_id
"""

TAG_IMAGE_SUGGEST = """
    select distinct tag.id, tag.name as value from tag
    join image_tag on tag.id=image_tag.tag_id
    join image on image_tag.image_id=image.id
    join art_site on art_site.art_id=image.art_id
    where name ilike :input and art_site.site_id=:site_id
"""

TAG_SUGGEST = """
    select distinct tag.id, tag.name as value
    from tag
    where name ilike :input
"""


async def tags(request):
    """Fetch all tags."""
    if site(request, 'minimal'):
        raise HTTPException(status_code=404)
    query = TAGS_BY_ART if site(request, 'mode') is Mode.ART else TAGS_BY_IMAGE
    return await template(request, 'tags.html',
        tags=[dict(r) for r in await request.app.state.database.fetch_all(query, dict(site_id=site(request, 'id')))]
    )


def get_tag_by_name(database, name):
    """Get a tag ID by name."""
    return database.fetch_one("select id from tag where name=:name", dict(name=name))


async def tag_add(request):
    """Add a tag."""
    data = await request.form()
    mode = data['mode']
    tag = await get_tag_by_name(request.app.state.database, data['name'])
    if not tag:
        await request.app.state.database.execute("insert into tag (name) values(:name)", dict(name=data['name']))
        tag = await get_tag_by_name(request.app.state.database, data['name'])
    try:
        query = f"insert into {mode}_tag ({mode}_id, tag_id) values(:id, :tag_id)"
        await request.app.state.database.execute(query, dict(id=int(data['id']), tag_id=tag['id']))
    except asyncpg.exceptions.UniqueViolationError:
        pass
    return JSONResponse(tag['id'])


async def tag_remove(request):
    """Remove a tag."""
    data = await request.form()
    tag = await get_tag_by_name(request.app.state.database, data['name'])
    mode = Mode(data['mode'])
    if mode is Mode.ART:
        sel = "art_tag where art_id=:id"
    elif mode is Mode.IMAGE:
        sel = "image_tag where image_id=:id"
    query = f"delete from {sel} and tag_id=:tag_id"
    await request.app.state.database.execute(query, dict(id=int(data['id']), tag_id=tag['id']))
    return JSONResponse()


async def tag_suggest(request):
    """Get suggested tags based on partial input."""
    values = dict(input='{}%'.format(request.path_params['input']))
    suggestions = await request.app.state.database.fetch_all(TAG_SUGGEST, values)
    return JSONResponse([dict(s) for s in suggestions])
