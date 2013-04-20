import os
from hashlib import md5
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker, relationship
from zope.sqlalchemy import ZopeTransactionExtension

from sqlalchemy import (Column, Integer, Text, Boolean, ForeignKey, DateTime,
                        func, UniqueConstraint, or_)
from .utils import local_packages, local_releases, get_search_names


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

    @classmethod
    def by_name(cls, name):
        names = get_search_names(name)
        or_query = or_(*[Package.name == n for n in names])
        return DBSession.query(Package).filter(or_query).one()


class Release(Base):
    __tablename__ = 'release'
    id = Column(Integer, primary_key=True)
    local = Column(Boolean, default=False)
    package_id = Column(Integer, ForeignKey('package.id'))
    version = Column(Text)
    download_url = Column(Text, unique=True)
    created = Column(DateTime(timezone=True), nullable=False,
                     server_default=func.now())
    modified = Column(DateTime(timezone=True), nullable=False,
                      server_default=func.now(), onupdate=func.now())
    files = relationship('File', backref='release')

    __table_args__ = (UniqueConstraint('version', 'package_id'), )

    def __repr__(self):
        if self.package:
            pkg_name = self.package.name
        else:
            pkg_name = u'UNKNOWN'
        return u'release: {}-{}'.format(pkg_name, self.version)


class File(Base):
    __tablename__ = 'file'
    id = Column(Integer, primary_key=True)
    created = Column(DateTime(timezone=True), nullable=False,
                     server_default=func.now())
    modified = Column(DateTime(timezone=True), nullable=False,
                      server_default=func.now(), onupdate=func.now())
    release_id = Column(Integer, ForeignKey('release.id'))
    filename = Column(Text, nullable=False, default=u'')
    md5 = Column(Text, nullable=False, default=u'')
    kind = Column(Text, nullable=False, default='source')

    @property
    def basename(self):
        return os.path.basename(self.filename)

    @classmethod
    def for_release(self, package, version):
        return (DBSession
                .query(File)
                .join(File.release, Release.package)
                .filter(Release.version == version, Package.name == package)
                .one())


def seed_packages(package_dir):
    packages = []
    for pkg in local_packages(package_dir):
        package = Package(name=pkg)
        for rel in local_releases(package_dir, pkg):
            root, ext = os.path.splitext(rel.fullpath)
            if ext in ('.md5'):
                continue
            release = Release(version=rel.number)

            with open(rel.fullpath) as fo:
                hashed_content = md5(fo .read()).hexdigest()
            release.files.append(File(filename=rel.fullpath, md5=hashed_content))
            package.releases.append(release)
        packages.append(package)
    return packages
