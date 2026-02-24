<template>
    <div class="programlist">
        <div class="controls">
            <div class="sort-controls">
                <label>Sort by:</label>
                <select v-model="sortKey" @change="onSortChange">
                    <option value="cpu_percent_total">CPU %</option>
                    <option value="memory_percent_total">MEM %</option>
                    <option value="name">Name</option>
                    <option value="pids_count">Processes</option>
                    <option value="threads">Threads</option>
                    <option value="memory_rss">RSS</option>
                </select>
                <button @click="toggleSortDir">{{ sortDir === 'desc' ? '↓' : '↑' }}</button>
            </div>
            <div class="filter-controls">
                <input
                    v-model="filterText"
                    placeholder="Filter programs..."
                    @input="onFilterChange"
                />
                <select v-model="filterKey" @change="onFilterChange">
                    <option value="name">Name</option>
                    <option value="status">Status</option>
                </select>
            </div>
        </div>
        <table class="program-table">
            <thead>
                <tr>
                    <th class="pin-col"></th>
                    <th class="name-col" @click="sort('name')">Program</th>
                    <th class="num-col" @click="sort('pids_count')">PID(s)</th>
                    <th class="num-col" @click="sort('cpu_percent_total')">CPU%</th>
                    <th class="num-col" @click="sort('memory_percent_total')">MEM%</th>
                    <th class="num-col" @click="sort('threads')">THR</th>
                    <th class="num-col" @click="sort('memory_rss')">RSS</th>
                    <th class="actions-col">Actions</th>
                </tr>
            </thead>
            <tbody>
                <template v-for="program in filteredPrograms" :key="program.name">
                    <tr :class="['program-row', program.status.toLowerCase()]">
                        <td class="pin-col">
                            <span v-if="program.pinned" class="pinned">📌</span>
                        </td>
                        <td class="name-col" @click="toggleExpand(program.name)">
                            <span class="expand-icon">{{expanded[program.name] ? '⮟' : '➤'}}</span>
                            {{ program.name }}
                        </td>
                        <td class="num-col">{{ program.pids_count }}</td>
                        <td class="num-col" :class="getCpuClass(program)">
                            {{ program.cpu_percent_total.toFixed(1) }}
                        </td>
                        <td class="num-col" :class="getMemClass(program)">
                            {{ program.memory_percent_total.toFixed(1) }}
                        </td>
                        <td class="num-col">{{ program.threads }}</td>
                        <td class="num-col">{{ formatBytes(program.memory_rss) }}</td>
                        <td class="actions-col">
                            <button
                                v-if="!program.pinned"
                                @click="pinProgram(program.name)"
                                class="pin-btn"    
                            >
                                📌 Pin
                            </button>
                            <button
                                v-else
                                @click="unpinProgram(program.name)"
                                class="unpin-btn"    
                            >
                                📌 Unpin
                            </button>
                        </td>
                    </tr>
                    <tr v-if="expanded[program.name]" class="processes-row">
                        <td colspan="8">
                            <table class="processes-table">
                                <thead>
                                    <tr>
                                        <th>PID</th>
                                        <th>Process</th>
                                        <th>CPU%</th>
                                        <th>MEM%</th>
                                        <th>RSS</th>
                                        <th>Status</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr v-for="proc in program.processes.slice(0, 10)" :key="proc.pid">
                                        <td>{{ proc.pid }}</td>
                                        <td>{{ proc.name }}</td>
                                        <td>{{ proc.cpu_percent.toFixed(1) }}</td>
                                        <td>{{ proc.memory_percent.toFixed(1) }}</td>
                                        <td>{{ formatBytes(proc.memory_rss) }}</td>
                                        <td>{{ proc.status }}</td>
                                    </tr>
                                    <tr v-if="program.processes.length > 10">
                                        <td colspan="6" class="more-processes">
                                            ... and {{ program.processes.length - 10 }} more processes
                                        </td>
                                    </tr>
                                </tbody>
                            </table>
                        </td>
                    </tr>
                </template>
            </tbody>
        </table>
    </div>
</template>

<script>

export default {
    name: 'Programlist',
	props: {
		stats: {
			type: Array,
            default: () => []
		}
	},
	data() {
		return {
			sortKey: 'cpu_percent_total',
            sortDir: 'desc',
            filterText: '',
            filterKey: 'name',
            expanded: {}
		};
	},
	computed: {
		filteredPrograms(){
            let programs = {...this.stats};

            // Apply filter
            if (this.filterText) {
                const filterLower = this.filterText.toLowerCase();
                programs = programs.filter(proc => {
                    if (this.filterKey === 'name') {
                        return proc.name.toLowerCase().includes(filterLower);
                    }else if (this.filterKey === 'status') {
                        return proc.status.toLowerCase().includes(filterLower);
                    }
                    return true;
                });
            }

            // Apply sorting
            programs.sort((a, z) => {
                let aValue = a[this.sortKey] || 0;
                let zValue = z[this.sortKey] || 0;

                if (this.sortKey === 'name') {
                    aValue = aValue.toString().toLowerCase();
                    zValue = zValue.toString().toLowerCase();
                }

                if (this.sortDir === 'desc') {
                    return aValue > zValue ? -1 : aValue < zValue ? 1 : 0;
                } else {
                    return aValue < zValue ? -1 : aValue > zValue ? 1 : 0;
                }
            });

            // Moving pinned to top
            const pinned = programs.filter(proc => proc.pinned);
            const unpinned = programs.filter(proc => !proc.pinned);
            return [...pinned, ...unpinned];
        }
	},
    methods: {
        sort(key) {
            if (this.sortKey === key) {
                this.sortDir = this.sortDir === 'desc' ? 'asc' : 'desc';
            } else {
                this.sortKey = key;
                this.sortDir = 'desc';
            }
            this.$emit('sort-change', { key: this.sortKey, dir: this.sortDir });
        },
        toggleSortDir() {
            this.sortDir = this.sortDir == 'desc' ? 'asc' : 'desc';
            this.$emit('sort-change', { key: this.sortKey, dir: this.sortDir }); 
        },
        onFilterChange() {
            this.$emit('filter-change', {
                text: this.filterText,
                key: this.filterKey
            });
        },
        toggleExpand(name) {
            this.$emit(this.expanded, name, !this.expanded(name));
        },
        pinProgram(name) {
            this.$emit('pin', name);
        },
        unpinProgram(name) {
            this.$emit('unpin', name);
        },
        formatBytes(bytes) {
            if (bytes === 0) return '0 Byte'
            const k = 1024;
            const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
            const x = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, x)).toFixed(1)) + ' ' + sizes[x];
        },
        getCpuClass(program) {
            if (program.cpu_status === 'CRITICAL') return 'critical';
            if (program.cpu_status === 'WARNING') return 'warning';
            return '';
        },
        getMemClass(program) {
            if (program.mem_status === 'CRITICAL') return 'critical';
            if (program.mem_status === 'WARNING') return 'warning';
            return '';
        }
    }
};
</script>

<style scoped>

.programlist {
    font-family: monospace;
    font-size: 12px;
}

.controls {
    display: flex;
    justify-content: space-between;
    margin-bottom: 10px;
    padding: 5px;
    background: #f5f5f5;
    border-radius: 3px;
}

.sort-controls, .filter-controls {
    display: flex;
    gap: 5px;
    align-items: center;
}

.sort-controls select, .filter-control select, .filter-controls input {
    padding: 3px;
    border: 1px solid #ccc;
    border-radius: 3px;
}

.sort-controls button {
    width: 25px;
    height: 25px;
    border: 1px solid #ccc;
    border-radius: 3px;
    background: white;
    cursor: pointer;
}

.program-table {
    width: 100%;
    border-collapse: collapse;
}

.program-table th{
    text-align: left;
    padding: 5px;
    background: #e0e0e0;
    cursor: pointer;
    user-select: none;
}

.program-table th:hover{
    background: #d0d0d0;
}

.processes-row {
    border-bottom: 1px solid #eee;
    cursor: pointer;
}

.processes-row td {
    padding: 10px;
    background: #f5f5f5;
}

.processes-row:hover {
    background-color: #f9f9f9;
}

.processes-row.critical {
    background-color: rgb(225, 0, 0, 0.1);
}

.processes-row.warning {
    background-color: rgb(225, 225, 0, 0.1);
}

.pin-col {
    width: 30px;
    text-align: center;
}

.name-col {
    width: 250px;
}

.num-col {
    width: 60px;
    text-align: left;
}

.actions-col {
    width: 100px;
    text-align: center;
}

.pinned {
    color: #f1c40f;
}

.expand-icon {
    display: inline-block;
    width: 15px;
    margin-right: 5px;
    color: #666;
}

.critical {
    color: #e74c3c;
    font-weight: bold;
}

.warning {
    color: #f39c12;
}

.pin-btn, .unpin-btn {
    padding: 2px 5px;
    border: 1px solid #ccc;
    border-radius: 3px;
    background: white;
    cursor: pointer;
    font-size: 11px;
}

.pin-btn:hover {
    background: #e0e0e0;
}

.unpin-btn {
    background: #f1c40f;
    border-color: #e67e22;
}

.processes-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 11px;
}

.processes-table th {
    text-align: left;
    padding: 3px;
    background: #e0e0e0;
}

.processes-table td {
    padding: 3px;
    border-bottom: 1px solid #ddd;
}

.more-processes {
    text-align: center;
    padding: 5px;
    color: #999;
    font-style: italic;
}
</style>