from fudge import Fake
from fudge.inspector import arg
from sqlalchemy.orm import exc
from belt.tests import patch
pypi_base_url = 'https://pypi.python.org/packages'


class TestPackageList(object):

    def test_requests_package_data_from_pypi(self, dummy_request):
        from belt.views import package_list
        dummy_request.matchdict = {'package': u'foo'}

        pkg = Fake('Package').has_attr(name='foo', releases=[1])

        with patch('belt.views.Package') as Package:
            Package.expects('by_name').with_args('foo').raises(exc.NoResultFound)
            (Package.expects('create_from_pypi')
             .with_args(name='foo', package_dir=arg.any())
             .returns(pkg))
            package_list(dummy_request)

    @patch('belt.views.DBSession')
    @patch('belt.views.Package')
    @patch('belt.views.package_releases')
    def test_requests_package_releases_if_none_exist(self, DBSession, Package,
                                                     package_releases,
                                                     dummy_request):
        from belt.views import package_list

        rel = Fake('Release').has_attr(version='106')
        package_releases.expects_call().with_args('quux', location=arg.any()).returns([rel])

        pkg = (Fake('pkg').has_attr(name='quux', releases=set()))
        Package.expects('by_name').with_args('quux').returns(pkg)
        DBSession.expects('add').with_args(pkg)

        dummy_request.matchdict = {'package': u'quux'}
        package_list(dummy_request)
