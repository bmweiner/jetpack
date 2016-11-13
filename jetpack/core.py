"""Implements core classes and functions."""

import os
import ConfigParser
import json
import datetime
import six
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
        self.cfg = ConfigParser.ConfigParser()
        self.context = {}
        self.templates = []
        self.manifest = {}

        self._validate_args()
        self.partials = Partials(self.hanger)
        self.read_cfg(os.path.join(self.hanger, self.name))  # init config
        self.path = self.find_path()
        self.read_cfg(self.find_meta('cfg'))
        self.update_context(self.builtin_context())
        self.read_context(self.find_meta('json'))
        exclude = [self.meta['cfg'], self.meta['json']]
        self.templates = self.find_templates(exclude)

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

    def get_cfg(self, section, option, default=None):
        try:
            return self.cfg.get(section, option)
        except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
            return default

    def find_path(self):
        """Find paths for pack and base(s).

        Returns:
            dict: Paths to pack and base(s) if exist.
        """
        path = {}
        path['pack'] = os.path.join(self.hanger, self.name)
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

    def build(self, dest, exclude=[]):
        """Build package from template.

        Args:
            dest: str. Destination directory.
        """
        exclude = self._check_str(exclude)
        renderer = pystache.Renderer(partials=self.partials)

        # build manifest
        manifest = {}
        for src, rel in self.templates:
            manifest[os.path.join(src, rel)] = os.path.join(dest, rel)

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

class Partials(object):
    def __init__(self, hanger):
        self.hanger = hanger
    def get(self, path):
        try:
            with open(os.path.join(self.hanger, path)) as f:
                return f.read()
        except IOError:
            return None

def launch(hanger, pack, name, description, destination):
    pack = Pack(hanger, pack)
    context = dict(name=name, description=description)
    pack.update_context(context)
    pack.build(destination)
