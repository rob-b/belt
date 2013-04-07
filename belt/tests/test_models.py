import os


def test_seed(tmpdir):
    from ..models import seed_packages
    yolk = tmpdir.mkdir('quux').join('quux-2.0.zip')
    yolk.write('')

    pkg, = seed_packages(str(tmpdir))
    expected = os.path.join(str(tmpdir), 'quux', 'quux-2.0.zip')
    rel, = pkg.releases
    rel_file, = rel.files
    assert expected == rel_file.filename
