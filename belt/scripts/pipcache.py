import os
import re
import glob
import shutil
import urlparse
from belt.axle import split_package_name, mkdir_p


def _pipcache():
    import argparse
    desc = 'Copy PIP_DOWNLOAD_CACHE to pypi dir'
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('--pip-download-cache',
                        help='Directory packages can be found in',
                        required=True)
    parser.add_argument('--pypi-dir',
                        help='Directory to copy packages to',
                        required=True)
    args = parser.parse_args()
    pipcache(args.pip_download_cache, args.pypi_dir)


def pipcache(pip_download_cache, pypi_dir):
    pip_download_cache = pip_download_cache.rstrip('/')
    md5_re = re.compile(r'\?md5=\w*$')
    for fn in glob.iglob(pip_download_cache + '/*'):
        real_name = os.path.basename(urlparse.unquote(fn))
        if not real_name or real_name.endswith('.content-type'):
            continue

        package_name, _ = split_package_name(real_name)
        dest = os.path.join(pypi_dir, package_name, real_name)

        dest = md5_re.sub('', dest)
        mkdir_p(os.path.dirname(dest))
        shutil.copyfile(fn, dest)


if __name__ == "__main__":
    _pipcache()
