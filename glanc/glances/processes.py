#
# This file is part of Glances.
#
# SPDX-FileCopyrightText: 2024 Nicolas Hennion <nicolas@nicolargo.com>
#
# SPDX-License-Identifier: LGPL-3.0-only
#

import os
import re
import psutil
import threading
from collections import defaultdict

from glances.logger import logger
from glances.timer import Timer
from glances.globals import iteritems, itervalues
from glances.programs import processes_to_programs
from glances.processes_tree import processes_tree_manager

# Importing programs aggregator
from glances.programs import glances_programs

# This constant by default, hide Glances and psutil processes
# by default, hide Glances and psutil processes
HIDE_PROCESS_FILTER = ['glances', 'psutil']

# This constant for Psutil process cache timeout
PSUTIL_PROCESS_CACHE_TIMEOUT = 1

# Adding program aggrepation support
class GlancesProcesses:
    """Class manages the processes table."""

    def __init__(self, cache_timeout=PSUTIL_PROCESS_CACHE_TIMEOUT):
        # Building the current process list
        self.processes = []
        # Process count, number of processes
        self.processcount = None

        # Process list, sorted by cpu
        self.sorted_by = 'cpu_percent'

        # Process filter
        self.process_filter = None
        self.process_filter_key = None
        # Process filter input, search
        self.process_filter_input = None
        # Process filter key for auto
        self.process_filter_auto_key = None

        # Process maximum
        self.process_max = None

        # Disable Process, if can't grab stats
        self.disable_process = False
        # The stats buffer, for delta
        self.stats_buffer = {}
        # Set the cache timeout
        self.cache_timeout = cache_timeout
        # Manage a lock for process list
        self._lock = threading.lock()
        # Manage process tree
        self._tree_manager = processes_tree_manager

        # Store process I/O counters, for rate 
        self.io_old = {}
        self.io_new = {}

        # Initialize
        self.update()

    def __get_uptime(self):
        """Get system uptime."""

        try:
            with open ('/proc/uptime', 'r') as s:
                uptime_seconds = float(s.readline().split()[0])
            return uptime_seconds
        except Exception:
            return None

    def __get__process_stats(self, proc, uptime):
        """Get process stats."""

        try:
            # Get process info
            with proc.onshot():
                # Get process name
                name = proc.name()
                # Get process cmdline
                cmdline = proc.cmdline()

                if not cmdline:
                    cmdline = [name]

                # Get process status
                status = proc.status()

                # Get process CPU percent
                cpu_percent = proc.cpu_percent()
                # Get process memory percent
                memory_percent = proc.memory_percent()
                # Get process memory info
                memory_info = proc.memory_info()
                # Get process number of threads
                num_threads = proc.num_threads()

                # Get process number of connections
                try:
                    num_connections = len(proc.num_connections())
                except Exception:
                    num_connections = 0
                
                # Get process IO counters
                try:
                    io_counters = proc.io_counters()
                except Exception:
                    io_counters = None

                # Get process create time
                create_time = proc.create_time()

            # Calculate process uptime
            if uptime:
                process_uptime = uptime - create_time
            else:
                process_uptime = 0

            # Building the process dict
            process = {
                'pid': proc.pid,
                'name': name,
                'cmdline': cmdline,
                'status': status,
                'cpu_percent': cpu_percent,
                'memory_percent': memory_percent,
                'memory_rss': memory_info.rss,
                'memory_vms': memory_info.vms,
                'num_threads': num_threads,
                'num_connections': num_connections,
                'io_counters': io_counters,
                'create_time': create_time,
                'uptime': process_uptime,
            }

            return process

        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            return None

    def __build_process_list(self):
        """Build the process list."""

        # Reset process list
        self.processes = []

        # Get system uptime
        uptime = self.__get_uptime()

        #for loop
        # Iterate over all processes
        for process_unit in psutil.process_iter():
            try:
                # Get process stats
                process = self.__get_process_stats(process_unit, uptime)

                if process is None:
                    continue
                
                # Applying hide filter
                if process['name'] in HIDE_PROCESS_FILTER:
                    continue

                # Apply user filter if set
                if self.process_filter:
                    if not self._match_filter(process, self.process_filter, self.process_filter_key):
                        continue      

                # Add process to list
                self.processses.append(process)

            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        # Update process count
        self.processcount =len(self.processes)

        # Update programs aggregator with new processes
        glances_programs.update(self.processes)

        # Sorting process list
        self._sort_processes()

    def _sort_processes(self):
        """Sort process list by current sort key."""

        reverse = True if self.sorted_by in [
            'cpu_percent',
            'memory_percent',
            'memory_rss',
            'memory_vms',
            'num_threads'
        ] else False
        
        self.processes.sort(
            key=lambda d: d.get(self.sorted_by, 0),
            reverse=reverse
        )

    def _match_filter(self, process ,filter_string, filter_key):
        """Checking if process matches the filter."""

        if filter_key == 'name':
            value = process['name']
        elif filter_key == 'cmdline':
            value = ' '.join(process['cmdline'])
        elif filter_key == 'status':
            value = process['status']
        elif filter_key == 'username':
            value = process.get('username', '')
        else:
            value = str(process.get(filter_key, ''))

        try:
            return re.search(filter_string, value, re.IGNORECASE) is not None
        except re.error:
            return filter_string.lower() in value.lower()


    def update(self):
        """Update the process list."""

        with self._lock:
            # Build new process list
            self.__build_process_list()

    def update(self):
        """Update the process list."""

        with self._lock:
            # Build new process list
            self.__build_process_list()

    def get_processes(self, sort_key=None, filter=None, filter_key=None, pinned=None):
        """Get process list with optional filtering and sorting."""

        with self._lock:
            processes = self.processes.copy()

            # Updating sort key if provided
            if sort_key:
                self.sorted_by = sort_key
                self.sort_processes()

            # Apply filter if provided
            if filter and filter_key:
                processes = [s for s in processes if self._match_filter(s, filter, filter_key)]

            # Apply pinning if provided
            if pinned:
                # Mark pinned processes
                for p in processes:
                    if p['pid'] in pinned:
                        p['pinned'] = True

                # Moving pinned processes to top
                pinned_p = [proc for proc in processes if proc.get('pinned', False)]
                unpinned_p = [proc for proc in processes if not proc.get('pinned', False)]
                processes = pinned_p + unpinned_p

            return processes

    def get_processcount(self):
        """Get process count."""

        return self.processcount
        
    def get_programs(self, **kwarg):
        """Getting aggregated programs view."""

        return glances_programs.get_programs(**kwarg)
        
    def get_process_tree(self):
        """Get process tree."""

        return self._tree_manager.get_tree(self.processes)
    
    def set_sort_key(self, sort_key):
        """Set sort key."""

        self.sorted_by = sort_key
        self._sort_processes()

    def set_filter(self, filter_string, filter_key='name'):
        """Set the process filter."""

        self.process_filter = filter_string
        self.process_filter_key = filter_key

    def clear_filter(self):
        """Clear the process filter."""

        self.process_filter = None
        self.process_filter_key = None

    def disable(self):
        """Disable process monitoring."""

        self.disable_process = True

    def enable(self):
        """Enable process monitoring."""

        self.disable_process = False

    def get_io_counters(self, pid):
        """Get IO counters for a specific process."""

        # Note: Implementation for IO rate calculation
        pass

# Create a singleton
glances_processes = GlancesProcesses()

# End of file glances/processes.py
