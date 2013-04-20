import os
import pytest
from belt import models


def test_seed(tmpdir):
    from ..models import seed_packages
    yolk = tmpdir.mkdir('quux').join('quux-2.0.zip')
    yolk.write('')

    pkg, = seed_packages(str(tmpdir))
    expected = os.path.join(str(tmpdir), 'quux', 'quux-2.0.zip')
    rel, = pkg.releases
    rel_file, = rel.files
    assert expected == rel_file.filename


@pytest.fixture
def session(request):
    from sqlalchemy import create_engine
    engine = create_engine('sqlite://', echo=False)

    from sqlalchemy.orm import scoped_session, sessionmaker
    Session = scoped_session(sessionmaker())

    models.Base.metadata.create_all(engine)
    Session.configure(bind=engine)

    connection = engine.connect()
    trans = connection.begin()

    def fin():
        trans.rollback()
    request.addfinalizer(fin)
    return Session


class TestModel(object):

    def test_something(self, session):
        package = models.Package(name='foo')
        session.add(package)
        rel = models.Release(version=u'1.2')
        package.releases.append(rel)
        rel = session.query(models.Release).one()
