"""Implements core classes and functions."""

import os
import json
import datetime
import six
from six.moves import configparser
import pystache

class Pack(object):
    """A package template class.

    Attributes:
        meta: dict. Defaults.
        ...
    """
    def __init__(self, hanger, name):
        """Init pack.

        Args:
            hanger: str. Path to hanger directory.
            name: str. Name of package template.
        """
        self.meta = {'cfg': 'pack.cfg',
                     'json': 'pack.json'}
        self.hanger = hanger
        self.name = name
        self.cfg = configparser.RawConfigParser()
        self.hierarchy = []
        self.partials = Partials(self.hanger)
        self.context = {}
        self.templates = []
        self.manifest = {}

        self._validate_args()
        self.find_hierarchy()
        self.read_cfg(self.find_meta('cfg'))
        self.update_context(self.builtin_context())
        self.read_context(self.find_meta('json'))
        exclude = [self.meta['cfg'], self.meta['json']]
        self.templates = self.find_templates(exclude)

    def _check_str(self, s):
        """Force str to iterable."""
        if isinstance(s, six.string_types):
            return [s]
        else:
            return s

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

    def _validate_args(self):
        # check directories exist.
        path = os.path.join(self.hanger, self.name)
        if not os.path.exists(path):
            raise IOError('No such pack: {}'.format(path))

    def _add_base(self, hanger, name, meta):
        cfg = configparser.RawConfigParser()
        cfg.read(os.path.join(hanger, name, meta))
        try:
            bases = self._split_cfg(cfg.get('class', 'base'))
            for base in bases:  # add bases for this name first
                if base == self.hierarchy[-1]:
                    if base == name:
                        raise RuntimeError("'{}' inherits itself.".format(base))
                elif base in self.hierarchy:
                    raise RuntimeError("'{}' creates a circular inheritance " \
                                       "by inheriting '{}'.".format(name, base))
                else:
                    self.hierarchy.append(base)
            for base in bases:  # add parents of the bases
                self._add_base(hanger, base, meta)
        except (configparser.NoSectionError, configparser.NoOptionError):
            pass

    def find_hierarchy(self):
        """Resolution order."""
        self.hierarchy = []
        self.hierarchy.append(self.name)
        self._add_base(self.hanger, self.name, self.meta['cfg'])

    def find_meta(self, meta):
        paths = []
        for pack in reversed(self.hierarchy + ['']):
            path = os.path.join(self.hanger, pack, self.meta[meta])
            if os.path.exists(path):
                paths.append(path)
        return paths

    def read_cfg(self, path):
        paths = self._check_str(path)
        self.cfg.read(paths)

    def get_cfg(self, section, option, default=None):
        try:
            return self.cfg.get(section, option)
        except (configparser.NoSectionError, configparser.NoOptionError):
            return default

    def builtin_context(self):
        context = {}
        # datetime
        # https://docs.python.org/2/library/time.html#time.strftime
        today = datetime.datetime.today()
        forms = dict(today = '%c',
                     year = '%Y', month = '%m', day = '%d',
                     hour = '%H', minute = '%M', second = '%S')
        for tag, val in six.iteritems(forms):
            context[tag] = today.strftime(self.get_cfg('datetime', tag, val))

        return context

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
        """Find template(s).

        Args:
            exclude: iterable of str. Filenames to exclude.
        """
        exclude = self._check_str(exclude)
        paths = []
        for pack in reversed(self.hierarchy):
            path = os.path.join(self.hanger, pack)
            paths += self._get_files(path)
        return [p for p in paths if self._valid_path(os.path.join(*p), exclude)]

    def build(self, name, description, dest='.'):
        """Build package from template.

        Args:
            dest: str. Destination directory.
        """
        self.update_context(dict(name=name, description=description))
        renderer = pystache.Renderer(partials=self.partials)

        # build manifest
        manifest = {}
        for root, rel in self.templates:
            manifest[os.path.join(root, rel)] = os.path.join(dest, rel)

        # render paths
        for src, dest in six.iteritems(manifest):
            self.manifest[src] = renderer.render(dest, self.context)

        # render and write templates
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

class Partials(object):
    def __init__(self, hanger):
        self.hanger = hanger
    def get(self, path):
        try:
            with open(os.path.join(self.hanger, path)) as f:
                return f.read()
        except IOError:
            return None

def launch(hanger, pack, name, description, dest='.'):
    pack = Pack(hanger, pack)
    pack.update_context(dict(name=name, description=description))
    pack.build(name, description, dest)
