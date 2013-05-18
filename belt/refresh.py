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
        package = release.package
        if package.name in packages:
            continue
        packages[package.name] = package
        releases = [r.version for r in package.releases]
        release.modified = Delorean().datetime

        package_location = os.path.join(location, package.name)
        for rel in package_releases(package.name, package_location):
            if rel.version not in releases:
                package.releases.add(release)
        yield package
