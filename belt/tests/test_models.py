import os
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

    def test_ignores_filename_for_whl_files(self, tmpdir):
        from ..models import seed_packages
        quux = tmpdir.mkdir('quux').join('quux-1.1-py27-none-any.whl')
        quux.write('')

        pkg, = seed_packages(str(tmpdir))
        assert 0 == len(pkg.releases)

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
        quux = tmpdir.mkdir('quux').join('quux-1.1.tgz')
        quux.write('')

        quux = tmpdir.join('quux', 'quux-1.1.zip')
        quux.write('')

        pkg, = seed_packages(str(tmpdir))
        release, = pkg.releases
        assert 2 == len(release.files)


class TestPackageByName(object):

    def test_is_case_insensitive(self, db_session):
        pkg = models.Package(name='Foo')
        db_session.add(pkg)
        assert 'Foo' == models.Package.by_name('foo').name


def test_uppercase_filename_not_found(db_session):
    file = models.File(filename='UPPER',
                       location='/tmp')
    db_session.add(file)
    db_session.flush()
    assert None is db_session.query(models.File).filter_by(filename='UPPER').first()


def test_filename_saved_as_lower_case(db_session):
    file = models.File(filename='upper',
                       location='/tmp')
    db_session.add(file)
    db_session.flush()
    assert None is not db_session.query(models.File).filter_by(filename='upper').first()
