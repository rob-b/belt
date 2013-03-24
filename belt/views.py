import re
import os
import glob
import urllib2
import logging
import collections
from pyramid.view import view_config
from pyramid.response import FileResponse
from pyramid.i18n import TranslationStringFactory

_ = TranslationStringFactory('belt')


log = logging.getLogger(__name__)


class PackageProxy(list):
    path = None


def pip_cache_to_packages():
    bare_packages = []
    for path, package in pip_cached_packages():
        for ext in known_extensions:
            if package.endswith(ext):
                package = package.replace(ext, '')
                break
        bare_packages.append((path, package))

    version_regex = re.compile('^([\w\.-]+)-((?:\d+\.?){1,3})')

    packages = collections.defaultdict(PackageProxy)
    for path, package in bare_packages:
        match = version_regex.match(package)

        if match:
            name, version = match.groups()
            packages[name].append(version)
        else:
            name = package
            packages[name].append(None)
        packages[name].path = path

        if not match:
            log.error('{} has a badly formatted version'.format(package))
    return packages


def path_to_name(path, bundle):
    return dict(bundle)[path]


def name_to_path(name, bundle):
    return dict([(v, k) for k, v in bundle])[name]


def pip_cache_path():
    return os.path.expanduser(os.environ['PIP_DOWNLOAD_CACHE'])


def compose(*functions):
    def composed(arg):
        return reduce(lambda a, f: f(a), [arg] + list(functions))
    return composed


def pip_cached_packages(pip_cache_dir=None):
    pip_cache_dir = pip_cache_dir or pip_cache_path()
    packages = glob.iglob('{}/*'.format(pip_cache_dir))
    composed = compose(urllib2.unquote, os.path.basename)
    return ((package, composed(package)) for package in packages)


def filter_packages(packages):
    return ((path, package) for path, package in packages if not
            path.endswith('content-type'))


known_extensions = ['.tar.gz', '.zip']


@view_config(route_name='simple', renderer='simple.html')
def simple_list(request):
    return {'packages': pip_cache_to_packages()}


@view_config(route_name='package_list')
def packages(request):
    name = request.matchdict['package']


def download(request):
    name = request.matchdict['package']
    path = name_to_path(name, pip_cached_packages())
    return FileResponse(path)
