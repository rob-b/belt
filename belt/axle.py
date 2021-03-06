import re
import os
import glob
import errno
import shutil
import logging
import urllib2
import xmlrpclib
import subprocess
from hashlib import md5
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

    wheel_match = WHEEL_INFO_RE(name)
    if wheel_match:
        pkg_name = wheel_match.group('name')
        version = wheel_match.group('ver')
    else:
        pkg_name = re.split(r'-\d+', name, 1)[0]
        version = name[len(pkg_name) + 1:]
        version = ARCHIVE_SUFFIX.sub('', version)
    return pkg_name, version


class WheelDestination(object):

    def __init__(self, local_pypi, name, version):
        self.local_pypi = local_pypi
        self.name = name
        self.version = version
        self._path = None

    @property
    def path(self):
        if self._path is None:
            # wheel converts hyphens in package names into underscores and
            # so there may be a cov-core dir that already exists but just
            # going by the wheel name we'd create cov_core
            package_dir = os.path.join(self.local_pypi, self.name)

            hyphenated = self.name.replace('_', '-')
            possible = os.path.join(self.local_pypi, hyphenated)
            if os.path.exists(possible):
                stem = '{}-{}'.format(hyphenated, self.version)
                stem = os.path.join(possible, stem)

                alt = (possible for ca in glob.iglob(possible + '/*') if
                       ARCHIVE_SUFFIX.sub('', ca) == stem)
                package_dir = next(alt, package_dir)
            self._path = package_dir
        return self._path


def copy_wheels_to_pypi(wheel_dir, local_pypi):
    for wheel in os.listdir(wheel_dir):
        match = WHEEL_INFO_RE(wheel)
        if match is None:
            continue
        tags = match.groupdict()
        path_to_wheel = os.path.abspath(os.path.join(wheel_dir, wheel))
        wheel_destination = WheelDestination(local_pypi, tags['name'], tags['ver'])
        local_wheel = os.path.join(wheel_destination.path, os.path.basename(path_to_wheel))

        if os.path.exists(local_wheel):
            continue

        mkdir_p(wheel_destination.path)
        shutil.copyfile(path_to_wheel, local_wheel)


def get_all_wheels(session, wheel_dir):
    from belt import models

    class Whl(object):

        def __init__(self, matchdict, wheel_dir, wheel):
            self.__dict__.update(matchdict)
            self.wheel_dir = wheel_dir
            self.wheel = wheel

        @property
        def path(self):
            if not hasattr(self, '_path'):
                self._path = os.path.abspath(os.path.join(self.wheel_dir, self.wheel))
            return self._path
    wheels = (session.query(models.File)
              .filter(models.File.filename.like("%whl")).all())
    wheels = [wheel.filename for wheel in wheels if
              os.path.exists(wheel.fullpath)]
    wheels = set(os.listdir(wheel_dir)).difference(wheels)
    for wheel in wheels:
        match = WHEEL_INFO_RE(wheel)
        if match is None:
            continue
        yield Whl(match.groupdict(), wheel_dir, wheel)


def add_generated_wheels_to_releases(session, wheel_dir, local_pypi):
    from belt import models
    from sqlalchemy.orm.exc import NoResultFound
    releases = {}
    for wheel in get_all_wheels(session, wheel_dir):

        # FIXME more name inconsistency
        name = wheel.name.lower()
        if name not in releases:
            try:
                releases[name] = models.Release.for_package(wheel.name, wheel.ver)
            except NoResultFound:
                continue
        release = releases[name]

        with open(wheel.path) as fo:
            hashed_content = md5(fo.read()).hexdigest()

        filename = os.path.basename(wheel.path)
        location = os.path.join(local_pypi, release.package.name)
        rel_file = models.File(md5=hashed_content,
                               location=location,
                               filename=filename,
                               kind=wheel.pyver)
        release.files.add(rel_file)


def build_wheels(local_pypi, wheel_dir):
    from belt.utils import get_search_names

    built_wheels = []
    for wheel in os.listdir(wheel_dir):
        match = WHEEL_INFO_RE(wheel)
        if match is None:
            continue
        tags = match.groupdict()
        # path_to_wheel = os.path.abspath(os.path.join(wheel_dir, wheel))
        built_wheels.append(tags['namever'].lower())

    for package_dir in os.listdir(local_pypi):
        dir_ = os.path.join(local_pypi, package_dir)
        for pkg in os.listdir(dir_):
            name = os.path.join(dir_, pkg)
            _, ext = os.path.splitext(name)
            if ext in ['.md5', '.whl']:
                continue
            package_name, version = split_package_name(pkg)
            package_name = '{}-{}'.format(package_name, version)

            # FIXME why are names inconsistent forcing us to check both
            # variations?
            options = get_search_names(package_name)
            for opt in options:
                if opt.lower() in built_wheels:
                    break
            else:
                args = 'pip wheel --wheel-dir {} {}'.format(wheel_dir, name)
                subprocess.call(args, shell=True)


def get_xmlrpc_client():
    return xmlrpclib.ServerProxy('https://pypi.python.org/pypi')


def get_package_name(name, client=None):
    client = client or get_xmlrpc_client()
    r = urllib2.Request('http://pypi.python.org/simple/{0}'.format(name))
    return urllib2.urlopen(r).geturl().split('/')[-2]


def package_releases(package, location, skip_versions=None, client=None):
    from belt import models
    client = client or get_xmlrpc_client()
    skip_versions = skip_versions or []
    logger.debug('Obtaining releases for ' + package)
    for version in client.package_releases(package, True):
        if version in skip_versions:
            continue
        rel = models.Release(version=version)
        logger.debug('Found {}-{}'.format(package, version))
        for pkg_data in client.release_urls(package, version):
            rel_file = models.File(md5=pkg_data['md5_digest'],
                                   download_url=pkg_data['url'],
                                   location=location,
                                   filename=pkg_data['filename'],
                                   kind=pkg_data['python_version'])
            rel.files.add(rel_file)
        yield rel
