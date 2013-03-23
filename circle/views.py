from pyramid.i18n import TranslationStringFactory

_ = TranslationStringFactory('circle')


def my_view(request):
    return {'project': 'circle'}
