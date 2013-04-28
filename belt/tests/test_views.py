import py.test
from fudge import patch, Fake
from fudge.inspector import arg
from pyramid import testing
from pyramid.httpexceptions import HTTPNotFound, HTTPServerError
from sqlalchemy.orm import exc
from httpretty import HTTPretty
from belt.utils import pypi_url
from belt import models
from belt.axle import split_package_name


pypi_base_url = 'https://pypi.python.org/packages'


def create_package(path, content=u''):
    import os

    if content:
        filename = str(path)
        path.write(content)
    else:
        filename = u''
    basename = os.path.basename(str(path))
    name, version = split_package_name(basename)

    package = models.Package(name=name)
    rel = models.Release(version=version)
    package.releases.append(rel)
    rel.files.append(models.File(filename=filename, md5='gg'))
    return package


class TestDownloadPackage(object):

    def test_returns_404_if_package_not_on_pypi(self, http, db_session, dummy_request):
        from ..views import download_package

        request = dummy_request
        url = pypi_url(pypi_base_url, 'source', 'flake8', 'flake8-2.0.tar.gz')
        HTTPretty.register_uri(HTTPretty.GET, url, body='Missed it!', status=404)
        request.matchdict = {'package': 'flake8', 'kind': 'source',
                             'letter': 'f', 'basename': 'flake8-2.0.tar.gz'}

        with py.test.raises(HTTPNotFound):
            download_package(request)

    def test_returns_500_when_server_error(self, http, dummy_request):
        from ..views import download_package

        request = dummy_request
        url = pypi_url(pypi_base_url, 'source', 'flake8', 'flake8-2.0.tar.gz')
        HTTPretty.register_uri(HTTPretty.GET, url, body='Yikes!', status=500)
        request.matchdict = {'package': 'flake8', 'kind': 'source',
                             'letter': 'f', 'basename': 'flake8-2.0.tar.gz'}

        with py.test.raises(HTTPServerError):
            download_package(request)

    def test_obtains_missing_file_from_pypi(self, tmpdir, http, db_session,
                                            dummy_request):
        from ..views import download_package

        pkg = tmpdir.join('foo-1.2.tar.gz')
        package = create_package(pkg, content=u'Short lived')

        # remove just the package file, not the record
        pkg.remove()
        db_session.add(package)
        db_session.flush()

        url = pypi_url(pypi_base_url, 'source', 'foo', 'foo-1.2.tar.gz')
        HTTPretty.register_uri(HTTPretty.GET, url, body='GOT IT', status=200)

        dummy_request.matchdict = {'package': 'foo', 'kind': 'source',
                                   'letter': 'f', 'basename': 'foo-1.2.tar.gz'}
        response = download_package(dummy_request)
        assert 'GOT IT' == response.body


class TestRequestNonExistentPackage(object):

    def test_creates_package_record(self, http, db_session, dummy_request):
        from ..views import download_package

        url = pypi_url(pypi_base_url, 'source', 'foo', 'foo-1.2.tar.gz')
        HTTPretty.register_uri(HTTPretty.GET, url, body='GOT IT', status=200)

        request = testing.DummyRequest()
        request.matchdict = {'package': 'foo', 'kind': 'source',
                             'letter': 'f', 'basename': 'foo-1.2.tar.gz'}
        download_package(request)

        db_session.query(models.Package).filter_by(name='foo').one()

    def test_creates_release_record(self, http, db_session, dummy_request):
        from ..views import download_package

        url = pypi_url(pypi_base_url, 'source', 'foo', 'foo-1.2.tar.gz')
        HTTPretty.register_uri(HTTPretty.GET, url, body='GOT IT', status=200)

        dummy_request.matchdict = {'package': 'foo', 'kind': 'source',
                                   'letter': 'f', 'basename': 'foo-1.2.tar.gz'}
        download_package(dummy_request)

        models.Release.for_package('foo', '1.2')

    def test_creates_file_record(self, http, db_session, dummy_request):
        from ..views import download_package

        url = pypi_url(pypi_base_url, 'source', 'foo', 'foo-1.2.tar.gz')
        HTTPretty.register_uri(HTTPretty.GET, url, body='GOT IT', status=200)

        dummy_request.matchdict = {'package': 'foo', 'kind': 'source',
                                   'letter': 'f', 'basename': 'foo-1.2.tar.gz'}
        download_package(dummy_request)

        models.File.for_release('foo', '1.2')


class TestRequestNonExistentFile(object):

    def test_redirects_to_pypi(self, http, db_session, dummy_request):
        from ..views import download_package

        url = pypi_url(pypi_base_url, 'source', 'foo', 'foo-1.2.tar.gz')
        HTTPretty.register_uri(HTTPretty.GET, url, body='GOT IT', status=200)

        dummy_request.matchdict = {'package': 'foo', 'kind': 'source',
                                   'letter': 'f', 'basename': 'foo-1.2.tar.gz'}
        response = download_package(dummy_request)
        assert url == response.location


class TestPackageList(object):

    def test_requests_package_data_from_pypi(self, dummy_request):
        from ..views import package_list
        dummy_request.matchdict = {'package': u'foo'}

        pkg = Fake('Package').has_attr(name='foo', releases=[1])

        with patch('belt.views.Package') as Package:
            Package.expects('by_name').with_args('foo').raises(exc.NoResultFound)
            (Package.expects('create_from_pypi')
             .with_args(name='foo', package_dir=arg.any())
             .returns(pkg))
            package_list(dummy_request)

    @patch('belt.views.DBSession')
    @patch('belt.views.Package')
    @patch('belt.views.package_releases')
    def test_requests_package_releases_if_none_exist(self, DBSession, Package,
                                                     package_releases):
        from ..views import package_list

        package_releases.expects_call().with_args('quux').returns('A RELEASE')

        pkg = (Fake('pkg').has_attr(name='quux', releases=[]))
        Package.expects('by_name').with_args('quux').returns(pkg)
        DBSession.expects('add').with_args(pkg)

        dummy_request = testing.DummyRequest()
        dummy_request.matchdict = {'package': u'quux'}

        package_list(dummy_request)
