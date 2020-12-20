"""Image route."""

import asyncio
import io

from PIL import Image
from starlette.exceptions import HTTPException
from starlette.responses import Response


def image_data(path, size=None, fmt='JPEG'):
    """Get image bytes for requested size."""
    try:
        img = Image.open(path)
    except FileNotFoundError:
        return None
    data = io.BytesIO()
    if size:
        ratio = size / max(img.height, img.width)
        img = img.resize((int(img.width * ratio), int(img.height * ratio)))
    img.save(data, format=fmt)
    return data.getvalue()


async def image(request):
    """Fetch an image."""
    image_id = request.path_params['image_id']
    size = request.path_params.get('size')
    key = (image_id, size)
    if not await request.app.state.cache.exists(key):
        data = await request.app.state.database.fetch_one(
            "select path from image where id=:id", values=dict(id=image_id)
        )
        result = await asyncio.to_thread(
            image_data, request.app.state.image_path / data['path'], size
        )
        if not result:
            raise HTTPException(status_code=404)
        await request.app.state.cache.set(key, result, ttl=600)
    return Response(await request.app.state.cache.get(key))
