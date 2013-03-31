import os
import urllib2
import logging
from hashlib import md5


logger = logging.getLogger(__name__)


class Path(object):

    def __init__(self, path):
        self.path = path

    @property
    def exists(self):
        return os.path.exists(self.path)


class Version(object):

    _md5 = ''

    def __init__(self, name, package_dir):
        self.name = name
        self.package_dir = package_dir

    def __eq__(self, other):
        return self.name == other

    def __repr__(self):
        return self.name

    @property
    def md5(self):
        if not self._md5:

            hash_name = os.path.join(self.package_dir, self.name) + '.md5'
            try:
                with open(hash_name) as hashed:
                    self._md5 = hashed.read()
            except IOError:
                msg = u'{} does not exist'.format(hash_name)
                logging.exception(msg)
        return self._md5


logger = logging.getLogger(__name__)


def local_packages(packages_root):
    for item in os.listdir(packages_root):
        if os.path.isdir(os.path.join(packages_root, item)):
            yield item


def local_versions(packages_root, package_name):
    package_dir = os.path.join(packages_root, package_name)
    candidates = os.listdir(package_dir) if os.path.exists(package_dir) else []
    return [Version(version, package_dir) for version in candidates if not version.endswith('.md5')]


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

    with open(path) as package:
        with open(path + '.md5', 'w') as hashed:
            hashed.write(md5(package.read()).hexdigest())
