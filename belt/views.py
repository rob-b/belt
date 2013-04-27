import os
import urllib2
import logging
from pyramid.view import view_config, notfound_view_config
from pyramid.i18n import TranslationStringFactory
from pyramid.response import FileResponse
from pyramid.httpexceptions import (exception_response, HTTPNotFound,
                                    HTTPMovedPermanently)

from .utils import (get_package, pypi_url, get_package_from_pypi,
                    store_locally, pypi_versions)

from sqlalchemy.orm import exc
from .models import DBSession, Package, File, Release
from .axle import (split_package_name, package_releases,
                   create_release)

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
    try:
        pkg = Package.by_name(name)
    except exc.NoResultFound:
        package_dir = request.registry.settings['local_packages']
        pkg = Package.create_from_pypi(name=name, package_dir=package_dir)

    if not pkg.releases:
        pkg.releases.extend(list(package_releases(pkg.name)))
        DBSession.add(pkg)

    if name != pkg.name:
        dest = request.route_url('package_list', package=pkg.name)
        raise HTTPMovedPermanently(dest)

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
    package_dir = request.registry.settings['local_packages']
    filename = os.path.join(package_dir, name)

    try:
        pkg = DBSession.query(Package).filter_by(name=name).one()
    except exc.NoResultFound:
        pkg = Package(name=name)
        DBSession.add(pkg)

    release = next((rel for rel in pkg.releases if rel.version == version), None)
    url = pypi_url(PYPI_BASE_URL, kind, letter, name, basename)
    log.info(release)
    if not release:
        log.info(basename + u' does not exist, retrieve from pypi')
        try:
            pkg = create_release(version, url)
        except urllib2.HTTPError as err:
            raise exception_response(err.code, body=err.read())
        except urllib2.URLError:
            raise
    else:
        rel_file = next((f for f in release.files if f.basename == basename), None)

    rel_file.filename = filename
    if not os.path.exists(rel_file.filename):
        fo = get_package_from_pypi(url)
        store_locally(rel_file.filename, fo)
    return FileResponse(rel_file.filename)
