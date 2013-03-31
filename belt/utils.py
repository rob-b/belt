import os
import urllib2
import logging


class Path(object):

    def __init__(self, path):
        self.path = path

    @property
    def exists(self):
        return os.path.exists(self.path)


logger = logging.getLogger(__name__)


def local_packages(packages_root):
    for item in os.listdir(packages_root):
        if os.path.isdir(os.path.join(packages_root, item)):
            yield item


def local_versions(packages_root, package_name):
    package_dir = os.path.join(packages_root, package_name)
    return os.listdir(package_dir) if os.path.exists(package_dir) else []


def get_package(packages_root, package_name, package_version):
    return Path(os.path.join(packages_root, package_name, package_version))


def get_package_from_pypi(url):
    try:
        fo = urllib2.urlopen(url)
    except urllib2.URLError as err:
        if hasattr(err, 'reason'):
            msg = u"Failed to connect to server because: " + err.reason
        if hasattr(err, 'code'):
            msg = u'Failed to complete response with error code: %d' % err.code
        logger.error("Failed to retrieve " + url)
        logger.exception(msg)
        raise
    return fo


def pypi_url(pypi_base_url, kind, letter, package_name, package_version):
    return '{}/{}/{}/{}/{}'.format(pypi_base_url.rstrip('/'), kind, letter,
                                   package_name, package_version)


def store_locally(path, fo):
    dirname = os.path.dirname(path)
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    with open(path, 'w') as package:
        package.write(fo.read())
