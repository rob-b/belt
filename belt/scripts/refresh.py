import sys
import datetime
import logging
from belt.refresh import refresh_packages
import transaction


log = logging.getLogger(__name__)


from belt.models import DBSession
from sqlalchemy import engine_from_config
from pyramid.paster import (
    get_appsettings,
    setup_logging,
)


def main(location):

    with transaction.manager:
        for package in refresh_packages(datetime.datetime(2013, 5, 5)):
            log.info(u'Updated ' + unicode(package))
            DBSession.add(package)

if __name__ == "__main__":
    config_uri = sys.argv[1]
    setup_logging(config_uri)
    settings = get_appsettings(config_uri)
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    main(settings['local_packages'])
