import os
import pytest
import py.test
from pyramid import testing
from pyramid.httpexceptions import HTTPNotFound, HTTPServerError
from httpretty import HTTPretty
from belt.utils import pypi_url
from belt import models
from belt.axle import split_package_name
from pyramid.paster import get_appsettings
from sqlalchemy import engine_from_config


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))


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


@pytest.fixture
def http(request):
    HTTPretty.reset()
    HTTPretty.enable()
    request.addfinalizer(HTTPretty.disable)


@pytest.fixture(scope='session')
def connection():
    settings = get_appsettings(os.path.join(ROOT, 'test.ini'))
    engine = engine_from_config(settings, 'sqlalchemy.')
    engine.echo = False
    models.Base.metadata.create_all(engine)
    connection = engine.connect()
    models.DBSession.registry.clear()
    models.DBSession.configure(bind=connection)
    models.Base.metadata.bind = engine
    return connection


@pytest.fixture
def db_session(request, connection):
    from transaction import abort
    trans = connection.begin()
    request.addfinalizer(trans.rollback)
    request.addfinalizer(abort)

    from belt.models import DBSession
    return DBSession


@pytest.fixture
def config(request):
    from pyramid import testing  # noqa
    config = testing.setUp()
    request.addfinalizer(testing.tearDown)
    return config


@pytest.fixture
def dummy_request(config, tmpdir):
    config.add_settings({'local_packages': str(tmpdir)})
    config.manager.get()['request'] = request = testing.DummyRequest()
    return request


class TestView(object):

    def test_returns_404_if_package_not_on_pypi(self, http, db_session, dummy_request):
        from ..views import download_package

        request = dummy_request
        url = pypi_url(pypi_base_url, 'source', 'f', 'flake8', 'flake8-2.0.tar.gz')
        HTTPretty.register_uri(HTTPretty.GET, url, body='Missed it!', status=404)
        request.matchdict = {'package': 'flake8', 'kind': 'source',
                             'letter': 'f', 'basename': 'flake8-2.0.tar.gz'}

        with py.test.raises(HTTPNotFound):
            download_package(request)

    def test_returns_500_when_server_error(self, http, dummy_request):
        from ..views import download_package

        request = dummy_request
        url = pypi_url(pypi_base_url, 'source', 'f', 'flake8', 'flake8-2.0.tar.gz')
        HTTPretty.register_uri(HTTPretty.GET, url, body='Yikes!', status=500)
        request.matchdict = {'package': 'flake8', 'kind': 'source',
                             'letter': 'f', 'basename': 'flake8-2.0.tar.gz'}

        with py.test.raises(HTTPServerError):
            download_package(request)

    def test_loads_existing_file_from_filesystem(self, tmpdir, db_session):
        from ..views import download_package

        package = create_package(tmpdir.join('foo-1.2.tar.gz'),
                                 content=u'No download')
        db_session.add(package)
        db_session.flush()

        request = testing.DummyRequest()
        request.matchdict = {'package': 'foo', 'kind': 'source',
                             'letter': 'f', 'basename': 'foo-1.2.tar.gz'}

        response = download_package(request)
        assert u'No download' == response.body

    def test_obtains_missing_file_from_pypi(self, tmpdir, http, db_session):
        from ..views import download_package

        pkg = tmpdir.join('foo-1.2.tar.gz')
        package = create_package(pkg, content=u'Short lived')

        # remove just the package file, not the record
        pkg.remove()
        db_session.add(package)
        db_session.flush()

        url = pypi_url(pypi_base_url, 'source', 'f', 'foo', 'foo-1.2.tar.gz')
        HTTPretty.register_uri(HTTPretty.GET, url, body='GOT IT', status=200)

        request = testing.DummyRequest()
        request.matchdict = {'package': 'foo', 'kind': 'source',
                             'letter': 'f', 'basename': 'foo-1.2.tar.gz'}
        response = download_package(request)
        assert 'GOT IT' == response.body
