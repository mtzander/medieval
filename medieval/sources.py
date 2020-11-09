"""Sources route."""

import asyncio
from collections import defaultdict

from starlette.exceptions import HTTPException

from medieval.util import template, site


SOURCE_QUERY = """
    select distinct source.*
    from source
    join image on source.id=image.source_id
    join art_site on image.art_id=art_site.art_id
    where site_id=:site_id and source.hidden = false
    order by type, published_year
"""

AUTHOR_QUERY = """
    select distinct author.*, source_author.source_id
    from author
    join source_author on author.id=source_author.author_id
    join image on source_author.source_id=image.source_id
    join art_site on image.art_id=art_site.art_id
    where site_id=:site_id
"""


async def sources(request):
    """Fetch sources."""
    if site(request, 'minimal') or not site(request, 'show_source_page'):
        raise HTTPException(status_code=404)

    sources_, authors = await asyncio.gather(
        request.app.state.database.fetch_all(SOURCE_QUERY, dict(site_id=site(request, 'id'))),
        request.app.state.database.fetch_all(AUTHOR_QUERY, dict(site_id=site(request, 'id')))
    )

    authors_by_source = defaultdict(list)
    for author in authors:
        authors_by_source[author['source_id']].append(author)

    return await template(request, 'sources.html',
        sources=[
            dict(authors=authors_by_source.get(source['id']), **source)
            for source in sources_
        ]
    )
