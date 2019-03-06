#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2019 Chris Caron <lead2gold@gmail.com>
# All rights reserved.
#
# This code is licensed under the MIT License.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files(the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and / or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions :
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import click
import logging
import sys

from . import NotifyType
from . import Apprise
from . import AppriseAsset
from . import AppriseConfig
from .utils import parse_list
from . import __title__
from . import __version__
from . import __license__
from . import __copywrite__

# Logging
logger = logging.getLogger('apprise.plugins.NotifyBase')

# Defines our click context settings adding -h to the additional options that
# can be specified to get the help menu to come up
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])

# Define our default configuration we use if nothing is otherwise specified
DEFAULT_SEARCH_PATHS = (
    'file://~/.apprise',
    'file://~/.apprise.yml',
    'file://~/.config/apprise',
    'file://~/.config/apprise.yml',
)


def print_help_msg(command):
    """
    Prints help message when -h or --help is specified.

    """
    with click.Context(command) as ctx:
        click.echo(command.get_help(ctx))


def print_version_msg():
    """
    Prints version message when -V or --version is specified.

    """
    result = list()
    result.append('{} v{}'.format(__title__, __version__))
    result.append(__copywrite__)
    result.append(
        'This code is licensed under the {} License.'.format(__license__))
    click.echo('\n'.join(result))


@click.command(context_settings=CONTEXT_SETTINGS)
@click.option('--title', '-t', default=None, type=str,
              help='Specify the message title.')
@click.option('--body', '-b', default=None, type=str,
              help='Specify the message body.')
@click.option('--config', '-c', default=None, type=str, multiple=True,
              help='Specify one or more configuration locations.')
@click.option('--notification-type', '-n', default=NotifyType.INFO, type=str,
              metavar='TYPE', help='Specify the message type (default=info).')
@click.option('--theme', '-T', default='default', type=str,
              help='Specify the default theme.')
@click.option('--tag', '-g', default=None, type=str, multiple=True,
              help='Specify one or more tags to reference.')
@click.option('-v', '--verbose', count=True)
@click.option('-V', '--version', is_flag=True,
              help='Display the apprise version and exit.')
@click.argument('urls', nargs=-1,
                metavar='SERVER_URL [SERVER_URL2 [SERVER_URL3]]',)
def main(title, body, config, urls, notification_type, theme, tag, verbose,
         version):
    """
    Send a notification to all of the specified servers identified by their
    URLs the content provided within the title, body and notification-type.

    """
    # Note: Click ignores the return values of functions it wraps, If you
    #       want to return a specific error code, you must call sys.exit()
    #       as you will see below.

    # Logging
    ch = logging.StreamHandler(sys.stdout)
    if verbose > 2:
        logger.setLevel(logging.DEBUG)

    elif verbose == 1:
        logger.setLevel(logging.INFO)

    else:
        logger.setLevel(logging.ERROR)

    if version:
        print_version_msg()
        sys.exit(0)

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # Prepare our asset
    asset = AppriseAsset(theme=theme)

    # Create our object
    a = Apprise(asset=asset)

    # Load our configuration if no URLs or specified configuration was
    # identified on the command line
    a.add(AppriseConfig(
        paths=DEFAULT_SEARCH_PATHS
        if not (config or urls) else config), asset=asset)

    # Load our inventory up
    for url in urls:
        a.add(url)

    if len(a) == 0:
        logger.error(
            'You must specify at least one server URL or populated '
            'configuration file.')
        print_help_msg(main)
        sys.exit(1)

    if body is None:
        # if no body was specified, then read from STDIN
        body = click.get_text_stream('stdin').read()

    # each --tag entry comprises of a comma separated 'and' list
    # we or each of of the --tag and sets specified.
    tags = None if not tag else [parse_list(t) for t in tag]

    # now print it out
    if a.notify(
            body=body, title=title, notify_type=notification_type, tag=tags):
        sys.exit(0)
    sys.exit(1)
