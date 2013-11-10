import pytest
from sqlalchemy.orm import exc


# def test_searches_for_correct_name(dummy_request, db_session):
#     from belt.views import package_version
#     dummy_request.matchdict = {'version': u'2.7.1', 'package': u'Jinja2'}

#     with pytest.raises(exc.NoResultFound):
#         package_version(dummy_request)
