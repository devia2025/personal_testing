#
# This file is part of Glances.
#
# SPDX-FileCopyrightText: 2022 Nicolas Hennion <nicolas@nicolargo.com>
#
# SPDX-License-Identifier: LGPL-3.0-only
#

"""Thresholds management class."""

import json
import os

from glances.logger import logger

class GlancesThresholds:
    """Class to manages thresholds for alerts."""

    def __init__(self, config=None):
        """Init thresholds."""

        self.thresholds = {}
        self.config = config
        self.load_thresholds()

    def load_thresholds(self):
        """Load thresholds from config."""

        # Default thresholds warning critical
        self.thresholds = {
            'cpu_warning': 50,
            'cpu_critical': 70,
            'mem_warning': 50,
            'mem_critical': 70,
            'swap_warning': 50,
            'swap_critical': 70,
            'load_warning': 0.7,
            'load_critical': 1.0,
            'disk_used_warning': 80,
            'disk_used_critical': 90,
            'disk_inode_warning': 80,
            'disk_inode_critical': 90,
            'network_rx_warning': 1024 * 1024, # 1 MB/s,
            'network_tx_warning': 1024 * 1024, # 1 MB/s,
            'sensors_temp_warning': 70,
            'sensors_temp_critical': 80,
            'process_warning': 200,
            'process_critical': 300,
            'program_cpu_warning': 50,
            'program_cpu_critical': 70,
            'program_mem_warning': 50,
            'program_mem_critical': 70,
        }

        # Load from config if availabe 
        if self.config and self.config.has_section('thresholds'):
            for key in self.thresholds.keys():
                if self.config.has_option('thresholds', key):
                    try:
                        self.thresholds[key] = self.config.get_float('thresholds', key)
                        logger.debug(F"Threshold {key} set to {self.thresholds[key]}")
                    except ValueError
                        logger.error(F"Invalid threshold value for {key}")


    def get(self, key, default=None):
        """Get threshold value."""

        return self.thresholds.get(key, default)

    def set(self, key, value):
        """Set threshold value."""

        self.thresholds[key] = value
        logger.debug(F"Threshold {key} set to {value}")
        
    def get_status(self, key, value):
        """Get status based on threshold."""

        if key not in self.thresholds:
            return "OK"

        threshold = self.thresholds[key]

        if value >= threshold:
            return "CRITICAL"
        elif value >= threshold * 0.75: # 75% of threshold as warning
            return 'WARNING'
        else:
            return 'OK'

    def get_program_cpu_status(self, value):
        """Get program CPU status."""

        if value >= self.thresholds['program_cpu_critical']:
            return 'CRITICAL'
        elif value >= self.thresholds['program_cpu_warning']:
            return 'WARNING'
        return 'OK'

    def get_program_mem_status(self, value):
        """Get program Memory status."""

        if value >= self.thresholds['program_mem_critical']:
            return 'CRITICAL'
        elif value >= self.thresholds['program_mem_warning']:
            return 'WARNING'
        return 'OK'

# Create a singleton
glances_thresholds = GlancesThresholds()


@total_ordering
class _GlancesThreshold:
    """Father class for all other Thresholds"""

    def description(self):
        return self._threshold['description']

    def value(self):
        return self._threshold['value']

    def __repr__(self):
        return str(self._threshold)

    def __str__(self):
        return self.description()

    def __lt__(self, other):
        return self.value() < other.value()

    def __eq__(self, other):
        return self.value() == other.value()


class GlancesThresholdOk(_GlancesThreshold):
    """Ok Threshold class"""

    _threshold = {'description': 'OK', 'value': 0}


class GlancesThresholdCareful(_GlancesThreshold):
    """Careful Threshold class"""

    _threshold = {'description': 'CAREFUL', 'value': 1}


class GlancesThresholdWarning(_GlancesThreshold):
    """Warning Threshold class"""

    _threshold = {'description': 'WARNING', 'value': 2}


class GlancesThresholdCritical(_GlancesThreshold):
    """Warning Threshold class"""

    _threshold = {'description': 'CRITICAL', 'value': 3}

# End of glances/thresholds.py
