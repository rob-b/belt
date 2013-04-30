import os
import logging
from hashlib import md5
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import (scoped_session, sessionmaker, relationship,
                            joinedload)
from zope.sqlalchemy import ZopeTransactionExtension

from sqlalchemy.ext.hybrid import Comparator, hybrid_property
from sqlalchemy import (Column, Integer, Text, Boolean, ForeignKey, DateTime,
                        func, UniqueConstraint, or_)
from .utils import local_packages, local_releases, get_search_names
from .axle import get_package_name, split_package_name


DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
Base = declarative_base()


log = logging.getLogger(__name__)


class CaseInsensitiveComparator(Comparator):
    def __eq__(self, other):
        return func.lower(self.__clause_element__()) == func.lower(other)


class Package(Base):

    __tablename__ = 'package'
    id = Column(Integer, primary_key=True)
    name = Column(Text, unique=True)
    releases = relationship('Release', backref='package',
                            cascade='all, delete-orphan', passive_deletes=True)

    def __init__(self, name, package_dir=None):
        self.name = name
        self.package_dir = package_dir

    def __repr__(self):
        return u'package: {}'.format(self.name)

    @hybrid_property
    def name_insensitive(self):
        return self.name.lower()

    @name_insensitive.comparator
    def name_insensitive(cls):
        return CaseInsensitiveComparator(cls.name)

    @classmethod
    def by_name(cls, name):
        names = get_search_names(name)
        or_query = or_(*[Package.name_insensitive == n for n in names])
        joined = joinedload(Package.releases, Release.files)
        return DBSession.query(Package).options(joined).filter(or_query).one()

    @classmethod
    def create_from_pypi(cls, name, package_dir):
        name = get_package_name(name)
        return cls(name=name, package_dir=package_dir)


class Release(Base):
    __tablename__ = 'release'
    __table_args__ = (UniqueConstraint('version', 'package_id'), )

    id = Column(Integer, primary_key=True)
    local = Column(Boolean, default=False)
    package_id = Column(Integer, ForeignKey('package.id', ondelete='CASCADE'))
    version = Column(Text)
    created = Column(DateTime(timezone=True), nullable=False,
                     server_default=func.now())
    modified = Column(DateTime(timezone=True), nullable=False,
                      server_default=func.now(), onupdate=func.now())
    files = relationship('File', backref='release')


    def __repr__(self):
        if self.package:
            pkg_name = self.package.name
        else:
            pkg_name = u'UNKNOWN'
        return u'release: {}-{}'.format(pkg_name, self.version)

    @classmethod
    def for_package(cls, package, version):
        return (DBSession.query(Release).join(Release.package)
                .filter(Release.version == version, Package.name == package)
                .one())


class File(Base):
    __tablename__ = 'file'
    __table_args__ = (UniqueConstraint('kind', 'release_id', 'filename'), )

    id = Column(Integer, primary_key=True)
    created = Column(DateTime(timezone=True), nullable=False,
                     server_default=func.now())
    modified = Column(DateTime(timezone=True), nullable=False,
                      server_default=func.now(), onupdate=func.now())
    release_id = Column(Integer, ForeignKey('release.id', ondelete='CASCADE'))
    location = Column(Text, nullable=False, default=u'')
    filename = Column(Text, nullable=False, default=u'')
    md5 = Column(Text, nullable=False, default=u'')
    kind = Column(Text, nullable=False, default='source')
    download_url = Column(Text, unique=True)

    @property
    def fullpath(self):
        return os.path.join(self.location, self.filename)

    @classmethod
    def for_release(cls, package, version):
        return (DBSession
                .query(File)
                .join(File.release, Release.package)
                .filter(Release.version == version, Package.name == package)
                .all())

    @classmethod
    def by_filename(cls, filename):
        name, version = split_package_name(filename)
        return (DBSession
                .query(File)
                .join(File.release, Release.package)
                .filter(Release.version == version,
                        Package.name_insensitive == name,
                        File.filename == filename)
                .one())


from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound


def get_or_create(session, model, defaults=None, **kwargs):
    query = session.query(model).filter_by(**kwargs)
    created = False
    try:
        instance = query.one()
    except NoResultFound:
        session.begin(nested=True)
        defaults = defaults or {}
        kwargs.update(defaults)
        instance = model(**kwargs)
        session.add(instance)
        try:
            session.flush()
        except IntegrityError:
            session.rollback()
            instance = query.one()
        else:
            created = True
    return instance, created


def seed_packages(package_dir):
    packages = []
    for pkg in local_packages(package_dir):
        releases = {}
        package = Package(name=pkg)
        for rel in local_releases(package_dir, pkg):
            root, ext = os.path.splitext(rel.fullpath)
            if ext in ['.md5']:
                continue

            release = releases.setdefault(rel.number,
                                          Release(version=rel.number))
            with open(rel.fullpath) as fo:
                hashed_content = md5(fo .read()).hexdigest()
            release.files.append(File(filename=rel.fullname,
                                      location=rel.package_dir, md5=hashed_content))
        for k, v in releases.items():
            package.releases.append(v)
        packages.append(package)
    return packages
