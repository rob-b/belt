import datetime
import fudge
from fudge.inspector import arg
from delorean import Delorean
from belt.tests import create_package, create_releases_for_package
from belt import models


class TestOutdatedReleases(object):

    def test_excludes_new_releases(self, tmpdir, db_session):
        from belt.refresh import outdated_releases

        pkg = tmpdir.join('foo-1.2.tar.gz')
        package = create_package(pkg, content=u'Short lived')
        db_session.add(package)
        db_session.flush()

        # in a search for releases that were last modified before 2010-01-01 we
        # trust that a newly created package's release won't be found
        releases = outdated_releases(db_session,
                                     last_modified_at=datetime.datetime(2010, 1, 1))
        assert 0 == len(releases)

    def test_returns_only_outdated_releases(self, tmpdir, db_session):
        from belt.refresh import outdated_releases

        pkg = tmpdir.join('bar-1.0.tar.gz')
        package = create_package(pkg, content=u'n/a')

        # a datetime for 1st release and a datetime for the point against which we
        # consider releases outdated and in need of refreshing
        first_release_date = Delorean(datetime.datetime(1978, 1, 1), u'UTC').datetime
        jan_1st = datetime.datetime(2010, 1, 1)

        # change the modified timestamp of the 1st release to be in the past.
        # Create a new release and trust that its modified stamp will be newer
        # than 2010-01-01
        rel, = package.releases
        rel.modified = first_release_date
        new_release = models.Release(version=u'1.3')
        package.releases.add(new_release)

        db_session.add(package)
        db_session.flush()

        releases = outdated_releases(db_session, last_modified_at=jan_1st)
        assert 1 == len(releases)


class TestRefreshPackages(object):

    def test_updates_package_release_modified(self, db_session, tmpdir):
        from belt.refresh import refresh_packages

        modified = Delorean(datetime.datetime(1999, 10, 5), timezone='UTC')
        package = create_releases_for_package(tmpdir.join('lemon-3.0.tar.gz'),
                                              '1.4', '1.2.3',
                                              modified=modified.datetime)
        db_session.add(package)
        db_session.flush()

        original_modification_times = [rel.modified for rel in package.releases]

        with fudge.patch('belt.refresh.package_releases') as package_releases:
            (package_releases.expects_call()
             .with_args('lemon', '/na/lemon', ['1.4', '1.2.3']).returns([]))

            package = list(refresh_packages(db_session,
                                            datetime.datetime.utcnow(),
                                            '/na'))[0]

        new_modification_times = [rel.modified for rel in package.releases]

        results = [original < new for original, new in zip(original_modification_times,
                                                           new_modification_times)]
        assert all(results)
