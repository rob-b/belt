Simple PyPI Proxy
=================

Belt is a simple PyPI proxy. Any packages that exist locally will be
installed direct from disk; non-existent packages will be installed from PyPI
and stored locally for future use.

The latest version is always available at `github.com/rob-b/belt
<https://github.com/rob-b/belt>`_

To install::

    easy_install belt

or::

    pip install belt


Development uses git-flow naming conventions. Also be sure to run::

    ln -fs "$(pwd)/pre-push.sh" .git/hooks/pre-push

to install the git pre-push hook that refuses to push to develop
or master when all tests do not pass.


Create a config file setting `local_packages` to wherever you want to store
your locally cached packages::

    cat << EOF > production.ini

    [app:main]
    use = egg:belt

    pyramid.reload_templates = false
    pyramid.debug_authorization = false
    pyramid.debug_notfound = false
    pyramid.debug_routematch = false
    pyramid.default_locale_name = en
    pyramid.includes =

    jinja2.directories = belt:templates
    jinja2.filters =
        route_url = pyramid_jinja2.filters:route_url_filter

    local_packages = /vagrant/pypi

    [server:main]
    use = egg:waitress#main
    host = 0.0.0.0
    port = 6543

    [loggers]
    keys = root, belt

    [handlers]
    keys = console

    [formatters]
    keys = generic

    [logger_root]
    level = WARN
    handlers = console

    [logger_belt]
    level = WARN
    handlers =
    qualname = belt

    [handler_console]
    class = StreamHandler
    args = (sys.stderr,)
    level = NOTSET
    formatter = generic

    [formatter_generic]
    format = %(asctime)s %(levelname)-5.5s [%(name)s][%(threadName)s] %(message)s
    EOF

Then run with `pserve`::

    pserve production.ini

You can now install packages via your local proxy::

    pip install -i http://localhost:6543/simple/ zest.releaser
