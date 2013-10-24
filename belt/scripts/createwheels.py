import logging
import transaction
from belt.models import DBSession
from belt.axle import (build_wheels, copy_wheels_to_pypi,
                       add_generated_wheels_to_releases)
from sqlalchemy import engine_from_config
from pyramid.paster import (
    get_appsettings,
    setup_logging,
)


log = logging.getLogger('belt.scripts.createwheels')


def _build_wheels():
    import argparse
    parser = argparse.ArgumentParser(description='Build wheels from packages')
    parser.add_argument('config_file')
    parser.add_argument('--wheel-dir', help='Directory to store wheels in',
                        required=True)
    parser.add_argument('--pypi-dir',
                        help='Directory packages can be found in',
                        required=True)
    args = parser.parse_args()

    config_uri = args.config_file
    setup_logging(config_uri)

    settings = get_appsettings(config_uri)
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)

    with transaction.manager:
        build_wheels(args.pypi_dir, args.wheel_dir)
        copy_wheels_to_pypi(args.wheel_dir, args.pypi_dir)
        add_generated_wheels_to_releases(DBSession, args.wheel_dir,
                                         args.pypi_dir)


if __name__ == "__main__":
    _build_wheels()
