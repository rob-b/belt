from pyramid.config import Configurator
from pyramid_jinja2 import renderer_factory


def main(global_config, **settings):
    """ This function returns a WSGI application.

    It is usually called by the PasteDeploy framework during
    ``paster serve``.
    """
    settings = dict(settings)
    settings.setdefault('jinja2.i18n.domain', 'belt')

    config = Configurator(settings=settings)
    config.add_translation_dirs('locale/')
    config.include('pyramid_jinja2')

    config.add_static_view('static', 'static')
    config.add_route('simple', '/simple')
    config.add_route('simple_name', '/simple/{name}')

    # config.add_route('simple_package', '/*subpath')
    # config.add_view('belt.static.static_view', route_name='simple_package')

    config.scan('belt')
    config.add_renderer('.html', renderer_factory)

    return config.make_wsgi_app()
