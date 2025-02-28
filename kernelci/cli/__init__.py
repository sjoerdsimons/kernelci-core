# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2022, 2023 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>
# Author: Jeny Sadadia <jeny.sadadia@collabora.com>

"""KernelCI command line utility package"""

import sys

from .base import Args, Command, parse_opts, sub_main
from . import (
    api,
    config,
    docker,
    job,
    node,
    pubsub,
    show,
    storage,
    user,
)

_COMMANDS = {
    'api': api.main,
    'config': config.main,
    'docker': docker.main,
    'job': job.main,
    'node': node.main,
    'pubsub': pubsub.main,
    'show': show.main,
    'storage': storage.main,
    'user': user.main,
}


def list_command_names():
    """Return a list with the command names"""
    return list(_COMMANDS.keys())


def call(name, args=None):
    """Call a command registered with kernelci.cli

    Call the command with the given *name* and optional arguments *args*.
    """
    cmd = _COMMANDS.get(name)
    if not cmd:
        print("Unknown command: {name}", file=sys.stderr, flush=True)
        sys.exit(1)
    _COMMANDS[name](args)
