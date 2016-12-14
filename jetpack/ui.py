#!/usr/bin/python
"""Implements user interface."""

import os
import argparse
from six.moves import input, configparser
from . import core

def _exp_path(path):
    return os.path.abspath(os.path.expanduser(path))

if __name__ == '__main__':
    # check config for hanger
    config = configparser.RawConfigParser()
    dot = os.path.join(os.path.expanduser('~'), '.jetpack')
    config.read(dot)
    hanger = None
    hanger_str = ''
    try:
        hanger = config.get('path', 'hanger')
        hanger_str = ' (default: {})'.format(hanger)
    except configparser.NoSectionError:
        config.add_section('path')
    except configparser.NoOptionError:
        pass

    # init arg parser
    description = 'A utility for building jetpack templates.'
    epilog = 'hanger cached in ~/.jetpack'
    parser = argparse.ArgumentParser('jetpack', description=description,
                                     epilog=epilog)
    parser.add_argument('pack',
                        help='pack name')
    parser.add_argument('-s', metavar='hanger', dest='hanger',
                        help='hanger directory{}'.format(hanger_str))
    parser.add_argument('-d', metavar='destination', dest='dest',
                        help='destination directory (default: current ' \
                              'directory)')
    kwargs = vars(parser.parse_args())

    # validate hanger
    update_config = True
    if kwargs.get('hanger'):  # hanger set in terminal
        kwargs['hanger'] = _exp_path(kwargs.get('hanger'))
    elif hanger:  # hanger set in config
        kwargs['hanger'] = _exp_path(hanger)
        print('hanger: {} (default)'.format(kwargs['hanger']))
        update_config = False
    else:  # hanger set interactively
         kwargs['hanger'] = _exp_path(input('hanger: '))

    # update config
    if update_config:
        config.set('path', 'hanger', kwargs.get('hanger'))
        with open(dot, 'w') as f:
            config.write(f)

    # validate dest
    if kwargs.get('dest'):
        kwargs['dest'] = _exp_path(kwargs.get('dest'))
    else:
        kwargs['dest'] = _exp_path(os.curdir)

    # collect kwargs
    kwargs['name'] = input('name: ')
    kwargs['description'] = input('description: ')

    core.launch(**kwargs)
