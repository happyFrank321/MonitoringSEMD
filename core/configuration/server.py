"""
Base Server class module.
GET OUT OF HERE!
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.configuration.events import __events__
from core.configuration.exception_handlers import __exception_handlers__
from core.configuration.middlewares import __middlewares__
from core.configuration.routes import __routes__
from core.configuration.routes.docs_tree import docs_tree

try:
    from settings import app_config
except ImportError:
    from settings_example import app_config


class Server:
    """
    Server class to initialise FastAPI server.
    """

    __app: FastAPI
    __title = 'FastAPI template'
    __description = \
        '''
        FastAPI version of backend server for LPU.
        '''
    __version = '0.3.2'

    def __init__(self):
        self.__app = FastAPI(
            title=self.__title,
            description=self.__description,
            version=self.__version,
            debug=app_config.DEVELOPMENT,
            openapi_tags=docs_tree
        )
        self.__app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=False,
            allow_methods=["*"],
            allow_headers=["*"]
        )
        self.__register_routes(self.__app)
        self.__register_events(self.__app)
        # self.__register_middlewares(self.__app)
        self.__register_exception_handlers(self.__app)

    def get_app(self) -> FastAPI:
        """
        Get method to return app.
        :return: FastAPI app.
        """

        return self.__app

    @staticmethod
    def __register_routes(app):
        __routes__.register_routes(app)

    @staticmethod
    def __register_events(app):
        __events__.register_events(app)

    @staticmethod
    def __register_middlewares(app):
        __middlewares__.register_middlewares(app)

    @staticmethod
    def __register_exception_handlers(app):
        __exception_handlers__.register_exception_handlers(app)
