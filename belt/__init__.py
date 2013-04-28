from pyramid.config import Configurator
from pyramid_jinja2 import renderer_factory
from sqlalchemy import engine_from_config
from .models import DBSession, Base


def main(global_config, **settings):
    """ This function returns a WSGI application.

    It is usually called by the PasteDeploy framework during
    ``paster serve``.
    """
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine

    settings = dict(settings)
    settings.setdefault('jinja2.i18n.domain', 'belt')

    config = Configurator(settings=settings)
    config.add_translation_dirs('locale/')
    config.include('pyramid_jinja2')
    config.include('pyramid_tm')

    config.add_static_view('static', 'static')
    config.add_route('simple', '/simple/')
    config.add_route('package_list', '/simple/{package}/')
    config.add_route('package_version', '/simple/{package}/{version}')
    config.add_route('download_package',
                     '/packages/{kind}/{letter}/{package}/{basename}')

    config.scan('belt', ignore='belt.tests')
    config.add_renderer('.html', renderer_factory)

    return config.make_wsgi_app()
