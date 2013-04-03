from belt.axle import build_wheels, copy_wheels_to_pypi


def _build_wheels():
    import argparse
    parser = argparse.ArgumentParser(description='Build wheels from packages')
    parser.add_argument('--wheel-dir', help='Directory to store wheels in',
                        required=True)
    parser.add_argument('--pypi-dir',
                        help='Directory packages can be found in',
                        required=True)
    args = parser.parse_args()
    build_wheels(args.pypi_dir, args.wheel_dir)
    copy_wheels_to_pypi(args.wheel_dir, args.pypi_dir)


if __name__ == "__main__":
    _build_wheels()
