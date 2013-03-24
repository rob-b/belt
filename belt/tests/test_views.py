import fudge
import pytest
from pyramid import testing


def test_read_pip_cache():
    from belt.views import pip_cached_packages
    package = list(pip_cached_packages())[0]
    assert len(package) == 2


def test_obtain_name():
    from belt.views import path_to_name
    path = '/var/www/thing'
    bundle = [
        (path, 'argparse.tgz'),
        ('/g', 'argparse.tgz'),
    ]
    name = path_to_name(path, bundle)
    assert name == 'argparse.tgz'


def test_raises_keyerror_if_missing_path():
    from belt.views import path_to_name
    with pytest.raises(KeyError):
        path_to_name('nope', {})


def test_obtain_path():
    from belt.views import name_to_path
    name = 'argparse.exe'
    bundle = [
        ('/a/b', name),
    ]
    path = name_to_path(name, bundle)
    assert path == '/a/b'


def test_keyerror_if_missing_name():
    from belt.views import name_to_path
    with pytest.raises(KeyError):
        name_to_path('', [])


def test_pip_cached_packages_is_unfiltered():
    from belt.views import pip_cached_packages
    names = (name for path, name in pip_cached_packages() if
             name.endswith('content-type'))
    assert next(names, 'no matches') != 'no matches'


def test_filter_packages_removes_non_archives():
    from belt.views import pip_cached_packages, filter_packages
    filtered = filter_packages(pip_cached_packages())
    names = (name for path, name in filtered if name.endswith('content-type'))
    assert next(names, 'no matches') == 'no matches'


class TestPipCacheToPackages(object):

    @fudge.patch('belt.views.pip_cached_packages')
    def test_returns_dict_of_package_names(self, pip_cached_packages):
        from belt.views import pip_cache_to_packages

        fullnames = [
            ('/foo', 'python-memcached-1.44.tar.gz'),
            ('/bar', 'argparse-1.2.1.tar.gz'),
        ]
        pip_cached_packages.expects_call().returns(fullnames)

        packages = pip_cache_to_packages()
        assert packages.keys() == ['python-memcached', 'argparse']

    @fudge.patch('belt.views.pip_cached_packages')
    def test_each_item_has_path_attr(self, pip_cached_packages):
        from belt.views import pip_cache_to_packages

        fullnames = [
            ('/foo', 'python-memcached-1.44.tar.gz'),
            ('/foo/quux', 'argparse-1.2.1.tar.gz'),
        ]
        pip_cached_packages.expects_call().returns(fullnames)

        packages = pip_cache_to_packages()
        assert packages['argparse'].path == '/foo/quux'

    @fudge.patch('belt.views.pip_cached_packages')
    def test_matches_package_names_with_dots(self, pip_cached_packages):
        from belt.views import pip_cache_to_packages

        fullnames = [
            ('/var/www', 'zope.interface-4.0.1.tar.gz'),
        ]
        pip_cached_packages.expects_call().returns(fullnames)

        packages = pip_cache_to_packages()
        assert 'zope.interface' in packages

    @fudge.patch('belt.views.pip_cached_packages')
    def test_packages_have_list_of_versions(self, pip_cached_packages):
        from belt.views import pip_cache_to_packages

        fullnames = [
            ('/var/www', 'zope.interface-4.0.1.tar.gz'),
            ('/foo/quux', 'zope.interface-4.0.3.tar.gz'),
        ]
        pip_cached_packages.expects_call().returns(fullnames)

        packages = pip_cache_to_packages()
        assert packages['zope.interface'] == ['4.0.1', '4.0.3']


class TestViewIntegration(object):

    def teardown_method(self, method):
        testing.tearDown()

    @fudge.patch('belt.views.pip_cached_packages')
    @fudge.patch('belt.views.FileResponse')
    def test_can_download_package(self, pip_cached_packages, FileResponse):
        from belt.views import download
        pip_cached_packages.expects_call().returns([
            ('/path/to/foozle', 'foozle'),
        ])

        FileResponse.expects('__init__').with_args('/path/to/foozle')
        request = testing.DummyRequest(matchdict={'package': 'foozle'})
        request.context = testing.DummyResource()
        download(request)

    def test_package_list(self):
        pass
