import os.path
import urllib2
import cStringIO
import py.test
from hashlib import md5
from httpretty import HTTPretty, httprettified


def test_get_local_packages(tmpdir):
    from ..utils import local_packages

    tmpdir.mkdir('py.test')
    tmpdir.mkdir('yolk')
    tmpdir.mkdir('coverage')

    package_names = local_packages(str(tmpdir))
    assert ['coverage', 'py.test', 'yolk'] == sorted(list(package_names))


def test_returns_empty_list_if_dir_is_empty(tmpdir):
    from ..utils import local_packages
    package_names = local_packages(str(tmpdir))
    assert [] == list(package_names)


def test_get_dir_for_package(tmpdir):
    from ..utils import local_versions
    yolk = tmpdir.mkdir('yolk').join('yolk.1.0.1.tar.gz')
    yolk.write('1')
    package_dir = str(tmpdir)
    assert ['yolk.1.0.1.tar.gz'] == local_versions(package_dir, 'yolk')


def test_local_versions_excludes_hash_files(tmpdir):
    from ..utils import local_versions
    yolk = tmpdir.mkdir('yolk').join('yolk.1.0.1.tar.gz.md5')
    yolk.write('')
    package_dir = str(tmpdir)
    assert [] == local_versions(package_dir, 'yolk')


def test_local_versions_has_md5_attr(tmpdir):
    from ..utils import local_versions
    p = tmpdir.join('somename.exe')
    p.write('')

    p = tmpdir.join('somename.exe.md5')
    p.write('HASHED CONTENT')
    package_dir = str(tmpdir)
    local, = local_versions(package_dir, '')
    assert 'HASHED CONTENT' == local.md5


def test_returns_empty_list_if_no_local_versions(tmpdir):
    from ..utils import local_versions
    package_dir = str(tmpdir)
    assert [] == local_versions(package_dir, 'yolk')


def test_returns_empty_list_if_no_local_package_dir(tmpdir):
    from ..utils import local_versions
    package_dir = str(tmpdir)
    tmpdir.mkdir('yolk')
    assert [] == local_versions(package_dir, 'yolk')


def test_get_full_path_to_version(tmpdir):
    from ..utils import get_package
    yolk = tmpdir.mkdir('yolk').join('yolk.1.0.1.tar.gz')
    yolk.write('1')
    expected = os.path.join(str(tmpdir), 'yolk', 'yolk.1.0.1.tar.gz')
    package_dir = str(tmpdir)
    assert expected == get_package(package_dir, 'yolk',
                                   'yolk.1.0.1.tar.gz').path


class TestStoreLocally(object):

    def test_writes_file_content_to_destination(self, tmpdir):
        from ..utils import store_locally
        blub = tmpdir.mkdir('blub').join('blub.4.3.tar.gz')
        blub.write('1')

        fo = cStringIO.StringIO()
        fo.write('some code goes here')
        fo.seek(0)
        store_locally(str(blub), fo)

        with open(str(blub)) as output:
            assert 'some code goes here' == output.read()

    def test_makes_dir_if_nonexistant(self, tmpdir):
        from ..utils import store_locally
        destination = os.path.join(str(tmpdir), 'foo', 'bar', 'baz-1.zip')
        fo = cStringIO.StringIO()
        fo.write('path making')
        fo.seek(0)

        store_locally(destination, fo)

        with open(destination) as output:
            assert 'path making' == output.read()

    def test_creates_md5_of_package(self, tmpdir):
        from ..utils import store_locally

        destination = os.path.join(str(tmpdir), 'baz-1.zip')
        fo = cStringIO.StringIO()
        fo.write('sOmE cOnTeNt')
        fo.seek(0)

        store_locally(destination, fo)
        with open(destination + '.md5') as hashed:
            assert md5('sOmE cOnTeNt').hexdigest() == hashed.read()


class TestGetPackageFromPypi(object):

    @httprettified
    def test_get_package_from_pypi(self):
        from ..utils import get_package_from_pypi, pypi_url
        pypi_base_url = 'https://pypi.python.org/packages'
        url = pypi_url(pypi_base_url, 'source', 'f', 'flake8',
                       'flake8-2.0.tar.gz')

        HTTPretty.register_uri(HTTPretty.GET, url, body='Got it!')
        response = get_package_from_pypi(url)
        assert 'Got it!' == response.read()

    @httprettified
    def test_breaks_on_404(self):
        from ..utils import get_package_from_pypi, pypi_url
        pypi_base_url = 'https://pypi.python.org/packages'
        url = pypi_url(pypi_base_url, 'source', 'f', 'flake8',
                       'flake8-2.0.tar.gz')

        HTTPretty.register_uri(HTTPretty.GET, url, body='Missed it!',
                               status=404)

        with py.test.raises(urllib2.URLError):
            get_package_from_pypi(url)
