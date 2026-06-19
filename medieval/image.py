"""Image route."""

import asyncio
import io
import os

from PIL import Image
from starlette.exceptions import HTTPException
from starlette.responses import Response


CACHED_SIZES = frozenset({200, 300, 400})

CACHE_HEADERS = {
    "Cache-Control": "public, max-age=31536000, immutable"
}


def image_data(path, size=None, fmt='WEBP'):
    """Get image bytes for requested size."""
    try:
        img = Image.open(path)
    except FileNotFoundError:
        return None
    if size:
        if img.format == 'JPEG':
            # Decode JPEG at a lower DCT level when downscaling; large speedup
            # for thumbnails.
            img.draft('RGB', (size * 2, size * 2))
        ratio = size / max(img.height, img.width)
        img = img.resize(
            (int(img.width * ratio), int(img.height * ratio)),
            Image.Resampling.LANCZOS,
        )
    data = io.BytesIO()
    img.save(data, format=fmt, quality=85)
    return data.getvalue()


def _read_cached(cache_file):
    """Read cached bytes if present."""
    try:
        with open(cache_file, 'rb') as f:
            return f.read()
    except FileNotFoundError:
        return None


def _write_cached(cache_file, payload):
    """Atomically write cached bytes; failures are non-fatal."""
    tmp = f'{cache_file}.tmp.{os.getpid()}.{os.urandom(4).hex()}'
    try:
        with open(tmp, 'wb') as f:
            f.write(payload)
        os.replace(tmp, cache_file)
    except OSError:
        try:
            os.unlink(tmp)
        except OSError:
            pass


async def image(request):
    """Fetch an image."""
    image_id = request.path_params['image_id']
    size = request.path_params.get('size')

    cache_file = None
    if size in CACHED_SIZES:
        cache_file = request.app.state.image_path / 'cache' / f'{image_id}x{size}.webp'
        cached = await asyncio.to_thread(_read_cached, cache_file)
        if cached is not None:
            return Response(cached, headers=CACHE_HEADERS)

    row = await request.app.state.database.fetch_one(
        "select path from image where id=:id", values=dict(id=image_id)
    )
    if not row:
        raise HTTPException(status_code=404)

    result = await asyncio.to_thread(
        image_data, request.app.state.image_path / row['path'], size
    )
    if not result:
        raise HTTPException(status_code=404)

    if cache_file is not None:
        await asyncio.to_thread(_write_cached, cache_file, result)

    return Response(result, headers=CACHE_HEADERS)
