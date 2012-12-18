#!/usr/bin/env python
from __future__ import print_function

import os
import sys
import time
import traceback
import subprocess

import pip.req
from pip.exceptions import InstallationError

_using_venv = False
try:
    # bundled with Python 3.3+
    import venv
    _using_venv = True
    import urllib.request
except:
    import virtualenv

# initialize vcs support for pip <= 1.1
if 'version_control' in pip.__dict__:
    pip.version_control()


class PBFile:
    @staticmethod
    def read(path, filename):
        try:
            with open(os.path.join(path, filename), 'r') as f:
                return f.read()
        except Exception as e:
            return None

    @staticmethod
    def find_upwards(fn, root=os.path.realpath(os.curdir)):
        if os.path.exists(os.path.join(root, fn)):
            return root
        up = os.path.abspath(os.path.join(root, '..'))
        if up == root:
            return None
        return PBFile.find_upwards(fn, up)


REQUIREMENTS = 'requirements.txt'
REQUIREMENTS_LAST = 'requirements.last'


class PBBasepathNotFound(Exception):
    pass


class FakeOptionsClass(object):
    def __hasattr__(self, name):
        return True

    def __getattr__(self, name):
        return None


class PBundle:
    def __init__(self, basepath):
        self.basepath = basepath
        self.workpath = os.path.join(self.basepath, ".pbundle")
        self.virtualenvpath = os.path.join(self.workpath, "virtualenv")
        self.ensure_paths()
        self.ensure_virtualenv()
        self._requirements = None
        self._requirements_last = None

    @staticmethod
    def find_basepath():
        return PBFile.find_upwards(REQUIREMENTS)

    def ensure_paths(self):
        if not os.path.exists(self.workpath):
            os.mkdir(self.workpath)

    def ensure_virtualenv(self):
        if not os.path.exists(os.path.join(self.virtualenvpath, 'bin')):
            if _using_venv:
                venv.create(self.virtualenvpath)
                self._install_prereqs()
            else:
                os.system("virtualenv " + self.virtualenvpath + " 2>&1")

    def _install_prereqs(self):
        # assumes _using_venv = True, python3.3+, as virtualenv would do
        # something similar itself.
        distribute_setup_py = os.environ.get('DISTRIBUTE_SETUP', None)
        if distribute_setup_py is not None:
            if not (os.path.isfile(distribute_setup_py) and
                    os.access(distribute_setup_py, os.X_OK)):
                raise PBCliError("Program specified in DISTRIBUTE_SETUP is not (an) executable.")
        else:
            distribute_setup_url = 'http://python-distribute.org/distribute_setup.py'
            distribute_setup_py = os.path.join(self.workpath, "distribute_setup.py")
            print("Downloading", distribute_setup_url)
            with urllib.request.urlopen(distribute_setup_url) as setup_sock:
                with open(distribute_setup_py, 'wb') as f:
                    buf = setup_sock.read()
                    f.write(buf)

            os.chmod(distribute_setup_py, 0o755)

        self._call_program(["python", distribute_setup_py], cwd=self.workpath)
        self._call_program(["easy_install", "pip"], cwd=self.workpath)

    def ensure_relocatable(self):
        self.make_scripts_relocatable()
        if not _using_venv:
            virtualenv.fixup_pth_and_egg_link(self.virtualenvpath)

    def make_scripts_relocatable(self):
        shebang_pfx = '#!'
        new_shebang = '#!/usr/bin/env pbundle-py'
        if sys.platform == 'win32':
            bin_suffix = 'Scripts'
        else:
            bin_suffix = 'bin'
        bin_dir = os.path.join(self.virtualenvpath, bin_suffix)
        for filename in os.listdir(bin_dir):
            filename = os.path.join(bin_dir, filename)
            if not os.path.isfile(filename):
                # ignore subdirs, e.g. .svn ones.
                continue
            if os.path.islink(filename):
                # venv will symlink python, don't even try to patch these.
                continue
            lines = None
            with open(filename, 'r') as f:
                try:
                    lines = f.readlines()
                except UnicodeDecodeError:
                    # Probably a binary.
                    continue
            if not lines:
                # Empty.
                continue

            line0 = lines[0].strip()
            if not line0.startswith(shebang_pfx):
                # Probably a binary.
                continue
            if not "python" in line0 and not "pbundle" in line0:
                # Has shebang prefix, but not a python script.
                # Better ignore it.
                continue
            if line0 == new_shebang:
                # Already patched, skip rewrite.
                continue
            lines = [new_shebang+'\n'] + lines[1:]
            f = open(filename, 'w')
            f.writelines(lines)
            f.close()

    def _parse_requirements(self, filename):
        reqs = {}
        try:
            try:
                for req in pip.req.parse_requirements(
                        os.path.join(self.basepath, filename),
                        options=FakeOptionsClass()):
                    reqs[req.name] = req
            except InstallationError as e:
                pass
        except Exception as e:
            import traceback
            traceback.print_exc(e)
        return reqs

    @property
    def requirements(self):
        if not self._requirements:
            self._requirements = \
                self._parse_requirements(REQUIREMENTS)
        return self._requirements

    @property
    def requirements_last(self):
        if not self._requirements_last:
            self._requirements_last = \
                self._parse_requirements(REQUIREMENTS_LAST)
        return self._requirements_last

    def requirements_changed(self):
        return self.requirements_last != self.requirements

    def save_requirements(self):
        with open(os.path.join(self.workpath, REQUIREMENTS_LAST), "w") as f:
            f.write("#pbundle %s, written %s\n" %
                    (REQUIREMENTS_LAST, time.time()))
            for r in self.requirements.values():
                f.write("%s\n" % r)

    def run(self, command, verbose=True):
        try:
            return self._call_program(command, verbose=verbose, honor_envfile=True, raise_on_error=False)
        except OSError as e:
            print(e)
            return 127

    def envfile(self):
        ef = {}
        filename = os.path.join(self.workpath, "environment.py")
        try:
            if sys.version_info >= (3,):
                with open(filename, 'r') as f:
                    exec(compile(f.read(), filename, 'exec'), {}, ef)
            else:
                execfile(filename, {}, ef)
        except IOError as e:
            # ignore non-existence of environment.py
            pass
        except Exception as e:
            print('environment.py: %s' % e)
        return ef

    def _call_program(self, command, verbose=True, raise_on_error=True, cwd=None, honor_envfile=False):
        if verbose:
            print("Running \"%s\" ..." % (' '.join(command),))

        env = os.environ.copy()
        if 'PYTHONHOME' in env:
            del env['PYTHONHOME']
        env['VIRTUAL_ENV'] = self.virtualenvpath
        env['PATH'] = (
            os.path.join(self.virtualenvpath, "local/bin") + ':' +
            os.path.join(self.virtualenvpath, "bin") + ':' +
            env['PATH']
            )
        for key, value in self.envfile().items():
            env[key] = value

        rc = subprocess.Popen(
            command,
            env=env,
            close_fds=True,
            shell=False,
            cwd=cwd
            ).wait()

        if rc != 0 and raise_on_error:
            raise PBCliError("External command %r failed with exit code %d" % (' '.join(command), rc))
        return rc

    def uninstall_removed(self):
        to_remove = set(self.requirements_last.keys()) - \
            set(self.requirements.keys())

        for p in to_remove:
            self._call_program(["pip", "uninstall", p], raise_on_error=False)

    def install(self):
        self._call_program(["pip", "install", "-r",
                            os.path.join(self.basepath, REQUIREMENTS)])
        self.ensure_relocatable()

    def upgrade(self):
        self._call_program(["pip", "install", "--upgrade", "-r",
                            os.path.join(self.basepath, REQUIREMENTS)])
        self.ensure_relocatable()


class PBCliError(Exception):
    def __init__(self, message):
        Exception.__init__(self, message)


USAGE = """
pbundle                  Copyright 2012 Christian Hofstaedtler
pbundle Usage:
  pbundle [install]    - Run pip, if needed (also uninstalls removed
                         requirements)
  pbundle upgrade      - Run pip, with --upgrade
  pbundle init         - Create empty requirements.txt
  pbundle run program  - Run "program" in activated virtualenv
  pbundle py args      - Run activated python with args

To auto-enable your scripts, use "#!/usr/bin/env pbundle-py" as the
shebang line.

Website:      https://github.com/zeha/pbundler
Report bugs:  https://github.com/zeha/pbundler/issues
"""


class PBCli():
    def __init__(self):
        self._pb = None

    @property
    def pb(self):
        if not self._pb:
            basepath = PBundle.find_basepath()
            if not basepath:
                message = ("Could not find requirements.txt " +
                           "in path from here to root.")
                raise PBCliError(message)
            self._pb = PBundle(basepath)
        return self._pb

    def handle_args(self, argv):
        args = argv[1:]
        command = "install"
        if args:
            command = args.pop(0)
        if command in ['--help', '-h']:
            command = 'help'
        if 'cmd_' + command in PBCli.__dict__:
            return PBCli.__dict__['cmd_' + command](self, args)
        else:
            raise PBCliError("Unknown command \"%s\"" % (command,))

    def run(self, argv):
        try:
            return self.handle_args(argv)
        except PBCliError as e:
            print("E:", str(e))
            return 1
        except Exception as e:
            print("E: Internal error in pbundler:")
            print("  ", e)
            traceback.print_exc()
            return 120

    def cmd_help(self, args):
        print(USAGE.strip())

    def cmd_init(self, args):
        # can't use PBundle here
        if os.path.exists(REQUIREMENTS):
            raise PBCliError("Cowardly refusing, as %s already exists here." %
                             (REQUIREMENTS,))
        with open(REQUIREMENTS, "w") as f:
            f.write("# pbundle MAGIC\n")
            f.write("#pbundle>=0\n")
            f.write("\n")

    def cmd_install(self, args):
        if self.pb.requirements_changed():
            self.pb.uninstall_removed()
            self.pb.install()
            self.pb.save_requirements()

    def cmd_upgrade(self, args):
        self.pb.uninstall_removed()
        self.pb.upgrade()

    def cmd_run(self, args):
        return self.pb.run(args, verbose=False)

    def cmd_py(self, args):
        return self.pb.run(["python"] + args, verbose=False)
