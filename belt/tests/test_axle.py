import os
import fudge


def test_move_wheels_to_pypi_dir(tmpdir):
    from ..axle import get_wheels

    wh = tmpdir.join('belt-0.2-py27-none-any.whl')
    wh.write('')

    py = tmpdir.mkdir('local')

    get_wheels(wheel_dir=str(tmpdir), local_pypi=str(py))

    expected = os.path.join(str(py), 'belt', 'belt-0.2-py27-none-any.whl')
    assert os.path.exists(expected)


def test_doesnt_overwrite_existing_wheels(tmpdir):
    from ..axle import get_wheels

    built_wheel = tmpdir.join('belt-0.2-py27-none-any.whl')
    built_wheel.write('')

    local_pypi = tmpdir.mkdir('local')
    package_wheel = local_pypi.mkdir('belt').join('belt-0.2-py27-none-any.whl')
    package_wheel.write('')

    with fudge.patch('belt.axle.shutil') as shutil:
        shutil.provides('copyfile').times_called(0)
        get_wheels(wheel_dir=str(tmpdir), local_pypi=str(local_pypi))
