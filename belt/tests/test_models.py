from belt.views import Version


def test_creates_package_with_release():
    from belt.models import seed_packages

    pp = [Version('1.0.0', '/mnt'), Version('2.0', '/medoa')]
    packages = {'yolk': pp}
    package = seed_packages(packages)[0]
    assert len(package.releases) == 2


def test_a_packages_release_has_a_path():
    from belt.models import seed_packages

    pp = [Version('1.0.0', '/mnt')]
    packages = {'yolk': pp}
    package = seed_packages(packages)[0]
    assert package.releases[0].path == '/mnt'


def test_each_release_has_a_unique_path():
    from belt.models import seed_packages
    pp = [Version('1.0.0', '/mnt'), Version('2.0', '/medoa')]
    packages = {'yolk': pp}
    package = seed_packages(packages)[0]
    rel1, rel2 = package.releases
    assert rel1.path != rel2.path
