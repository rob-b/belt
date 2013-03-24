import fudge
from pyramid import testing


class TestViewIntegration(object):

    def teardown_method(self, method):
        testing.tearDown()

    @fudge.patch('belt.views.pip_cached_packages')
    @fudge.patch('belt.views.FileResponse')
    def test_can_download_package(self, pip_cached_packages, FileResponse):
        from belt.views import download
        pip_cached_packages.expects_call().returns([
            ('/path/to/foozle', 'foozle'),
        ])

        FileResponse.expects('__init__').with_args('/path/to/foozle')
        request = testing.DummyRequest(matchdict={'package': 'foozle'})
        request.context = testing.DummyResource()
        download(request)

    def test_package_list(self):
        pass
