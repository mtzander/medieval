"""Art route."""

import asyncio
import json

from starlette.exceptions import HTTPException

from medieval.util import site, template, Mode


ART_TAG_QUERY = """
    select tag.id, tag.name as value
    from tag
    join art_tag on tag.id=art_tag.tag_id
    where art_id=:id
"""

IMAGE_TAG_QUERY = """
    select tag.id, tag.name as value
    from tag
    join image_tag on tag.id=image_tag.tag_id
    join image on image_tag.image_id=image.id
    where image.id=:id
"""

IMAGE_QUERY = """
    select
        image.id, folio, page_location, image.url, image.page_url,
        source.attribution, source.rights
    from image
    left join source on image.source_id=source.id
    where
"""

ART_QUERY = """
    select
        art.id, art.name, url, year_start, year_end, latitude, longitude,
        shelfmark, inventory_number, title, position,
        institution.name as institution_name, institution.id as institution_id,
        form.name as form_name, form.id as form_id,
        artist.name as artist_name, artist.id as artist_id,
        medium.name as medium_name, medium.id as medium_id
    from art
    join art_site on art.id=art_site.art_id
    left join institution on art.institution_id=institution.id
    left join artist on art.artist_id=artist.id
    left join medium on art.medium_id=medium.id
    left join form on art.form_id=form.id
    where art.id=:id and art_site.site_id=:site_id
"""

RELATED_IMAGE_QUERY = """
    select image.id, folio, source.attribution, source.rights
    from image
    left join source on image.source_id=source.id
    where art_id=:id and image.id<>:image_id
"""

PLACE_QUERY = """
    select place.*, country.name as country_name, country.id as country_id
    from art
    join place on art.place_id=place.id
    join country on place.country_id=country.id
    where art.id=:id
"""

COSTUME_QUERY = """
    select costume.id, costume.name
    from art_costume
    join costume on art_costume.costume_id=costume.id
    where art_id=:id
"""

GENDER_QUERY = """
    select gender.id, gender.name
    from art_gender
    join gender on art_gender.gender_id=gender.id
    where art_id=:id
"""

SOURCE_QUERY = """
    select source.*, license.name as license_name, license.url as license_url
    from image
    join source on image.source_id=source.id
    left join license on source.license_id=license.id
    where image.id=:image_id and source.hidden = false
"""

AUTHOR_QUERY = """
    select author.*
    from image
    join source on image.source_id=source.id
    join source_author on source_author.source_id=source.id
    join author on author.id=source_author.author_id
    where image.id=:image_id
"""


async def get_image(request):
    """Get representative image."""
    if 'image_id' in request.path_params:
        query = f"{IMAGE_QUERY} image.id=:image_id"
        return await request.app.state.database.fetch_one(query, dict(image_id=request.path_params['image_id']))
    query = f"{IMAGE_QUERY} art_id=:id order by representative desc nulls last limit 1"
    return await request.app.state.database.fetch_one(query, dict(id=request.path_params['art_id']))


async def art(request):
    """Fetch art."""
    art_id = request.path_params['art_id']
    mode = site(request, 'mode')
    image = await get_image(request)
    tag_query = ART_TAG_QUERY if site(request, 'mode') is Mode.ART else IMAGE_TAG_QUERY
    item, related, place, tags, costumes, genders, source, authors = await asyncio.gather(
        request.app.state.database.fetch_one(ART_QUERY, dict(id=art_id, site_id=site(request, 'id'))),
        request.app.state.database.fetch_all(RELATED_IMAGE_QUERY, dict(id=art_id, image_id=image['id'])),
        request.app.state.database.fetch_one(PLACE_QUERY, dict(id=art_id)),
        request.app.state.database.fetch_all(tag_query, dict(id=art_id if mode is Mode.ART else image['id'])),
        request.app.state.database.fetch_all(COSTUME_QUERY, dict(id=art_id)),
        request.app.state.database.fetch_all(GENDER_QUERY, dict(id=art_id)),
        request.app.state.database.fetch_one(SOURCE_QUERY, dict(image_id=image['id'])),
        request.app.state.database.fetch_all(AUTHOR_QUERY, dict(image_id=image['id']))
    )

    if not item:
        raise HTTPException(status_code=404)

    return await template(request, 'art.html',
        art=item,
        image=image,
        source=dict(source, authors=authors) if source else None,
        costumes=costumes,
        genders=genders,
        place=place,
        related=related,
        tags=json.dumps([dict(t) for t in tags])
    )
