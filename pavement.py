from paver.easy import *
from paver import doctools
from paver.setuputils import setup

DIST = "djangofeeds"

options(
        sphinx=Bunch(builddir=".build"),
)


def sphinx_builddir(options):
    return path("docs") / options.sphinx.builddir / "html"


@task
def clean_docs(options):
    sphinx_builddir(options).rmtree()


@task
@needs("clean_docs", "paver.doctools.html")
def html(options):
    destdir = path("Documentation")
    destdir.rmtree()
    builtdocs = sphinx_builddir(options)
    builtdocs.move(destdir)


@task
@needs("clean_docs", "paver.doctools.html")
def upload_pypi_docs(options):
    builtdocs = path("docs") / options.builddir / "html"
    sh("python setup.py upload_sphinx --upload-dir='%s'" % (builtdocs))


@task
@needs("upload_pypi_docs", "ghdocs")
def upload_docs(options):
    pass


@task
def flakes(options):
    sh("find %s -name '*.py' | xargs pyflakes" % (DIST, ))


@task
def bump(options):
    sh("bump -c %s" % (DIST, ))


@task
@cmdopts([
    ("coverage", "c", "Enable coverage"),
    ("quick", "q", "Quick test"),
    ("verbose", "V", "Make more noise"),
])
def test(options):
    cmd = "python manage.py test"
    if getattr(options, "coverage", False):
        cmd += " --with-coverage3 --cover3-html"
    if getattr(options, "quick", False):
        cmd = "env QUICKTEST=1"
    if getattr(options, "verbose", False):
        cmd += " --verbosity=2"
    sh(cmd, cwd="tests")


@task
@cmdopts([
    ("noerror", "E", "Ignore errors"),
])
def pep8(options):
    noerror = getattr(options, "noerror", False)
    return sh("""find . -name "*.py" | xargs pep8 | perl -nle'\
            print; $a=1 if $_}{exit($a)'""", ignore_error=noerror)


@task
def removepyc(options):
    sh("find . -name '*.pyc' | xargs rm")


@task
@needs("removepyc")
def gitclean(options):
    sh("git clean -xdn")


@task
@needs("removepyc")
def gitcleanforce(options):
    sh("git clean -xdf")


@task
@needs("pep8", "autodoc", "verifyindex", "test", "gitclean")
def releaseok(options):
    pass


@task
@needs("releaseok", "removepyc", "upload_docs")
def release(options):
    pass
