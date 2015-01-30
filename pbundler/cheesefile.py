from __future__ import print_function
from __future__ import absolute_import

__all__ = ['Cheesefile', 'Cheese', 'CHEESEFILE', 'CHEESEFILE_LOCK']

import os
from contextlib import contextmanager
import pkg_resources

from pip.req import parse_requirements

from . import PBundlerException
from .dsl import DslRunner
from .sources import CheeseshopSource


CHEESEFILE = 'Cheesefile'
CHEESEFILE_LOCK = 'Cheesefile.lock'


class Cheese(object):
    """A package. A distribution. A requirement. A cheese.
    Whatever you want to call it.
    """

    def __init__(self, name, version_req, platform=None, path=None, source=None):
        self.name = name
        self.version_req = version_req
        self.platform = platform
        self.path = path
        self.source = source
        self.dist = None
        self._requirements = None
        self.key = self.name.lower()

    @classmethod
    def from_requirement(cls, req):
        version = ','.join([op + ver for (op, ver) in req.specs])
        if version == '':
            version = None
        return cls(req.project_name, version, None, None)

    def applies_to(self, platform):
        if self.platform is None:
            return True
        return (self.platform == platform)

    def is_exact_version(self):
        return self.version_req.startswith('==')

    @property
    def exact_version(self):
        """Returns the version number, without an operator. If the operator
        was not '==', an Exception is raised."""

        if not self.is_exact_version():
            raise Exception("Cheese %s didn't have an exact version (%s)" %
                            (self.name, self.version_req))

        return self.version_req[2:]

    def use_from(self, version, source):
        self.version_req = '==' + version
        self.source = source

    def use_dist(self, dist):
        self.dist = dist

    def requirement(self):
        """Return pkg_resources.Requirement matching this object."""

        version = self.version_req
        if version is None:
            version = ''
        else:
            if not ('>' in version or '<' in version or '=' in version):
                version = '==' + version
        return pkg_resources.Requirement.parse(self.name + version)

    @property
    def requirements(self):
        assert(self.dist is not None)
        if self._requirements is None:
            self._requirements = [Cheese.from_requirement(dep) for dep in self.dist.requires()]
        return self._requirements


class CheesefileContext(object):
    """DSL Context class. All methods not starting with an underscore
    are exposed to the Cheesefile."""

    def __init__(self, path):
        self.path = path
        self.sources = []
        self.groups = {}

        with self.group('default'):
            pass

    def __str__(self):
        s = []

        for source in self.sources:
            s.append('source(%r)' % source)
        s.append('')

        for name, group in self.groups.items():
            indent = '  '
            if name == 'default':
                indent = ''
            else:
                s.append('with group(%r):' % name)
            for egg in group:
                s.append(indent + ('%r' % (egg,)))
            s.append('')

        return "\n".join(s)

    def source(self, name_or_url):
        if name_or_url == 'pypi':
            name_or_url = 'http://pypi.python.org/pypi'

        self.sources.append(CheeseshopSource(name_or_url))

    @contextmanager
    def group(self, name):
        self.current_group = name
        self.groups[name] = self.groups.get(name, [])
        yield
        self.current_group = 'default'

    def req(self, name, version=None, platform=None, path=None):
        self.groups[self.current_group].append(
            Cheese(name, version, platform, path)
            )

    def pipspec(self, path_to_requirements_txt=None):
        if path_to_requirements_txt is None:
            non_default_path = 'requirements.txt'
        else:
            non_default_path = path_to_requirements_txt
        abs_path = os.path.join(os.path.dirname(self.path), non_default_path)
        for requirement in parse_requirements(abs_path):
            self.groups[self.current_group].append(Cheese.from_requirement(requirement.req))


class Cheesefile(object):
    """Parses and holds Cheesefiles."""

    def __init__(self, path):
        self.path = path

    @classmethod
    def generate_empty_file(cls, path):
        filepath = os.path.join(path, CHEESEFILE)
        if os.path.exists(filepath):
            raise PBundlerException("Cowardly refusing, as %s already exists here." %
                                    (CHEESEFILE,))
        print("Writing new %s to %s" % (CHEESEFILE, filepath))
        with open(filepath, "w") as f:
            f.write("""# PBundler Cheesefile
source('pypi')

# req('Flask')

# import an existing requirements.txt in the same directory as this Cheesefile
# pipspec()

# import any requirements.txt file
# pipspec(<path relative to the directory of this Cheesefile>)
""")

    def parse(self):
        runner = DslRunner(lambda: CheesefileContext(self.path))
        ctx = runner.execfile(self.path)
        for attr, val in ctx.__dict__.items():
            self.__setattr__(attr, val)

    def collect(self, groups, platform):
        collection = {}
        groups = [group for name, group in self.groups.iteritems() if name in groups]
        for pkgs in groups:
            for pkg in pkgs:
                if pkg.applies_to(platform):
                    collection[pkg.key] = pkg
        return collection


class CheesefileLockContext(object):
    """DSL Context class. All methods not starting with an underscore
    are exposed to the Cheesefile.lock."""

    def __init__(self):
        self.cheesefile_data = []
        self.from_source_data = {}

    @contextmanager
    def from_source(self, url):
        self.from_source_data[url] = []
        self.current_req_context = self.from_source_data[url]
        yield
        self.current_req_context = None

    @contextmanager
    def Cheesefile(self):
        self.current_req_context = self.cheesefile_data
        yield
        self.current_req_context = None

    def req(self, name, version, platform=None, path=None):
        req = Cheese(name, version, platform, path)
        self.current_req_context.append(req)

    @contextmanager
    def resolved_req(self, name, version):
        prev_req_context = self.current_req_context
        solved_req = Cheese(name, version)
        self.current_req_context = solved_req.requirements
        yield
        self.current_req_context = prev_req_context
        self.current_req_context.append(solved_req)


class CheesefileLock(object):
    """Parses and holds Cheesefile.locks."""

    def __init__(self, path):
        self.path = path

    def parse(self):
        runner = DslRunner(CheesefileLockContext)
        ctx = runner.execfile(self.path)
        for attr, val in ctx.__dict__.items():
            self.__setattr__(attr, val)
