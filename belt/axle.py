import re
import os
import errno
import shutil
import logging
import urllib2
import xmlrpclib
import subprocess
import collections
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


def get_xmlrpc_client():
    return xmlrpclib.ServerProxy('https://pypi.python.org/pypi')


def get_package_name(name, client=None):
    client = client or get_xmlrpc_client()
    r = urllib2.Request('http://pypi.python.org/simple/{0}'.format(name))
    return urllib2.urlopen(r).geturl().split('/')[-2]


def package_releases(package, location=None, client=None):
    from belt import models
    client = client or get_xmlrpc_client()
    logger.debug('Obtaining releases for ' + package)
    for version in client.package_releases(package, True):
        logger.debug('Found {}-{}'.format(package, version))
        for pkg_data in client.release_urls(package, version):
            rel = models.Release(version=version)
            rel_file = models.File(md5=pkg_data['md5_digest'],
                                   download_url=pkg_data['url'],
                                   location=location or u'',
                                   filename=pkg_data['filename'],
                                   kind=pkg_data['python_version'])
            rel.files.append(rel_file)
            yield rel


def release_union(releases):
    keep = collections.defaultdict(list)
    for rel in releases:
        keep[rel.version].append(rel)

    for v in keep.values():
        yield sorted(v, key=lambda i: i.id, reverse=True)[0]


def create_release(version, url):
    from belt import models
    from belt.utils import get_package_from_pypi
    pkg = get_package_from_pypi(url)
    rel = models.Release(version=version, download_url=url)
