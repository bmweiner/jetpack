"""Implements core classes and functions."""

import os
import ConfigParser
import json
import six
import pystache

class Pack(object):
    """A package template class.

    Attributes:
        meta: dict. Defaults.
        ...
    """
    def __init__(self, hanger, name, license=None):
        """Init pack.

        Args:
            hanger: str. Path to hanger directory.
            name: str. Name of package template.
            license: str. Path to license directory. If None, will search hanger
                for a directory named `license`.
        """
        self.meta = {'cfg': 'pack.cfg',
                     'json': 'pack.json',
                     'license': 'license'}
        self.hanger = hanger
        self.name = name
        self.cfg = ConfigParser.ConfigParser()
        self.context = {}
        self.templates = []
        self.license = None
        self.manifest = {}

        self._validate_args()
        self.read_cfg(os.path.join(self.hanger, self.name))  # init config
        self.path = self.find_path(license)
        self.read_cfg(self.find_meta('cfg'))
        self.read_context(self.find_meta('json'))
        exclude = [self.meta['cfg'], self.meta['json']]
        self.templates = self.find_templates(exclude)
        self.find_license()

    def _validate_args(self):
        path = os.path.join(self.hanger, self.name)
        if not os.path.exists(path):
            raise IOError('No such pack: {}'.format(path))

    def _check_str(self, path):
        """Force str to iterable."""
        if isinstance(path, basestring):
            return [path]
        else:
            return path

    def _split_cfg(self, val):
        return [v.strip() for v in val.split(',')]

    def _get_files(self, root):
        """Recursively find all files at path."""
        paths = []
        for path, dirs, files in os.walk(root):
            for f in files:
                rel = os.path.relpath(os.path.join(path, f), root)
                paths.append((root, rel))
        return paths

    def _valid_path(self, path, exclude):
        for excl in exclude:
            if path.endswith(excl):
                return False
        return True

    def read_cfg(self, path):
        paths = self._check_str(path)
        self.cfg.read(paths)

    def get_cfg(self, section, option, cfg=None):
        if not cfg:
            cfg = self.cfg
        try:
            return cfg.get(section, option)
        except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
            return None

    def find_path(self, license=None):
        """Find paths for pack, base(s), and license.

        Args:
            license: str. Path to license directory. If None, will search hanger
                for a directory named `license`.

        Returns:
            dict: Paths to pack, base(s) and license if exist.
        """
        path = {}
        path['pack'] = os.path.join(self.hanger, self.name)
        if license:
            path['license'] = license
        else:
            path['license'] = os.path.join(self.hanger, self.meta['license'])
        path['base'] = []
        bases = self.get_cfg('class', 'base')
        if bases:
            for base in self._split_cfg(bases):
                path['base'].append(os.path.join(self.hanger, base))
        return path

    def find_meta(self, meta):
        paths = [os.path.join(self.hanger, self.meta[meta])]
        for path in self.path['base'] + [self.path['pack']]:
            paths.append(os.path.join(path, self.meta[meta]))

        return [p for p in paths if os.path.exists(p)]

    def read_context(self, path):
        """Read context file(s).

        Args:
            path: str or iterable. Path to context file. Multiple paths
                will be unioned to a single context. When a tag is
                encountered more than once, the value in the last path
                is used.
        """
        paths = self._check_str(path)
        context = {}
        for path in paths:
            with open(path) as f:
                context.update(json.loads(f.read()))
        self.context.update(context)

    def update_context(self, context):
        """Update context.

        Args:
            context: dict. Mustache tag/value pairs.
        """
        self.context.update(context)

    def find_templates(self, exclude=[]):
        """Find template(s) at self.path.

        Args:
            exclude: iterable of str. Filenames to exclude.
        """
        exclude = self._check_str(exclude)
        class_exclude = self.get_cfg('class', 'exclude')
        if class_exclude:
            exclude += self._split_cfg(class_exclude)
        paths = []
        for path in self.path['base'] + [self.path['pack']]:
            paths += self._get_files(path)
        return [p for p in paths if self._valid_path(os.path.join(*p), exclude)]

    def find_license(self, name=None):
        name = name or self.get_cfg('license', 'name')
        if name:
            licenses = os.listdir(self.path['license'])
            name = [l for l in licenses if name in l][0]
            self.license = (self.path['license'], name)

    def build(self, dest, exclude=[]):
        """Build package from template.

        Args:
            dest: str. Destination directory.
        """
        exclude = self._check_str(exclude)
        renderer = pystache.Renderer()

        # build manifest
        manifest = {}
        for src, rel in self.templates:
            manifest[os.path.join(src, rel)] = os.path.join(dest, rel)
        if self.license:
            license_src = os.path.join(*self.license)
            shim = self.get_cfg('license', 'dest') or ''
            license_dest = os.path.join(dest, shim, 'LICENSE')
            manifest[license_src] = license_dest

        # render paths and remove excludes
        for src, dest in six.iteritems(manifest):
            if self._valid_path(src, exclude):
                self.manifest[src] = renderer.render(dest, self.context)

        # render templates and create package
        for src, dest in six.iteritems(self.manifest):
            # create dest dir if needed
            if not os.path.exists(os.path.dirname(dest)):
                try:
                    os.makedirs(os.path.dirname(dest))
                except OSError as exc: # race condition
                    if exc.errno != errno.EEXIST:
                        raise
            with open(dest, 'w') as f:
                f.write(renderer.render_path(src, self.context))

def launch(hanger, pack, name, description, destination, license=None):
    pack = Pack(hanger, pack, license)
    context = dict(name=name,
                   description=description)
    pack.update_context(context)
    pack.build(destination)
