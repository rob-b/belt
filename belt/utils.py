import os
import urllib2
import logging


logger = logging.getLogger(__name__)


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


def get_package_from_pypi(url):
    try:
        fo = urllib2.urlopen(url)
    except urllib2.URLError as err:
        if hasattr(err, 'reason'):
            msg = u"Failed to connect to server because: " + err.reason
        if hasattr(err, 'code'):
            msg = u'Failed to complete response with error code: %d' % err.code
        logger.exception(msg)
        raise
    return fo


def pypi_url(pypi_base_url, kind, letter, package_name, package_version):
    return '{}/{}/{}/{}/{}'.format(pypi_base_url.rstrip('/'), kind, letter,
                                   package_name, package_version)


def store_locally():
    pass
