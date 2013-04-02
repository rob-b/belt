import os
import errno
import shutil
import logging
from wheel.install import WHEEL_INFO_RE


logger = logging.getLogger(__name__)


def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as err:
        if err.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def get_wheels(wheel_dir, local_pypi):

    for pkg in os.listdir(wheel_dir):
        match = WHEEL_INFO_RE(pkg)
        if match is None:
            continue
        tags = match.groupdict()
        path_to_wheel = os.path.abspath(os.path.join(wheel_dir, pkg))

        package_dir = os.path.join(local_pypi, tags['name'])
        local_wheel = os.path.join(package_dir, os.path.basename(path_to_wheel))

        # TODO Should we create md5s as we do with source packages?
        if os.path.exists(local_wheel):
            continue

        mkdir_p(package_dir)
        shutil.copyfile(path_to_wheel, local_wheel)
