import os
import fudge
import pytest


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
        assert packages['argparse'][0].path == '/foo/quux'

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
        versions = [vers.number for vers in packages['zope.interface']]
        assert versions == ['4.0.1', '4.0.3']

    @fudge.patch('belt.views.pip_cached_packages')
    def test_excludes_content_type_file(self, pip_cached_packages):
        from belt.views import pip_cache_to_packages
        keep = ('/.pip-cache/git-sweep-0.1.1.tar.gz',
                'git-sweep-0.1.1.tar.gz')
        discard = ('/.pip-cache/git-sweep-0.1.1.tar.gz.content-type',
                   'git-sweep-0.1.1.tar.gz.content-type')
        pip_cached_packages.expects_call().returns((keep, discard))

        packages = pip_cache_to_packages()
        version = packages['git-sweep']
        assert len(version) == 1

    @fudge.patch('belt.views.pip_cached_packages')
    def test_excludes_content_type_file_2(self, pip_cached_packages):
        from belt.views import pip_cache_to_packages
        keep = ('/.pip-cache/git-sweep-0.1.1.tar.gz',
                'git-sweep-0.1.1.tar.gz')
        discard = ('/.pip-cache/git-sweep-0.1.1.tar.gz.content-type',
                   'git-sweep-0.1.1.tar.gz.content-type')
        pip_cached_packages.expects_call().returns((keep, discard))

        packages = pip_cache_to_packages()
        version, = packages['git-sweep']
        assert version.number == '0.1.1'


class TestPipCacheAccess(object):

    @classmethod
    def setup_class(cls):
        cls._original_cache_path = os.environ.get('PIP_DOWNLOAD_CACHE')
        # os.environ['PIP_DOWNLOAD_CACHE'] = ''

    @classmethod
    def teardown_class(cls):
        os.environ['PIP_DOWNLOAD_CACHE'] = cls._original_cache_path

    def test_read_pip_cache(self, tmpdir):
        from belt.views import pip_cached_packages
        tarball = tmpdir.join('foo.tar.gz')
        tarball.write('yikes!')
        package = list(pip_cached_packages(tarball.dirname))[0]
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
