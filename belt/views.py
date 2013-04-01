import urllib2
import logging
from pyramid.view import view_config, notfound_view_config
from pyramid.i18n import TranslationStringFactory
from pyramid.response import FileResponse
from pyramid.httpexceptions import exception_response, HTTPNotFound

from .utils import (local_packages, local_versions, get_package, pypi_url,
                    get_package_from_pypi, store_locally)

_ = TranslationStringFactory('belt')


PYPI_BASE_URL = 'https://pypi.python.org/packages'


log = logging.getLogger(__name__)


@notfound_view_config(append_slash=True)
def notfound(request):
    return HTTPNotFound()


@view_config(route_name='simple', renderer='simple.html')
def simple_list(request):
    package_dir = request.registry.settings['local_packages']
    return {'packages': local_packages(package_dir)}


@view_config(route_name='package_list', renderer='package_list.html')
def package_list(request):
    package_dir = request.registry.settings['local_packages']
    name = request.matchdict['package']
    return {'package_versions': local_versions(package_dir, name),
            'kind': 'source',
            'letter': name[0],
            'package_name': name}


@view_config(route_name='download_package')
def download_package(request):
    name, version, kind, letter = [request.matchdict[key] for key in
                                   ['package', 'version', 'kind', 'letter']]
    package_dir = request.registry.settings['local_packages']
    package_path = get_package(package_dir, name, version)
    if not package_path.exists:
        url = pypi_url(PYPI_BASE_URL, kind, letter, name, version)
        try:
            package = get_package_from_pypi(url)
        except urllib2.HTTPError as err:
            raise exception_response(err.code, body=err.read())
        except urllib2.URLError:
            raise
        store_locally(package_path.path, package)
    return FileResponse(package_path.path)
