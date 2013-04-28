import os
import urllib2
import logging
from pyramid.view import view_config, notfound_view_config
from pyramid.i18n import TranslationStringFactory
from pyramid.response import FileResponse
from pyramid.httpexceptions import (HTTPNotFound,
                                    HTTPFound,
                                    HTTPMovedPermanently)

from .utils import (get_package, pypi_url, get_package_from_pypi,
                    store_locally, pypi_versions)

from sqlalchemy.orm import exc
from .models import DBSession, Package, File, Release, get_or_create
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
    package, basename, kind, letter = [request.matchdict[key] for key in
                                       ['package', 'basename', 'kind', 'letter']]
    name, version = split_package_name(basename)

    try:
        rel_file = File.for_release(name, version)
    except exc.NoResultFound:
        rel_file = File()

        try:
            rel = Release.for_package(name, version)
        except exc.NoResultFound:
            rel = Release(version=version)
        rel.files.append(rel_file)
        if not rel.package:
            pkg, _ = get_or_create(DBSession, Package, name=name)
            rel.package = pkg
        DBSession.add(rel)

        dest = pypi_url(PYPI_BASE_URL, kind, name, basename)
        return HTTPFound(dest)
