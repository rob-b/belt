import datetime
from delorean import Delorean
from belt.tests import create_package
from belt import models


def test_excludes_new_release(tmpdir, db_session):
    from belt.refresh import outdated_packages

    pkg = tmpdir.join('foo-1.2.tar.gz')
    package = create_package(pkg, content=u'Short lived')
    db_session.add(package)
    db_session.flush()

    packages = outdated_packages(datetime.datetime(2010, 1, 1))
    assert 0 == len(packages)


def test_returns_package_with_any_matching_release(tmpdir, db_session):
    from belt.refresh import outdated_packages

    pkg = tmpdir.join('bar-1.0.tar.gz')
    package = create_package(pkg, content=u'n/a')

    # a datetime for 1st release and a datetime for the offset against which we
    # consider releases outdated
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

    packages = outdated_packages(last_modified_at=jan_1st)
    assert 1 == len(packages)


def test_it():
    from belt.refresh import refresh_packages
    since = datetime.datetime(2013, 5, 5)
    updates = []
    for pkg in refresh_packages(since):
        updates.append(pkg)
