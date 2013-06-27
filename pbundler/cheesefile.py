from __future__ import print_function
from __future__ import absolute_import

__all__ = ['Cheesefile', 'Cheese', 'CHEESEFILE', 'CHEESEFILE_LOCK']

import os
import shlex
from contextlib import contextmanager
import pkg_resources

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
        self.orig_version_req = None
        self.platform = platform
        self.path = path
        self.source = source
        self.dist = None
        self._requirements = None

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
        if self.version_req is None: return False
        return self.version_req.startswith('==')

    @property
    def version_req(self):
        return self._version_req

    @version_req.setter
    def version_req(self, value):
        """Version setter that ensures that exact versions end up as
        ==version.number."""

        if value is None:
            self._version_req = value
        else:
            op_chars = ['>', '<', '=', '(']
            for char in op_chars:
                if char in value:
                    self._version_req = value
                    return
            self._version_req = '==' + value

    @property
    def exact_version(self):
        """Returns the version number, without an operator. If the operator
        was not '==', an Exception is raised."""

        if not self.is_exact_version():
            raise Exception("Cheese %s didn't have an exact version (%s)" %
                            (self.name, self.version_req))

        return self.version_req[2:]

    def use_from(self, version, source):
        self.orig_version_req = self.version_req
        self.version_req = '==' + version
        self.source = source

    def use_dist(self, dist):
        self.dist = dist
        #print(self.dist)
        #self.name = dist.safe_name()

    def requirement(self):
        """Return pkg_resources.Requirement matching this object."""

        version = self.version_req
        if version is None:
            version = ''
        else:
            if not ('>' in version or '<' in version or '=' in version
                    or '(' in version):
                version = '==' + version
        return pkg_resources.Requirement.parse(self.name + version)

    @property
    def requirements(self):
        assert(self.dist is not None)
        if self._requirements is None:
            self._requirements = [Cheese.from_requirement(dep) for dep in self.dist.requires()]
        return self._requirements

    def requirements_setter(self):
        """Used to set requirements from a Cheesefile.lock."""
        self._requirements = []
        return self._requirements

    @property
    def key(self):
        """Used as the lookup key in require (and other Cheese collections)."""
        return self.name.upper()


class CheesefileContext(object):
    """DSL Context class. All methods not starting with an underscore
    are exposed to the Cheesefile."""

    def __init__(self):
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
            name_or_url = 'https://pypi.python.org/pypi'

        self.sources.append(CheeseshopSource(name_or_url))

    @contextmanager
    def group(self, name):
        self.current_group = name
        self.groups[name] = self.groups.get(name, [])
        yield
        self.current_group = 'default'

    def pkg(self, name, version=None, platform=None, path=None):
        self.groups[self.current_group].append(
            Cheese(name, version, platform, path)
            )


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
            f.write("# PBundler Cheesefile\n")
            f.write("\n")
            f.write("source(\"pypi\")\n")
            f.write("\n")
            f.write("# pkg(\"Flask\")\n")
            f.write("\n")

    def parse(self):
        runner = DslRunner(CheesefileContext)
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

    def pkg(self, name, version, platform=None, path=None):
        req = Cheese(name, version, platform, path)
        self.current_req_context.append(req)

    @contextmanager
    def resolved_pkg(self, name, version):
        prev_req_context = self.current_req_context
        solved_req = Cheese(name, version)
        self.current_req_context = solved_req.requirements_setter()
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

        # rebuild pkg.source attributes
        for source_url, pkgs in self.from_source_data.iteritems():
            source = CheeseshopSource(source_url)
            for pkg in pkgs:
                pkg.use_from(pkg.exact_version, source)

    def matches_cheesefile(self, cheesefile):
        flat_reqs = [item for pkgs in cheesefile.groups.values() for item in pkgs]
        if sorted([pkg.name for pkg in flat_reqs]) != sorted([pkg.name for pkg in self.cheesefile_data]):
            # pkg names mismatch
            return False
        for their_pkg in flat_reqs:
            our_pkg = [pkg for pkg in self.cheesefile_data if pkg.name == their_pkg.name][0]
            if their_pkg.version_req != our_pkg.version_req:
                return False
        return True

    def to_required(self):
        pkgs = [item for pkgs in self.from_source_data.itervalues() for item in pkgs]
        return dict(zip([pkg.key for pkg in pkgs], pkgs))
