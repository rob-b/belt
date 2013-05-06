import os
import pytest
from belt import models


class TestSeedPackages(object):

    def test_handles_zip_files(self, tmpdir):
        from ..models import seed_packages
        quux = tmpdir.mkdir('quux').join('quux-2.0.zip')
        quux.write('')

        pkg, = seed_packages(str(tmpdir))
        expected = os.path.join(str(tmpdir), 'quux', 'quux-2.0.zip')
        rel, = pkg.releases
        rel_file, = rel.files
        assert expected == rel_file.fullpath

    def test_sets_filename_for_whl_files(self, tmpdir):
        from ..models import seed_packages
        quux = tmpdir.mkdir('quux').join('quux-1.1-py27-none-any.whl')
        quux.write('')

        pkg, = seed_packages(str(tmpdir))
        expected = os.path.join(str(tmpdir), 'quux',
                                'quux-1.1-py27-none-any.whl')
        rel, = pkg.releases
        rel_file, = rel.files
        assert expected == rel_file.fullpath

    def test_detects_version_for_whl_files(self, tmpdir):
        from ..models import seed_packages
        quux = tmpdir.mkdir('quux').join('quux-1.1-py27-none-any.whl')
        quux.write('')

        pkg, = seed_packages(str(tmpdir))
        rel, = pkg.releases
        assert u'1.1' == rel.version

    def test_groups_releases(self, tmpdir):
        from ..models import seed_packages
        quux = tmpdir.mkdir('quux').join('quux-1.1-py27-none-any.whl')
        quux.write('')

        quux = tmpdir.join('quux', 'quux-1.1.zip')
        quux.write('')

        pkg, = seed_packages(str(tmpdir))
        assert 1 == len(pkg.releases)

    def test_release_can_have_many_files(self, tmpdir):
        from ..models import seed_packages
        quux = tmpdir.mkdir('quux').join('quux-1.1-py27-none-any.whl')
        quux.write('')

        quux = tmpdir.join('quux', 'quux-1.1.zip')
        quux.write('')

        pkg, = seed_packages(str(tmpdir))
        release, = pkg.releases
        assert 2 == len(release.files)


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
