from belt import models
from belt.axle import package_releases
from delorean import Delorean


def outdated_packages(last_modified_at):
    return (models.DBSession
            .query(models.Package)
            .filter(models.Release.modified < last_modified_at)
            .limit(8))


def refresh_packages(last_modified_at):
    for package in outdated_packages(last_modified_at):
        releases = [r.version for r in package.releases]

        for release in package_releases(package.name):
            if release.version not in releases:
                release.modified = Delorean().datetime
                package.releases.add(release)
        yield package
