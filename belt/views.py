import os
import urllib2
import logging
from pyramid.view import view_config, notfound_view_config
from pyramid.i18n import TranslationStringFactory
from pyramid.response import FileResponse
from pyramid.httpexceptions import exception_response, HTTPNotFound

from .utils import (local_packages, local_releases, get_package, pypi_url,
                    get_package_from_pypi, store_locally, pypi_versions,
                    pypi_package_page, convert_url_to_pypi)

from sqlalchemy import or_
from sqlalchemy.orm import exc
from .models import DBSession, Package, File, Release
from .utils import get_search_names
from .axle import split_package_name

_ = TranslationStringFactory('belt')


PYPI_BASE_URL = 'https://pypi.python.org/packages'


log = logging.getLogger(__name__)


@notfound_view_config(append_slash=True)
def notfound(request):
    return HTTPNotFound()


@view_config(route_name='simple', renderer='simple.html')
def simple_list(request):
    pkgs = DBSession.query(Package).all()
    return {'packages': pkgs}


@view_config(route_name='package_list', renderer='package_list.html')
def package_list(request):
    name = request.matchdict['package']
    names = get_search_names(name)
    or_query = or_(*[Package.name == n for n in names])
    pkg = DBSession.query(Package).filter(or_query).one()
    return {'package': pkg,
            'kind': 'source',
            'letter': name[0],
            'package_name': name}


@view_config(route_name='package_version', renderer='package_list.html')
def package_version(request):
    name = request.matchdict['package']
    version = request.matchdict['version']

    # when specifiying a version pip requests /simple/package/version but it
    # seems that url scheme never resolves on the real pypi which gives us a
    # chance to inject a decision (perhaps that is the purpose of that
    # lookup). If we have a local package with said name and version we can
    # redirect to our local list, else use the pypi list for this package in
    # case it exists there. Unfortunately we cannot just directly download
    # from this point as we don't have the 'kind' value
    package_dir = request.registry.settings['local_packages']
    package_path = get_package(package_dir, name, version)
    if not package_path.exists:
        log.info(package_path.path + u' does not exist, retrieve from pypi')
    else:
        log.info(package_path.path + u' exists')
    return HTTPNotFound()


@view_config(route_name='download_package')
def download_package(request):
    name, basename, kind, letter = [request.matchdict[key] for key in
                                   ['package', 'basename', 'kind', 'letter']]
    name, version = split_package_name(basename)

    try:
        rel_file = File.for_release(package=name, version=version)
    except exc.NoResultFound:
        package_dir = request.registry.settings['local_packages']
        # package_dir = '/tmp'
        dest = os.path.join(package_dir, name, basename)
        rel_file = File(filename=dest, md5='')

        try:
            release = (DBSession.query(Release).join(Release.package)
                       .filter(Release.version == version, Package.name == name)
                       .one())
        except:
            pass
        else:
            release.files.append(rel_file)
            DBSession.add(rel_file)

    if not os.path.exists(rel_file.filename):

        log.info(basename + u' does not exist, retrieve from pypi')
        url = pypi_url(PYPI_BASE_URL, kind, letter, name, basename)
        try:
            package = get_package_from_pypi(url)
        except urllib2.HTTPError as err:
            raise exception_response(err.code, body=err.read())
        except urllib2.URLError:
            raise
        store_locally(rel_file.filename, package)
    return FileResponse(rel_file.filename)
