#!/usr/bin/env python3
"""
Command line tool for MetSim
"""
# Meteorology Simulator
# Copyright (C) 2017  The Computational Hydrology Group, Department of Civil
# and Environmental Engineering, University of Washington.

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import argparse
import json
import logging
import os
import sys
import json
import logging
import argparse
from configparser import SafeConfigParser
from collections import OrderedDict

import click

from metsim.metsim import MetSim, formatter
from metsim.utils import setup_dask


ch = logging.StreamHandler(sys.stdout)
ch.setFormatter(formatter)
logger = logging.getLogger("metsim")


def init(config_file, log_level, time_grouper):
    """Initialize some information based on the options & config"""
    config = ConfigParser()
    config.optionxform = str
    config.read(config_file)
    conf = OrderedDict(config['MetSim'])
    conf['forcing_vars'] = OrderedDict(config['forcing_vars'])
    conf['domain_vars'] = OrderedDict(config['domain_vars'])
    conf['state_vars'] = OrderedDict(config['state_vars'])
    out_dir = conf['out_dir']
    # out_state = conf.get('out_state', None)
    # if out_state is None:
    #     out_state = os.path.join(out_dir, 'state.nc')

    method = conf['method']

    # If the forcing variable is a directory, scan it for files
    if os.path.isdir(conf['forcing']):
        forcing_files = [os.path.join(conf['forcing'], fn) for fn in
                         next(os.walk(conf['forcing']))[2]]
    else:
        forcing_files = conf['forcing']

    # We assume there is only one domain file and one state file
    domain_file = conf['domain']

    def to_list(s):
        return json.loads(s.replace("'", '"'))

    conf.update({"calendar": conf.get('calendar', 'standard'),
                 "method": method,
                 "out_dir": out_dir,
                 "domain": domain_file,
                 "forcing": forcing_files,
                 "log_level": log_level})
    conf['out_vars'] = to_list(conf.get('out_vars', '[]'))
    conf['iter_dims'] = to_list(conf.get('iter_dims', '["lat", "lon"]'))
    conf['time_grouper'] = time_grouper if time_grouper else None
    conf = {k: v for k, v in conf.items() if v != []}
    return conf


@click.command(context_settings=dict(help_option_names=['-h', '--help']))
@click.argument('config', type=click.Path(exists=True))
@click.option('--scheduler', type=str, default=None,
              help='Parallel dask scheduler to use, defaults to '
                   'multiprocessing when num_workers is set.'
                   'Valid options include `distributed`, `multiprocessing`, '
                   '`threaded`, `synchronous` or a path to a dask scheduler '
                   'file.')
@click.option('-n', '--num_workers', default=None, type=int,
              help='Number of workers to use during parallel computations')
@click.option('-tg', '--time_grouper', default=None, type=str, multiple=True,
              help='Pandas TimeGrouper string (e.g. `1AS`)')
@click.option('-v', '--verbose', count=True,
              help='Set the Verbosity of MetSim')
def main(config, scheduler, num_workers, time_grouper, verbose):
    """Runs MetSim"""

    log_level = max(logging.WARNING - verbose * 10, 1)
    logger.setLevel(log_level)
    ch.setLevel(log_level)
    logger.addHandler(ch)

    dask_info = setup_dask(scheduler, num_workers)
    logger.debug(dask_info)

    setup = init(config, log_level, time_grouper)
    ms = MetSim(setup)
    ms.run()


if __name__ == '__main__':
    main()