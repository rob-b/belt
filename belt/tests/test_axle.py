import os
import fudge
import pytest


def test_move_wheels_to_pypi_dir(tmpdir):
    from ..axle import copy_wheels_to_pypi

    wh = tmpdir.join('belt-0.2-py27-none-any.whl')
    wh.write('')

    py = tmpdir.mkdir('local')

    copy_wheels_to_pypi(wheel_dir=str(tmpdir), local_pypi=str(py))

    expected = os.path.join(str(py), 'belt', 'belt-0.2-py27-none-any.whl')
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


def test_build_wheels_from_packages(tmpdir):
    from ..axle import build_wheels
    build_wheels('/vagrant/pypi', '/vagrant/wheelhouse')


@pytest.mark.parametrize(('package', 'name_and_version'), [
    ('bump-0.1.0.tar.gz', ('bump', '0.1.0')),
    ('fudge-22.1.4.zip', ('fudge', '22.1.4')),
    ('wheel-1.0.0a1.tar.bz2', ('wheel', '1.0.0a1')),
])
def test_split_package_name_detects_name(package, name_and_version):
    from ..axle import split_package_name
    assert name_and_version == split_package_name(package)
