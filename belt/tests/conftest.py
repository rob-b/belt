import os
import pytest
from belt import models
from httpretty import HTTPretty
from pyramid.paster import get_appsettings
from pyramid import testing
from sqlalchemy import engine_from_config


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))


@pytest.fixture
def http(request):
    HTTPretty.reset()
    HTTPretty.enable()
    request.addfinalizer(HTTPretty.disable)


@pytest.fixture(scope='session')
def connection(request):
    settings = get_appsettings(os.path.join(ROOT, 'test.ini'))
    engine = engine_from_config(settings, 'sqlalchemy.')
    models.Base.metadata.create_all(engine)
    connection = engine.connect()
    models.DBSession.registry.clear()
    models.DBSession.configure(bind=connection)
    models.Base.metadata.bind = engine
    request.addfinalizer(models.Base.metadata.drop_all)
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
