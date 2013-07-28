import urllib2
import py.test
import cStringIO
from belt import models
from belt.utils import pypi_url
from belt.tests import create_package, patch
from pyramid.httpexceptions import HTTPNotFound, HTTPServerError
pypi_base_url = 'https://pypi.python.org/packages'


class TestDownloadPackage(object):

    def test_returns_404_if_package_not_on_pypi(self, db_session, dummy_request):
        from belt.views import download_package

        url = pypi_url(pypi_base_url, 'source', 'flake8', 'flake8-2.0.tar.gz')
        dummy_request.path = url
        dummy_request.matchdict = {'package': 'flake8', 'kind': 'source',
                                   'letter': 'f', 'basename': 'flake8-2.0.tar.gz'}

        with patch('belt.views.get_package_from_pypi') as get_package:
            err404 = urllib2.HTTPError(url, 404, 'Not Found', None, None)
            get_package.expects_call().with_args(url).raises(err404)

            with py.test.raises(HTTPNotFound):
                download_package(dummy_request)

    def test_returns_500_when_server_error(self, db_session, http, dummy_request):
        from belt.views import download_package

        url = pypi_url(pypi_base_url, 'source', 'flake8', 'flake8-2.0.tar.gz')
        dummy_request.path = url
        dummy_request.matchdict = {'package': 'flake8', 'kind': 'source',
                                   'letter': 'f', 'basename': 'flake8-2.0.tar.gz'}

        with patch('belt.views.get_package_from_pypi') as get_package:
            err500 = urllib2.URLError('yikes!')
            get_package.expects_call().with_args(url).raises(err500)

            with py.test.raises(HTTPServerError):
                download_package(dummy_request)

    def test_obtains_missing_file_from_pypi(self, tmpdir, db_session,
                                            dummy_request):
        from belt.views import download_package

        pkg = tmpdir.join('foo-1.2.tar.gz')
        package = create_package(pkg, content=u'Short lived')

        # remove just the package file, not the record
        pkg.remove()
        db_session.add(package)
        db_session.flush()

        url = pypi_url(pypi_base_url, 'source', 'foo', 'foo-1.2.tar.gz')
        dummy_request.path = url
        dummy_request.matchdict = {'package': 'foo', 'kind': 'source',
                                   'letter': 'f', 'basename': 'foo-1.2.tar.gz'}
        with patch('belt.views.get_package_from_pypi') as get_package:
            get_package.expects_call().with_args(url).returns(cStringIO.StringIO('Got it!'))
            response = download_package(dummy_request)
        assert 'Got it!' == response.body


class TestRequestNonExistentPackage(object):

    def test_creates_package_record(self, db_session, dummy_request):
        from belt.views import download_package

        url = pypi_url(pypi_base_url, 'source', 'foo', 'foo-1.2.tar.gz')
        dummy_request.matchdict = {'package': 'foo', 'kind': 'source',
                                   'letter': 'f', 'basename': 'foo-1.2.tar.gz'}
        dummy_request.path = url

        with patch('belt.views.get_package_from_pypi') as get_package:
            content = cStringIO.StringIO('Got it!')
            get_package.expects_call().with_args(url).returns(content)
            download_package(dummy_request)

        db_session.query(models.Package).filter_by(name='foo').one()

    def test_creates_release_record(self, db_session, dummy_request):
        from belt.views import download_package

        url = pypi_url(pypi_base_url, 'source', 'foo', 'foo-1.2.tar.gz')
        dummy_request.matchdict = {'package': 'foo', 'kind': 'source',
                                   'letter': 'f', 'basename': 'foo-1.2.tar.gz'}
        dummy_request.path = url

        with patch('belt.views.get_package_from_pypi') as get_package:
            content = cStringIO.StringIO('Got it!')
            get_package.expects_call().with_args(url).returns(content)
            download_package(dummy_request)

        models.Release.for_package('foo', '1.2')

    def test_creates_file_record(self, db_session, dummy_request):
        from belt.views import download_package

        url = pypi_url(pypi_base_url, 'source', 'foo', 'foo-1.2.tar.gz')
        dummy_request.matchdict = {'package': 'foo', 'kind': 'source',
                                   'letter': 'f', 'basename': 'foo-1.2.tar.gz'}
        dummy_request.path = url
        with patch('belt.views.get_package_from_pypi') as get_package:
            content = cStringIO.StringIO('Got it!')
            get_package.expects_call().with_args(url).returns(content)
            download_package(dummy_request)

        models.File.for_release('foo', '1.2')


class TestRequestNonExistentFile(object):

    def test_redirects_to_pypi(self, db_session, dummy_request):
        from belt.views import download_package

        url = pypi_url(pypi_base_url, 'source', 'foo', 'foo-1.2.tar.gz')
        dummy_request.matchdict = {'package': 'foo', 'kind': 'source',
                                   'letter': 'f', 'basename': 'foo-1.2.tar.gz'}
        dummy_request.path = url
        with patch('belt.views.get_package_from_pypi') as get_package:
            content = cStringIO.StringIO('GOT IT')
            get_package.expects_call().with_args(url).returns(content)
            response = download_package(dummy_request)
        assert 'GOT IT' == response.body
