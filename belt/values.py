import os
import logging
from .axle import split_package_name


logger = logging.getLogger(__name__)


class Path(object):

    def __init__(self, path):
        self.path = path

    @property
    def exists(self):
        return os.path.exists(self.path)


class ReleaseValue(object):

    _md5 = ''

    def __init__(self, name, package_dir):
        self.name, self.number = split_package_name(name)
        self.fullname = name

        self.package_dir = package_dir

    def __eq__(self, other):
        return self.fullname == other

    def __repr__(self):
        return self.fullname

    @property
    def md5(self):
        if not self._md5:

            hash_name = self.fullpath + '.md5'
            try:
                with open(hash_name) as hashed:
                    self._md5 = hashed.read()
            except IOError:
                # msg = u'{} does not exist'.format(hash_name)
                # logger.exception(msg)
                pass
        return self._md5

    @property
    def fullpath(self):
        return os.path.join(self.package_dir, self.fullname)
