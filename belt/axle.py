import re
import os
import errno
import shutil
import logging
import subprocess
from wheel.install import WHEEL_INFO_RE


logger = logging.getLogger(__name__)


ARCHIVE_SUFFIX = re.compile(
    r"(\.zip|\.tar\.gz|\.tgz|\.tar\.bz2|-py[23]\.\d-.*|\.win-amd64-py[23]\.\d\..*|\.win32-py[23]\.\d\..*)$",
    re.IGNORECASE)


def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as err:
        if err.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def split_package_name(name):
    # name_ = ARCHIVE_SUFFIX.sub('', name)
    pkg_name = re.split(r'-\d+', name, 1)[0]
    version = name[len(pkg_name) + 1:]
    version = ARCHIVE_SUFFIX.sub('', version)
    return pkg_name, version


def copy_wheels_to_pypi(wheel_dir, local_pypi):

    for wheel in os.listdir(wheel_dir):
        match = WHEEL_INFO_RE(wheel)
        if match is None:
            continue
        tags = match.groupdict()
        path_to_wheel = os.path.abspath(os.path.join(wheel_dir, wheel))

        package_dir = os.path.join(local_pypi, tags['name'])
        local_wheel = os.path.join(package_dir, os.path.basename(path_to_wheel))

        # TODO Should we create md5s as we do with source packages?
        if os.path.exists(local_wheel):
            continue

        mkdir_p(package_dir)
        shutil.copyfile(path_to_wheel, local_wheel)


def build_wheels(local_pypi, wheel_dir):

    built_wheels = []
    for wheel in os.listdir(wheel_dir):
        match = WHEEL_INFO_RE(wheel)
        if match is None:
            continue
        tags = match.groupdict()
        # path_to_wheel = os.path.abspath(os.path.join(wheel_dir, wheel))
        built_wheels.append(tags['namever'])

    for package_dir in os.listdir(local_pypi):
        dir_ = os.path.join(local_pypi, package_dir)
        for pkg in os.listdir(dir_):
            name = os.path.join(dir_, pkg)
            _, ext = os.path.splitext(name)
            if ext in ['.md5', '.whl']:
                continue
            package_name, version = split_package_name(pkg)
            package_name = '{}-{}'.format(package_name, version)
            if package_name in built_wheels:
                continue
            args = 'pip wheel --wheel-dir {} {}'.format(wheel_dir, name)
            subprocess.call(args, shell=True)
