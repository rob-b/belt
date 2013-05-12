import os
import itertools
import fudge
import pytest
import py.test
from belt import models
from sqlalchemy import exc


def test_move_wheels_to_pypi_dir(tmpdir):
    from ..axle import copy_wheels_to_pypi

    wh = tmpdir.join('belt-0.2-py27-none-any.whl')
    wh.write('')

    pypi = tmpdir.mkdir('local')

    copy_wheels_to_pypi(wheel_dir=str(tmpdir), local_pypi=str(pypi))

    expected = os.path.join(str(pypi), 'belt', 'belt-0.2-py27-none-any.whl')
    assert os.path.exists(expected)


def test_doesnt_overwrite_existing_wheels(tmpdir):
    from ..axle import copy_wheels_to_pypi

    built_wheel = tmpdir.join('belt-0.2-py27-none-any.whl')
    built_wheel.write('')

    local_pypi = tmpdir.mkdir('local')
    package_wheel = local_pypi.mkdir('belt').join('belt-0.2-py27-none-any.whl')
    package_wheel.write('')

    with fudge.patch('belt.axle.shutil') as shutil:
        shutil.provides('copyfile').times_called(0)
        copy_wheels_to_pypi(wheel_dir=str(tmpdir), local_pypi=str(local_pypi))


@pytest.mark.parametrize(('package', 'name_and_version'), [
    ('bump-0.1.0.tar.gz', ('bump', '0.1.0')),
    ('fudge-22.1.4.zip', ('fudge', '22.1.4')),
    ('wheel-1.0.0a1.tar.bz2', ('wheel', '1.0.0a1')),
])
def test_split_package_name_detects_name(package, name_and_version):
    from ..axle import split_package_name
    assert name_and_version == split_package_name(package)


belt_pkg_data = [
    {'comment_text': '',
     'downloads': 120,
     'filename': 'belt-0.5.tar.gz',
     'has_sig': False,
     'md5_digest': '5cdf19d11ccd9f3cb0becb3f07284ce1',
     'packagetype': 'sdist',
     'python_version': 'source',
     'size': 26173,
     'upload_time': '20130506T21:05:11',
     'url':
     'http://pypi.python.org/packages/source/b/belt/belt-0.5.tar.gz'},
    {'comment_text': '',
     'downloads': 133,
     'filename': 'belt-0.5.zip',
     'has_sig': False,
     'md5_digest': 'f7429b4f1ca327102e001f91928b23be',
     'packagetype': 'sdist',
     'python_version': 'source',
     'size': 35259,
     'upload_time': '20130506T21:05:11',
     'url': 'http://pypi.python.org/packages/source/b/belt/belt-0.5.zip'}]


class TestGetReleaseData(object):

    def test_sets_release_version(self):
        from ..axle import package_releases
        client = (fudge.Fake('client')
                  .expects('release_urls').with_args('belt', '0.5')
                  .returns(belt_pkg_data)
                  .expects('package_releases').with_args('belt', True)
                  .returns(['0.5']))
        release, = package_releases('belt', client=client)
        assert u'0.5' == release.version

    def test_sets_release_file_md5(self):
        from ..axle import package_releases
        client = (fudge.Fake('client')
                  .expects('release_urls').with_args('belt', '0.3')
                  .returns(belt_pkg_data)
                  .expects('package_releases').with_args('belt', True)
                  .returns(['0.3']))
        release, = package_releases('belt', client=client)
        assert 'f7429b4f1ca327102e001f91928b23be' == release.files[1].md5

    def test_returns_list_of_releases_to_add_to_package(self, db_session):
        from ..axle import package_releases
        client = (fudge.Fake('client')
                  .expects('release_urls').returns(belt_pkg_data)
                  .expects('package_releases').returns(['0.1']))
        pkg = models.Package(name=u'belt')
        db_session.add(pkg)

        releases = package_releases('belt', client=client)
        pkg.releases.extend(list(releases))
        pkg = db_session.query(models.Package).filter_by(name='belt').one()
        assert 1 == len(pkg.releases)

    def test_release_list_does_not_guarantee_uniqueness(self, db_session):
        from ..axle import package_releases
        client = (fudge.Fake('client')
                  .expects('release_urls').returns(belt_pkg_data)
                  .expects('package_releases').returns(['0.1']))

        # add a package named belt with a 0.1 release
        pkg = models.Package(name=u'belt')
        pkg.releases.append(models.Release(version=u'0.1'))
        db_session.add(pkg)

        releases = package_releases('belt', client=client)

        # add the returned packages and flushing should cause an
        # IntegrityError because of two releases of the same name
        pkg.releases.extend(list(releases))

        with py.test.raises(exc.IntegrityError):
            db_session.flush()


def eq_(a, b):
    assert a == b


class TestReleaseUnion(object):

    def test_removes_release_with_duplicate_version(self):
        from ..axle import release_union

        releases = (models.Release(version=u'1.2.4'),
                    models.Release(version=u'1.2.4'))

        releases = release_union(releases)

        assert 1 == len(list(releases))

    def test_retains_releases_with_distinct_versions(self):
        from ..axle import release_union

        releases = (models.Release(version=u'1.2.4'),
                    models.Release(version=u'1.2.5'))
        expected = [u'1.2.4', u'1.2.5']

        releases = release_union(releases)

        for expect, got in itertools.izip_longest(expected, releases):
            yield eq_, expect, got.version

    def test_prefers_releases_with_ids(self, db_session):
        from ..axle import release_union

        pkg = models.Package(name=u'belt')
        pkg.releases.append(models.Release(version=u'1.2.4'))

        releases = (models.Release(version=u'1.2.4'),
                    models.Release(version=u'1.2.4'),
                    pkg.releases[0])
        db_session.add(pkg)
        db_session.flush()

        release, = release_union(releases)
        assert release.id is not None
