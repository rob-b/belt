import logging
from pyramid.view import view_config
from pyramid.i18n import TranslationStringFactory
from pyramid.response import FileResponse

from .utils import local_packages, local_versions, get_package

_ = TranslationStringFactory('belt')


log = logging.getLogger(__name__)


@view_config(route_name='simple', renderer='simple.html')
def simple_list(request):
    package_dir = request.registry.settings['local_packages']
    return {'packages': local_packages(package_dir)}


@view_config(route_name='package_list', renderer='package_list.html')
def package_list(request):
    package_dir = request.registry.settings['local_packages']
    name = request.matchdict['package']
    return {'package_versions': local_versions(package_dir, name),
            'package_name': name}


@view_config(route_name='download_package')
def download_package(request):
    name, version = request.matchdict['package'], request.matchdict['version']
    package_dir = request.registry.settings['local_packages']
    package_path = get_package(package_dir, name, version)
    return FileResponse(package_path)
