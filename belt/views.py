import os
import glob
import urllib2
from pyramid.view import view_config
from pyramid.response import FileResponse
from pyramid.i18n import TranslationStringFactory

_ = TranslationStringFactory('belt')


def path_to_name(path, bundle):
    return dict(bundle)[path]


def name_to_path(name, bundle):
    return dict([(v, k) for k, v in bundle])[name]


def pip_cache_path():
    return '/Users/rob/.pip-cache'


def compose(*functions):
    def composed(arg):
        for function in functions:
            arg = function(arg)
        return arg
    return composed


def package_dir_contents():
    packages = glob.iglob('{}/*'.format(pip_cache_path()))
    composed = compose(urllib2.unquote, os.path.basename)
    return ((package, composed(package)) for package in packages if
            filter_package(package))


def filter_package(package):
    return not package.endswith('content-type')


@view_config(route_name='simple', renderer='simple.html')
def my_view(request):
    packages = package_dir_contents()
    return {'packages': packages}


@view_config(route_name='simple_name')
def download(request):
    name = request.matchdict['name']
    path = name_to_path(name, package_dir_contents())
    return FileResponse(path)
