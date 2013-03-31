import os.path
import urllib2
import py.test
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
    assert expected == get_package(package_dir, 'yolk', 'yolk.1.0.1.tar.gz')


class TestGetPackageFromPypi(object):

    @httprettified
    def test_get_package_from_pypi(self):
        from ..utils import get_package_from_pypi, pypi_url
        pypi_base_url = 'https://pypi.python.org/simple'
        url = pypi_url(pypi_base_url, 'source', 'f', 'flake8',
                       'flake8-2.0.tar.gz')

        HTTPretty.register_uri(HTTPretty.GET, url, body='Got it!')
        response = get_package_from_pypi(url)
        assert 'Got it!' == response.read()

    @httprettified
    def test_breaks_on_404(self):
        from ..utils import get_package_from_pypi, pypi_url
        pypi_base_url = 'https://pypi.python.org/simple'
        url = pypi_url(pypi_base_url, 'source', 'f', 'flake8',
                       'flake8-2.0.tar.gz')

        HTTPretty.register_uri(HTTPretty.GET, url, body='Missed it!',
                               status=404)

        with py.test.raises(urllib2.URLError):
            get_package_from_pypi(url)
