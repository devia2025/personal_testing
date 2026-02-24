#
# This file is part of Glances.
#
# SPDX-FileCopyrightText: 2024 Nicolas Hennion <nicolas@nicolargo.com>
#
# SPDX-License-Identifier: LGPL-3.0-only
#
#

"""Glances plugin initialization."""

# Import plugins
from glances.plugins.alerts import Plugin as AlertPlugin
from glances.plugins.amps import Plugin as AmpsPlugin
from glances.plugins.cloud import Plugin as CloudPlugin
from glances.plugins.connections import Plugin as ConnectionsPlugin

from glances.plugins.containers import Plugin as ContainersPlugin
from glances.plugins.cpu import Plugin as CpuPlugin
from glances.plugins.diskio import Plugin as DiskioPlugin
from glances.plugins.folders import Plugin as FoldersPlugin
from glances.plugins.fs import Plugin as FsPlugin
from glances.plugins.gpu import Plugin as GpuPlugin
from glances.plugins.help import Plugin as HelpPlugin
from glances.plugins.ip import Plugin as IpPlugin
from glances.plugins.irq import Plugin as IrqPlugin
from glances.plugins.load import Plugin as LoadPlugin

from glances.plugins.mem import Plugin as MemPlugin
from glances.plugins.memswap import Plugin as MemswapsPlugin
from glances.plugins.network import Plugin as NetworkPlugin
from glances.plugins.now import Plugin as NowPlugin
from glances.plugins.npu import Plugin as NpuPlugin
from glances.plugins.percpu import Plugin as PercpuPlugin
from glances.plugins.ports import Plugin as PortsPlugin
from glances.plugins.processcount import Plugin as ProcesscountPlugin
from glances.plugins.processlist import Plugin as ProcesslistPlugin
from glances.plugins.programlist import Plugin as ProgramlistPlugin

from glances.plugins.psutilversion import Plugin as psutilversionPlugin
from glances.plugins.quicklook import Plugin as QuicklookPlugin
from glances.plugins.raid import Plugin as RaidPlugin
from glances.plugins.sensors import Plugin as SensorsPlugin
from glances.plugins.smart import Plugin as SmartPlugin
from glances.plugins.system import Plugin as SystemPlugin
from glances.plugins.uptime import Plugin as UptimePlugin
from glances.plugins.version import Plugin as VersionPlugin
from glances.plugins.vms import Plugin as VmsPlugin
from glances.plugins.wifi import Plugin as WifiPlugin

# List of available plugins
__all__ = [
    'AlertPlugin',
    'AmpsPlugin',
    'CloudPlugin',
    'ConnectionsPlugin',
    'ContainersPlugin',
    'CpuPlugin',
    'DiskioPlugin',
    'FoldersPlugin',
    'FsPlugin',
    'GpuPlugin',
    'HelpPlugin',
    'IpPlugin',
    'IrqPlugin',
    'LoadPlugin',
    'MemPlugin',
    'MemswapsPlugin',
    'NetworkPlugin',
    'NowPlugin',
    'NpuPlugin',
    'PercpuPlugin',
    'PortsPlugin',
    'ProcesscountPlugin',
    'ProcesslistPlugin',
    'ProgramlistPlugin',
    'psutilversionPlugin',
    'QuicklookPlugin',
    'RaidPlugin',
    'SensorsPlugin',
    'SmartPlugin',
    'SystemPlugin',
    'UptimePlugin',
    'VersionPlugin',
    'VmsPlugin',
    'WifiPlugin',
]

# End of glances/plugins/__init__.py
