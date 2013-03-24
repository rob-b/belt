import fudge
import pytest
from pyramid import testing


def test_read_pip_cache():
    from circle.views import package_dir_contents
    package = list(package_dir_contents())[0]
    assert len(package) == 2


def test_obtain_name():
    from circle.views import path_to_name
    path = '/var/www/thing'
    bundle = [
        (path, 'argparse.tgz'),
        ('/g', 'argparse.tgz'),
    ]
    name = path_to_name(path, bundle)
    assert name == 'argparse.tgz'


def test_raises_keyerror_if_missing_path():
    from circle.views import path_to_name
    with pytest.raises(KeyError):
        path_to_name('nope', {})


def test_obtain_path():
    from circle.views import name_to_path
    name = 'argparse.exe'
    bundle = [
        ('/a/b', name),
    ]
    path = name_to_path(name, bundle)
    assert path == '/a/b'


def test_keyerror_if_missing_name():
    from circle.views import name_to_path
    with pytest.raises(KeyError):
        name_to_path('', [])


def test_package_filter_excludes_content_type():
    from circle.views import package_dir_contents
    path, name = list(package_dir_contents())[0]
    assert not name.endswith('content-type')


class TestViewIntegration(object):

    def teardown_method(self, method):
        testing.tearDown()

    @fudge.patch('circle.views.package_dir_contents')
    @fudge.patch('circle.views.FileResponse')
    def test_god_knows_what(self, package_dir_contents, FileResponse):
        from circle.views import download
        package_dir_contents.expects_call().returns([
            ('/path/to/foozle', 'foozle'),
        ])

        FileResponse.expects('__init__').with_args('/path/to/foozle')
        request = testing.DummyRequest(matchdict={'name': 'foozle'})
        request.context = testing.DummyResource()
        download(request)
