import re
import os
import urllib2
import logging
import urlparse
from .values import Path, ReleaseValue


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
    import lxml.html
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
    return [ReleaseValue(version, package_dir) for version in candidates if not version.endswith('.md5')]


def get_package(packages_root, package_name, package_version):
    return Path(os.path.join(packages_root, package_name, package_version))


def get_package_from_pypi(url):
    return get_url(url)


def pypi_url(pypi_base_url, kind, package_name, basename):
    return '{}/{}/{}/{}/{}'.format(pypi_base_url.rstrip('/'), kind,
                                   package_name[0],
                                   package_name, basename)


def store_locally(path, fo):
    dirname = os.path.dirname(path)
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    with open(path, 'w') as package:
        package.write(fo.read())


def get_search_names(name):
    parts = re.split('[-_]', name)
    if len(parts) == 1:
        return parts

    result = set()
    for i in range(len(parts) - 1, 0, -1):
        for s1 in '-_':
            prefix = s1.join(parts[:i])
            for s2 in '-_':
                suffix = s2.join(parts[i:])
                for s3 in '-_':
                    result.add(s3.join([prefix, suffix]))
    return list(result)
