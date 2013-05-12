import os
from belt.axle import split_package_name
from belt import models


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
