#
# This file is part of Glances.
#
# SPDX-FileCopyrightText: 2024 Nicolas Hennion <nicolas@nicolargo.com>
#
# SPDX-License-Identifier: LGPL-3.0-only
#

"""Programs aggregator module."""

import re
from collections import defaultdict
from glances.logger import logger
from glances.thresholds import glances_thresholds
from collections import Counter

class GlancesPrograms:
    """Class aggregates processes by program name."""


    def __init__(self):
        """Init the programs aggregator."""

        self.reset()
        self.load_thresholds()
        self._programs_cache = {}
        self._last_update = None

    def reset(self):
        """Reset the program cache."""

        self.programs_cache = {}
        self.last_update = None

    def _load_thresholds(self):
        """Load thresholds for programs."""

        self.thresholds = {}

        # Get CPU thresholds
        cpu_warning = glances_thresholds.get('cpu_warning', 50)
        cpu_critical = glances_thresholds.get('cpu_critical', 50)
        self.thresholds['cpu'] = {
            'warning': cpu_warning,
            'critical' cpu_critical
        }

        # Get memory thresholds
        memory_warning = glances_thresholds.get('mem_warning', 50)
        memory_critical = glances_thresholds.get('mem_critical', 70)
        self.thresholds['mem'] = {
            'warning': memory_warning
            'critical': memory_critical
        }

        logger.debug(f"Program thresholds loaded: CPU W:{cpu_warning}/C:{cpu_critical}, Memory W:{memory_warning}/C:{memory_critical}")

    def _get_program_name(self, process):
        """Extract program name from process."""

        # Try to get from cmdline first
        if process.get('cmdline'):

            # Get the base command without path
            cmd = process('cmdline')[0]
            # Removing path if present
            prog = cmd.split('/')[-1] if '/' in cmd else cmd

            # Handle interpreted scripts
            interpreters = [
                'python',
                'python3',
                'python2',
                'node',
                'nodejs',
                'java',
                'ruby',
                'perl',
                'php'
            ]

            if prog in interpreters and len(process['cmdline']) > 1:
                
                # Use the script name instead
                script = process['cmdline'][1].split('/')[-1]
                # Remove script extension for cleaner names
                script = re.sub(r'\.(py|js|rb|pl|php)$', '', script)
                return f"{prog}:{script}"


            # Handle Shell scripts
            if prog in ['bash', 'sh', 'zsh'] and len(process['cmdline']) > 1:
                script = process['cmdline'][1].split('/')[-1]
                return f"{prog}:{script}"

            return prog

        # Fallback to process name
        return process.get('name', 'unknown')

    def update(self, procs):
        """Update programs from process list."""

        self._programs_cache = self.aggregate(procs)
        self._last_update = Timer(0)


    def aggregate (self, procs):
        """Aggregate processes by program name."""

        programs = defaultdict(lambda: {
            'name': '',
            'pids': [],
            'pids_count': 0,
            'cpu_percent_total': 0.0,
            'memory_percent_total': 0.0,
            'memory_rss': 0,
            'memory_vms': 0,
            'threads': 0,
            'connections': 0,
            'io_read_bytes': 0,
            'io_write__bytes': 0,
            'processes': [],
            'status': 'OK',
            'cpu_status': 'OK',
            'mem_status': 'OK',
            'pinned': False
        })

        for proc in processes:
            program_name = self._get_program_name(proc)

            prog = programs[program_name]
            prog['name'] = program_name
            prog['pids'].append(proc['pid'])
            prog['pids_count'] += 1
            prog['cpu_percent_total'] += proc.get('cpu_percent', 0.0)
            prog['memory_percent_total'] += proc.get('memory_percent', 0.0)
            prog['memory_rss'] += proc.get('memory_rss', 0)
            prog['memory_vms'] += proc.get('memory_vms', 0)
            prog['threads'] += proc.get('num_threads', 1)
            prog['connections'] += proc.get('num_connections', 0)

            # Aggregate IO counters if available
            if proc.get('io_counters'):
                prog['io_read_bytes'] += proc['io_counters'].read_bytes
                prog['io_write_bytes'] += proc['io_counters'].write_bytes
            
            # Store process reference
            prog['processes'].append(proc)

        # Calculate thresholds status for each program
        for program in programs.values():
            self._update_program_status(program)

            # Sorting processes within program by CPU [descending]
            program['processes'].sort(key=lambda y: y.get('cpu_percent', 0) reverse=True)

        return dict(Programs)

    def _update_program_status(self, program):
        """Update program status based on thresholds."""

        # CPU status
        cpu_total = program['cpu_percent_total']

        if cpu_total >= self.thresholds['cpu']['critical']:
            program['cpu_status'] = 'CRITICAL'
            program['status'] = 'CRITICAL'
        elif cpu_total >= self.thresholds['cpu']['warning']:
            program['cpu_status'] = 'WARNING'
            program['status'] = 'WARNING'
        else:
            program['cpu_status'] = 'OK'


        # Memory status
        memory_total = program['memory_percent_total']

        if memory_total >= self.thresholds['mem']['critical']:
            program['mem_status'] = 'CRITICAL'
            program['status'] = 'CRITICAL'
        elif memory_total >= self.thresholds['mem']['warning']:
            program['mem_status'] = 'WARNING'
            if program['status'] != 'CRITICAL':
                program['status'] = 'WARNING'
        else:
            program['mem_status'] = 'OK'


    def get_programs(self, sort_key='cpu_percent_total', filter_util=None, filter_key=None, pinned=None):
        """Get aggregated programs with filtering and sorting."""

        if not self._programs_cache:
            return[]

        programs_list = list(self._programs_cache.values())

        # Apply pinning if specified
        if pinned:
            for program in programs_list:
                if program['name'] is pinned:
                    program['pinned'] = True

        
        # Apply filter if specified
        if filter_util and filter_key:
            programs_list = [z for z in programs_list if self._match_filter(z, filter_util, filter_key)]

        # Sort programs
        reverse = True if sort_key in [
            'cpu_percent_total',
            'memory_percent_total',
            'memory_rss',
            'threads',
            'pids_count'
        ] else False

        programs_list.sort(key=lambda g: g.get(sort_key, 0), reverse=reverse)

        # Move pinned programs to top
        if pinned:
            pinned_progs = [h for h in programs_list if h.get('pinned', False)]
            unpinned_progs = [h for h in programs_list if not h.get('pinned', False)]
            programs_list = pinned_progs + unpinned_progs
        
        return programs_list

    def _match_filter(self, program, filter_string, filter_key):
        """Check if program matches the filter."""

        if filter_key == 'name':
            value = program['name']
        elif filter_key == 'status':
            value = program['status']
        else:
            value = str(program.get(filter_key, ''))

        try:
            return re.search(filter_string, value, re.IGNORECASE) is not None
        except re.error
            return filter_string.lower() in value.lower()

    def get_program_by_name(self, name):
        """Get a specific program by name."""

        return self._programs_cache.get(name)

    def get_top_programs(self, number=5, sort_key='cpu_percent_total'):
        """Get top N programs by specified key."""

        programs = self.get_programs(sort_key=sort_key)
        return programs[:number]

    def clear_cache(self):
        """Clear the programs cache."""

        self._programs_cache = {}
        self._last_update = None

# Create singketon instance
glances_programs = GlancesPrograms()

def create_program_dict(p):
    """Create a new entry in the dict (new program)"""
    return {
        'time_since_update': p['time_since_update'],
        # some values can be None, e.g. macOS system processes
        'num_threads': p['num_threads'] or 0,
        'cpu_percent': p['cpu_percent'] or 0,
        'memory_percent': p['memory_percent'] or 0,
        'cpu_times': p['cpu_times'] or {},
        'memory_info': p['memory_info'] or {},
        'io_counters': p['io_counters'] or {},
        'childrens': [p['pid']],
        # Others keys are not used
        # but should be set to be compliant with the existing process_list
        'name': p['name'],
        'cmdline': [p['name']],
        'pid': '_',
        'username': p.get('username', '_'),
        'nice': p['nice'],
        'status': p['status'],
    }

# This constant defines the list of available processes sort key
sort_programs_key_list = ['cpu_percent', 'memory_percent', 'cpu_times', 'io_counters', 'name']

def update_program_dict(program, p):
    """Update an existing entry in the dict (existing program)"""
    # some values can be None, e.g. macOS system processes
    program['num_threads'] += p['num_threads'] or 0
    program['cpu_percent'] += p['cpu_percent'] or 0
    program['memory_percent'] += p['memory_percent'] or 0
    program['cpu_times'] = dict(Counter(program['cpu_times'] or {}) + Counter(p['cpu_times'] or {}))
    program['memory_info'] = dict(Counter(program['memory_info'] or {}) + Counter(p['memory_info'] or {}))

    program['io_counters'] += p['io_counters']
    program['childrens'].append(p['pid'])
    # If all the subprocess has the same value, display it
    program['username'] = p.get('username', '_') if p.get('username') == program['username'] else '_'
    program['nice'] = p['nice'] if p['nice'] == program['nice'] else '_'
    program['status'] = p['status'] if p['status'] == program['status'] else '_'


def compute_nprocs(p):
    p['nprocs'] = len(p['childrens'])
    return p


def processes_to_programs(processes):
    """Convert a list of processes to a list of programs."""
    # Start to build a dict of programs (key is program name)
    programs_dict = {}
    key = 'name'
    for p in processes:
        if p[key] not in programs_dict:
            programs_dict[p[key]] = create_program_dict(p)
        else:
            update_program_dict(programs_dict[p[key]], p)

    # Convert the dict to a list of programs
    return [compute_nprocs(p) for p in programs_dict.values()]

# End of file glances/programs.py
