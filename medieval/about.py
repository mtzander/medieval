"""About route."""

from medieval.util import template

async def about(request):
    """Fetch the `About` page."""
    return await template(request, 'about.html')
