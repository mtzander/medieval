"""Home route."""

import asyncio
import time

from medieval.util import template, site


AOTD_QUERY = """
    select
        art_id, image.id, image.folio, image.rights, image.attribution,
        art.name, art.shelfmark, art.year_start, art.year_end,
        country.name as country, medium.name as medium
    from (
        select
            row_number() over (
                partition by image.art_id
                order by representative desc nulls last
            ) as number,
            image.art_id, image.id, folio, representative,
            source.rights, source.attribution
        from image
        join art_site on image.art_id=art_site.art_id
        left join source on image.source_id=source.id
        where art_site.site_id=:site_id and source.rights=true
    ) as image
    join art on image.art_id=art.id
    join place on art.place_id=place.id
    join country on place.country_id=country.id
    left join medium on medium.id=art.medium_id
    where image.number = 1
    order by random() limit 1
"""

RECENT_QUERY = """
    select
        art.id, medium.name as medium, art.name, year_start,
        year_end, shelfmark, country.name as country
    from art join art_site on art.id=art_site.art_id
    join place on art.place_id=place.id
    join country on place.country_id=country.id
    left join medium on art.medium_id=medium.id
    where art_site.site_id=:site_id
    order by art.id desc limit 10
"""

IMAGE_COUNT_QUERY = """
    select count(*) as count from image
    join art_site on image.art_id=art_site.art_id
    where art_site.site_id=:site_id
"""

ART_COUNT_QUERY = """
    select count(*) as count from art_site
    where art_site.site_id=:site_id
"""

COUNTRY_COUNT_QUERY = """
    select count(distinct place.country_id) as count
    from image join art on image.art_id=art.id
    join place on art.place_id=place.id
    join art_site on image.art_id=art_site.art_id
    where art_site.site_id=:site_id
"""


async def home(request):
    """Fetch home page."""
    await request.app.state.database.execute(
        "select setseed(:seed)",
        values=dict(seed=time.localtime().tm_yday / 366)
    )
    values = dict(site_id=site(request, 'id'))
    aotd, recent, image_count, art_count, country_count = await asyncio.gather(
        request.app.state.database.fetch_one(AOTD_QUERY, values=values),
        request.app.state.database.fetch_all(RECENT_QUERY, values=values),
        request.app.state.database.fetch_one(IMAGE_COUNT_QUERY, values=values),
        request.app.state.database.fetch_one(ART_COUNT_QUERY, values=values),
        request.app.state.database.fetch_one(COUNTRY_COUNT_QUERY, values=values)
    )
    return await template(request, 'home.html',
        aotd=aotd,
        recent=recent,
        image_count=image_count['count'],
        art_count=art_count['count'],
        country_count=country_count['count']
    )
