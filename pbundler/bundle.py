from __future__ import print_function
from __future__ import absolute_import

__all__ = ['Bundle']

import os
import sys
import time
import traceback
import subprocess
import pkg_resources

from . import PBundlerException
from .util import PBFile
from .pypath import PyPath
from .cheesefile import Cheesefile, Cheese, CHEESEFILE, CHEESEFILE_LOCK
from .sources import CheeseshopSource, FilesystemSource
from .localstore import LocalStore


class Bundle:

    def __init__(self, path):
        self.path = path
        self.current_platform = 'cpython'

        self.cheesefile = Cheesefile(os.path.join(self.path, CHEESEFILE))
        self.cheesefile.parse()

        self.localstore = LocalStore()

    @classmethod
    def load(cls, path=None):
        """Preferred constructor."""

        if path is None:
            path = PBFile.find_upwards(CHEESEFILE)
            if path is None:
                message = ("Could not find %s in path from here to " +
                           "filesystem root.") % (CHEESEFILE)
                raise PBundlerException(message)

        return cls(path)

    def validate_requirements(self):
        self.calculate_requirements()
        pass

    def _add_new_dep(self, dep):
        cheese = Cheese.from_requirement(dep)
        existing = self.required.get(cheese.name)
        if existing:
            # FIXME: check if we're compatible
            return None
        self.required[cheese.name] = cheese
        return cheese

    def _resolve_deps(self):
        for pkg in self.required.values():
            if pkg.source or pkg.dist:
                # don't touch packages where we already know a source (& version)
                continue

            if pkg.path:
                source = FilesystemSource(pkg.path)
                available_versions = source.available_versions(pkg)
                if len(available_versions) == 0:
                    raise PBundlerException("Package %s is not available in %r" % (pkg.name, pkg.path))
                if len(available_versions) != 1:
                    raise PBundlerException("Package %s has multiple versions in %r" % (pgk.name, pkg.path))

                version = available_versions[0]
                pkg.use_from(version, source)

            else:
                # TODO: choose highest version from all sources

                req = pkg.requirement()
                for source in self.cheesefile.sources:
                    for version in source.available_versions(pkg):
                        if version in req:
                            pkg.use_from(version, source)
                            break

                if pkg.source is None:
                    raise PBundlerException("Package %s is not available on any sources." % (pkg.name))

        new_deps = []

        for pkg in self.required.values():
            if pkg.dist:
                # don't touch packages where we already have a (s)dist
                continue

            if pkg.path:
                # FIXME: not really the truth
                dist = pkg.source.get_distribution(pkg.source)
                print("Using %s %s from %s" % (pkg.name, pkg.exact_version, pkg.path))
            else:
                dist = self.localstore.get(pkg)
                if dist:
                    print("Using %s %s" % (pkg.name, pkg.exact_version))
                else:
                    # download and unpack
                    dist = self.localstore.prepare(pkg, pkg.source)

            pkg.use_dist(dist)

            for dep in dist.requires():
                new_deps.append(self._add_new_dep(dep))

        # super ugly:
        new_deps = list(set(new_deps))
        if None in new_deps:
            new_deps.remove(None)
        return new_deps

    def install(self, groups):
        self.required = self.cheesefile.collect(groups, self.current_platform)

        while True:
            new_deps = self._resolve_deps()
            if len(new_deps) == 0:
                # done resolving!
                break

        for pkg in self.required.values():
            if getattr(pkg.dist, 'is_sdist', False) is True:
                dist = self.localstore.install(pkg, pkg.dist)
                pkg.use_dist(dist)  # mark as installed

        self._write_cheesefile_lock()
        print("Your bundle is complete.")

    def _write_cheesefile_lock(self):
        # TODO: file format is wrong. at least we must consider groups,
        # and we shouldn't rewrite the entire file (think groups, platforms).
        with file(os.path.join(self.path, CHEESEFILE_LOCK), 'wt') as lockfile:
            for name in sorted(self.required.keys()):
                # ignore ourselves and our dependencies (which should
                # only ever be distribute).
                if name in ['pbundler', 'distribute']:
                    continue
                pkg = self.required[name]
                lockfile.write("cheese(%r, %r, path=%r)\n" % (pkg.name, pkg.exact_version, pkg.path))

    def _check_sys_modules_is_clean(self):
        # TODO: Possibly remove this when resolver/activation development is done.
        unclean = []
        for name, module in sys.modules.iteritems():
            source = getattr(module, '__file__', None)
            if source is None or name == '__main__':
                continue
            in_path = False
            for path in sys.path:
                if source.startswith(path):
                    in_path = True
                    break
            if in_path:
                continue
            unclean.append('%s from %s' % (name, source))
        if len(unclean) > 0:
            raise PBundlerException("sys.modules contains foreign modules: %s" % ','.join(unclean))

    def enable(self, groups):
        if getattr(self, 'required', None) is None:
            # while we don't have a lockfile reader:
            self.install(groups)
            #raise PBundlerException("Your bundle is not installed.")

        # reset import path
        new_path = [sys.path[0]]
        new_path.extend(PyPath.clean_path())
        PyPath.replace_sys_path(new_path)

        enabled_path = []
        for pkg in self.required.values():
            pkg.dist.activate(enabled_path)

        new_path = [sys.path[0]]
        new_path.extend(enabled_path)
        new_path.extend(PyPath.clean_path())
        PyPath.replace_sys_path(new_path)

        self._check_sys_modules_is_clean()

    def exec_enabled(self, command):
        import pkg_resources
        dist = pkg_resources.get_distribution('pbundler')
        activation_path = os.path.join(dist.location, 'pbundler', 'activation')
        os.putenv('PYTHONPATH', activation_path)
        os.putenv('PBUNDLER_CHEESEFILE', self.cheesefile.path)
        os.execvp(command[0], command)
