import os
from belt import models
from belt.axle import package_releases
from delorean import Delorean


def outdated_releases(session, last_modified_at):
    return (session
            .query(models.Release)
            .join(models.Package.releases)
            .filter(models.Release.modified < last_modified_at)
            .all())


def refresh_packages(session, last_modified_at, location):
    packages = {}
    for release in outdated_releases(session, last_modified_at):
        release.modified = Delorean().datetime
        package = release.package
        if package.name in packages:
            continue
        packages[package.name] = package
        versions = [r.version for r in package.releases]

        package_location = os.path.join(location, package.name)
        for rel in package_releases(package.name, package_location, versions):
            if rel.version not in versions:
                package.releases.add(rel)
        yield package
