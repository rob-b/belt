import os
import urllib2
import logging
import urlparse
import lxml.html
from hashlib import md5
from .values import Path, Version


logger = logging.getLogger(__name__)


def get_url(url):
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


def local_packages(packages_root):
    for item in os.listdir(packages_root):
        if os.path.isdir(os.path.join(packages_root, item)):
            yield item


def pypi_versions(package_page, url=None):
    html = lxml.html.fromstring(package_page)
    if url:
        html.make_links_absolute(url)
    links = []
    for elem, attr, link, pos in html.iterlinks():
        if elem.tag != 'a':
            continue
        if elem.attrib.get('rel', '') == 'homepage':
            continue
        links.append(lxml.html.tostring(elem))
    return links


def pypi_package_page(url):
    url = convert_url_to_pypi(url)
    return get_url(url).read()


def convert_url_to_pypi(url):
    # TODO define pypi url once only
    base = 'https://pypi.python.org'
    return urlparse.urljoin(base, urlparse.urlsplit(url).path)


def local_releases(packages_root, package_name):
    package_dir = os.path.join(packages_root, package_name)
    candidates = os.listdir(package_dir) if os.path.exists(package_dir) else []
    return [Version(version, package_dir) for version in candidates if not version.endswith('.md5')]


def get_package(packages_root, package_name, package_version):
    return Path(os.path.join(packages_root, package_name, package_version))


def get_package_from_pypi(url):
    return get_url(url)


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
