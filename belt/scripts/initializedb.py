import os
import sys
import transaction

from sqlalchemy import engine_from_config

from pyramid.paster import (
    get_appsettings,
    setup_logging,
)


from ..models import (
    DBSession,
    Base,
    seed_packages,
)


def usage(argv):
    cmd = os.path.basename(argv[0])
    print('usage: %s <config_uri> [<package_directory>]\n'
          '(example: "%s development.ini")' % (cmd, cmd))
    sys.exit(1)


def main(argv=sys.argv):
    if len(argv) not in [2, 3]:
        usage(argv)
    config_uri = argv[1]
    setup_logging(config_uri)
    settings = get_appsettings(config_uri)
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    Base.metadata.create_all(engine)

    package_dir = argv[2]
    with transaction.manager:
        for pkg in seed_packages(package_dir):
            DBSession.add(pkg)
