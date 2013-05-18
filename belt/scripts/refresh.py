import logging
import datetime
import argparse
from belt.refresh import refresh_packages
from sqlalchemy import engine_from_config
from sqlalchemy.orm import sessionmaker
from pyramid.paster import (
    get_appsettings,
    setup_logging,
)


log = logging.getLogger('belt.scripts.refresh')


def strptime(value):
    try:
        value = datetime.datetime.strptime(value, '%Y-%m-%d')
    except ValueError:
        msg = u'{} is not in YYYY-MM-DD format'.format(value)
        raise argparse.ArgumentTypeError(msg)

    if value.date() == datetime.date.today():
        value = value + datetime.timedelta(seconds=86399),
    return value


def main(location, older_than, session):

    packages = list(refresh_packages(session, older_than, location))
    suffix = '' if len(packages) == 1 else 's'
    msg = u'{} release{} unmodified since {} found'.format(len(packages),
                                                           suffix,
                                                           older_than.isoformat())
    log.info(msg)
    for package in packages:
        log.info(u'Updated ' + unicode(package))
        session.commit()

if __name__ == "__main__":
    description = u'Check for new releases of all locally known packages'
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('config_file')
    parser.add_argument('--older-than',
                        default=datetime.datetime.utcnow(),
                        type=strptime,
                        help=u'Refresh packages older than YYYY-MM-DD')

    args = parser.parse_args()

    config_uri = args.config_file
    setup_logging(config_uri)
    settings = get_appsettings(config_uri)
    engine = engine_from_config(settings, 'sqlalchemy.')

    Session = sessionmaker()
    Session.configure(bind=engine)
    session = Session()

    main(settings['local_packages'], args.older_than, session)
