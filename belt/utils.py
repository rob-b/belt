import os


def local_packages(packages_root):
    for item in os.listdir(packages_root):
        if os.path.isdir(os.path.join(packages_root, item)):
            yield item


def local_versions(packages_root, package_name):
    package_dir = os.path.join(packages_root, package_name)
    return os.listdir(package_dir) if os.path.exists(package_dir) else []


def get_package(packages_root, package_name, package_version):
    path = os.path.join(packages_root, package_name, package_version)
    return path if os.path.exists(path) else None
