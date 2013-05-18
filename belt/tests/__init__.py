import os
from belt.axle import split_package_name
from belt import models


def _create_package(path, content=u''):
    if content:
        path.write(content)
    basename = os.path.basename(str(path))
    name, version = split_package_name(basename)
    return models.Package(name=name)


def create_package(path, content=u''):

    if content:
        filename = str(path)
        path.write(content)
    else:
        filename = u''
    basename = os.path.basename(str(path))
    name, version = split_package_name(basename)

    package = models.Package(name=name)
    rel = models.Release(version=version)
    package.releases.add(rel)
    rel.files.add(models.File(filename=filename, md5='gg'))
    return package


def create_releases_for_package(path, *versions, **kwargs):
    modified = kwargs.get('modified')
    created = kwargs.get('created')
    content = kwargs.get('content', u'')

    package = _create_package(path, content)
    for suffix, version in enumerate(versions):
        rel = create_release(version, modified, created)
        rel.files.add(models.File(filename=u'File_{}'.format(suffix), md5=u'gg'))
        package.releases.add(rel)
    return package


def create_release(version, modified=None, created=None):
    return models.Release(version=version, modified=modified, created=created)
