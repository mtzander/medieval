"""Entry point."""
import pathlib

import databases

from starlette.applications import Starlette
from starlette.config import Config
from starlette.datastructures import URL
from starlette.routing import Route, Mount
from starlette.staticfiles import StaticFiles

import aiocache

from medieval import home, search, tags, art, image, sources, about
from medieval.util import css, javascript, favicon, metadata


class Manager:
    """Manage application lifecycle and metadata."""

    def __init__(self):
        """Initialize."""
        config = Config('./.env')
        self.debug = config('DEBUG', cast=bool, default=False)
        self.database = databases.Database(config('DATABASE_URL', cast=databases.DatabaseURL))
        self.image_path = config('IMAGE_PATH', cast=pathlib.Path)
        self.emulate = config('EMULATE', cast=str, default=None)
        self.cache = aiocache.Cache(aiocache.Cache.MEMORY)
        self.metadata = {}

    async def startup(self):
        """Called on startup."""
        await self.database.connect()
        self.metadata = await metadata(self.database)

    async def shutdown(self):
        """Called on shutdown."""
        await self.database.disconnect()


class MultiStaticFiles(StaticFiles):
    """Differentiate static files by domain."""

    def __init__(self, force=None, **kwargs):
        """Initialize."""
        super().__init__(**kwargs)
        self._force = force

    def get_path(self, scope):
        """Get local file path."""
        domain = URL(scope=scope).hostname
        if self._force:
            domain = self._force
        return pathlib.Path(domain, pathlib.Path(scope['path']).name)


def new_app():
    """Create a new instance of ASGI application."""
    manager = Manager()
    routes = [
        Route('/', home.home),
        Route('/search', search.search),
        Route('/gallery', search.search),
        Route('/tags', tags.tags),
        Route('/tags/add', tags.tag_add, methods=['POST']),
        Route('/tags/remove', tags.tag_remove, methods=['POST']),
        Route('/tags/suggest/{input:str}', tags.tag_suggest),
        Route('/{art_id:int}', art.art),
        Route('/{art_id:int}/{image_id:int}', art.art),
        Route('/image/{image_id:int}', image.image),
        Route('/image/{image_id:int}/{size:int}', image.image),
        Route('/sources', sources.sources),
        Route('/about', about.about),
        Route('/css', css),
        Route('/js', javascript),
        Route('/favicon.ico', favicon),
        Mount('/assets', MultiStaticFiles(directory='assets', force=manager.emulate))
    ]
    app = Starlette(
        debug=manager.debug,
        routes=routes,
        on_startup=[manager.startup],
        on_shutdown=[manager.shutdown]
    )
    app.state = manager
    return app


APP = new_app()
