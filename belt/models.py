from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker, relationship
from zope.sqlalchemy import ZopeTransactionExtension

from sqlalchemy import (Column, Integer, Text, Boolean, ForeignKey)


DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
Base = declarative_base()


class Package(Base):

    __tablename__ = 'package'
    id = Column(Integer, primary_key=True)
    name = Column(Text, unique=True)
    releases = relationship('Release', backref='package')

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return u'package: {}'.format(self.name)


class Release(Base):
    __tablename__ = 'release'
    id = Column(Integer, primary_key=True)
    local = Column(Boolean, default=True)
    package_id = Column(Integer, ForeignKey('package.id'))
    version = Column(Text)
    path = Column(Text, unique=True)

    def __init__(self, version, path=None, local=True):
        self.local = local
        self.version = version
        self.path = path

    def __repr__(self):
        return u'release: {}-{}'.format(self.package.name, self.version)


def seed_packages(package_proxies):

    packages = []
    for name, versions in package_proxies.items():
        package = Package(name=name)
        for version in versions:
            package.releases.append(Release(version.number, path=version.path))
        packages.append(package)
    return packages
