import os.path


def test_get_local_packages(tmpdir):
    from ..utils import local_packages

    tmpdir.mkdir('py.test')
    tmpdir.mkdir('yolk')
    tmpdir.mkdir('coverage')

    package_names = local_packages(str(tmpdir))
    assert ['coverage', 'py.test', 'yolk'] == sorted(list(package_names))


def test_returns_empty_list_if_dir_is_empty(tmpdir):
    from ..utils import local_packages
    package_names = local_packages(str(tmpdir))
    assert [] == list(package_names)


def test_get_dir_for_package(tmpdir):
    from ..utils import local_versions
    yolk = tmpdir.mkdir('yolk').join('yolk.1.0.1.tar.gz')
    yolk.write('1')
    package_dir = str(tmpdir)
    assert ['yolk.1.0.1.tar.gz'] == local_versions(package_dir, 'yolk')


def test_returns_empty_list_if_no_local_versions(tmpdir):
    from ..utils import local_versions
    package_dir = str(tmpdir)
    assert [] == local_versions(package_dir, 'yolk')


def test_returns_empty_list_if_no_local_package_dir(tmpdir):
    from ..utils import local_versions
    package_dir = str(tmpdir)
    tmpdir.mkdir('yolk')
    assert [] == local_versions(package_dir, 'yolk')


def test_get_full_path_to_version(tmpdir):
    from ..utils import get_package
    yolk = tmpdir.mkdir('yolk').join('yolk.1.0.1.tar.gz')
    yolk.write('1')
    expected = os.path.join(str(tmpdir), 'yolk', 'yolk.1.0.1.tar.gz')
    package_dir = str(tmpdir)
    assert expected == get_package(package_dir, 'yolk', 'yolk.1.0.1.tar.gz')
