/**
 * Copyright 2020 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

import React from 'react';
import Box from '@material-ui/core/Box';
import Collapse from '@material-ui/core/Collapse';
import IconButton from '@material-ui/core/IconButton';
import Table from '@material-ui/core/Table';
import TableBody from '@material-ui/core/TableBody';
import TableCell from '@material-ui/core/TableCell';
import TableContainer from '@material-ui/core/TableContainer';
import TableHead from '@material-ui/core/TableHead';
import TableRow from '@material-ui/core/TableRow';
import Typography from '@material-ui/core/Typography';
import Paper from '@material-ui/core/Paper';
import KeyboardArrowDownIcon from '@material-ui/icons/KeyboardArrowDown';
import KeyboardArrowUpIcon from '@material-ui/icons/KeyboardArrowUp';

/**
 * A system run describes a run of the executor. A run can perform multiple
 * import attempts.
 */
type SystemRun = {
    run_id: string,
    repo_name: string,
    branch_name: string,
    pr_number: number,
    commit_sha: string,
    time_created: string,
    time_completed: string,
    // Array of attempt IDs. The actual attempts can be retrieved from
    // /import_attempts/{attempt_id}
    import_attempts: Array<string>,
    // Array of log IDs. The actual logs can be retrieved from
    // /system_runs/{run_id}/logs
    logs: Array<string>,
    status: string
}

/**
 * An import attempt is performed by a system run and is an attempt to
 * import a table or a node MCF file to the Data Commons knowledge graph
 * via the Data Commons importer.
 */
type ImportAttempt = {
    attempt_id: string,
    absolute_import_name: string,
    status: string,
    time_created: string,
    time_completed: string,
    provenance_url: string,
    provenance_description: string,
    // Array of log IDs. The actual logs can be retrieved from 
    // /import_attempts/{attempt_id}/logs
    logs: Array<string>
}

/**
 * A log can be linked to a system run, an import attempt, or both.
 */
type ProgressLog = {
    log_id: string,
    time_logged: string,
    level: string,
    message: string
}


type ImportAttemptRowProps = {
    attempt: ImportAttempt
}

type ImportAttemptRowState = {
    // Whether the row is collapsed
    open: boolean,
    logs: Array<ProgressLog>
}

/**
 * A row for an import attempt. The row can be collapsed to show the logs of the
 * import attempt.
 */
class ImportAttemptRow extends React.Component<ImportAttemptRowProps, ImportAttemptRowState> {

    constructor(props: ImportAttemptRowProps) {
        super(props);
        this.state = {
            open: false,
            logs: []
        };
        this._fetchLogs();
    }

    /**
     * Fetches the actual logs using the log IDs, sorts them descendingly by
     * time_logged, and stores them in this.state.logs.
     */
    _fetchLogs() {
        fetch('/import_attempts/' + this.props.attempt.attempt_id + '/logs').then(response => response.json()).then(data => {
            data.sort((log1: ProgressLog, log2: ProgressLog) => log1.time_logged > log2.time_logged ? 1 : -1);
            this.setState({ logs: data });
        });
    }

    /**
     * Generates the drop-down rows, one for each log.
     */
    _generateLogRows() {
        return this.state.logs.map(log => (
            <TableRow key={log.log_id}>
                <TableCell align="right">{log.time_logged}</TableCell>
                <TableCell align="right">{log.level}</TableCell>
                <TableCell align="left">{log.message}</TableCell>
            </TableRow>
        ));
    }

    render() {
        return (
            <React.Fragment>
                <TableRow>
                    <TableCell>
                        <IconButton aria-label="Show Logs" size="small" onClick={() => this.setState({ open: !this.state.open })}>
                            {this.state.open ? <KeyboardArrowUpIcon /> : <KeyboardArrowDownIcon />}
                        </IconButton>
                    </TableCell>
                    <TableCell align="right">{this.props.attempt.absolute_import_name}</TableCell>
                    <TableCell align="right">{this.props.attempt.status}</TableCell>
                    <TableCell align="right">{this.props.attempt.time_created}</TableCell>
                    <TableCell align="right">{this.props.attempt.time_completed}</TableCell>
                    <TableCell align="right">{this.props.attempt.provenance_url}</TableCell>
                    <TableCell align="right">{this.props.attempt.provenance_description}</TableCell>
                </TableRow>
                <TableRow>
                    <TableCell style={{ paddingBottom: 0, paddingTop: 0 }} colSpan={10}>
                        <Collapse in={this.state.open} timeout="auto" unmountOnExit>
                            <Box margin={1}>
                                <Typography variant="h6" gutterBottom component="div">
                                    Import Attempt Logs
                               </Typography>
                                <Table size="small" aria-label="Logs">
                                    <TableHead>
                                        <TableRow>
                                            <TableCell align="right">Time Logged</TableCell>
                                            <TableCell align="right">Level</TableCell>
                                            <TableCell align="left">Message</TableCell>
                                        </TableRow>
                                    </TableHead>
                                    <TableBody>
                                        {this._generateLogRows()}
                                    </TableBody>
                                </Table>
                            </Box>
                        </Collapse>
                    </TableCell>
                </TableRow>
            </React.Fragment>
        );
    }
}


type SystemRunRowProps = {
    run: SystemRun
}

type SystemRunRowState = {
    // Whether the row is collapsed
    open: boolean,
    attempts: Array<ImportAttempt>,
    logs: Array<ProgressLog>
}

/**
 * A row for a system run. The row can be collapsed to show the logs of the
 * system run and the import attempts performed by the system run.
 */
class SystemRunRow extends React.Component<SystemRunRowProps, SystemRunRowState> {

    constructor(props: SystemRunRowProps) {
        super(props);
        this.state = {
            open: false,
            attempts: [],
            logs: []
        };
        this._fetchLogs();
        this._fetchAttempts();
    }

    /**
     * Fetches the actual import attempts using the attempt IDs and stores
     * them in this.state.attempts.
     */
    _fetchAttempts() {
        const attemptIds = this.props.run.import_attempts || []
        const attempts: Array<ImportAttempt> = []
        attemptIds.map(id => fetch('/import_attempts/' + id).then(response => response.json()).then(data => {
            attempts.push(data);
            if (attempts.length === attemptIds.length) {
                this.setState({ attempts: attempts });
            }
        }));
    }

    /**
     * Generates the drop-down rows, one for each import attempt.
     */
    _generateAttemptRows() {
        return this.state.attempts.map(attempt => (
            <ImportAttemptRow key={attempt.attempt_id} attempt={attempt} />
        ));
    }

    /**
     * Fetches the actual logs using the log IDs, sorts them descendingly by
     * time_logged, and stores them in this.state.logs.
     */
    _fetchLogs() {
        fetch('/system_runs/' + this.props.run.run_id + '/logs').then(response => response.json()).then(data => {
            data.sort((log1: ProgressLog, log2: ProgressLog) => log1.time_logged > log2.time_logged ? 1 : -1);
            this.setState({ logs: data });
        });
    }

    /**
     * Generates the rows for the logs. These go above the drop-down
     * rows for the import attempts.
     */
    _generateLogRows() {
        return this.state.logs.map(log => (
            <TableRow key={log.log_id}>
                <TableCell align="right">{log.time_logged}</TableCell>
                <TableCell align="right">{log.level}</TableCell>
                <TableCell align="left">{log.message}</TableCell>
            </TableRow>
        ));
    }

    render() {
        return (
            <React.Fragment>
                <TableRow>
                    <TableCell>
                        <IconButton aria-label="Show Import Attempts" size="small" onClick={() => this.setState({ open: !this.state.open })}>
                            {this.state.open ? <KeyboardArrowUpIcon /> : <KeyboardArrowDownIcon />}
                        </IconButton>
                    </TableCell>
                    <TableCell align="right">{this.props.run.status}</TableCell>
                    <TableCell align="right">{this.props.run.time_created}</TableCell>
                    <TableCell align="right">{this.props.run.time_completed}</TableCell>
                    <TableCell align="right">{this.props.run.repo_name}</TableCell>
                    <TableCell align="right">{this.props.run.branch_name}</TableCell>
                    <TableCell align="right">{this.props.run.pr_number}</TableCell>
                    <TableCell align="right">{this.props.run.commit_sha}</TableCell>
                </TableRow>
                <TableRow>
                    <TableCell style={{ paddingBottom: 0, paddingTop: 0 }} colSpan={10}>
                        <Collapse in={this.state.open} timeout="auto" unmountOnExit>
                            <Box margin={1}>
                                <Typography variant="h6" gutterBottom component="div">
                                    System Run Logs
                                </Typography>
                                <Table size="small" aria-label="System Run Logs">
                                    <TableHead>
                                        <TableRow>
                                            <TableCell align="right">Time Logged</TableCell>
                                            <TableCell align="right">Level</TableCell>
                                            <TableCell align="left">Message</TableCell>
                                        </TableRow>
                                    </TableHead>
                                    <TableBody>
                                        {this._generateLogRows()}
                                    </TableBody>
                                </Table>
                                <Typography variant="h6" gutterBottom component="div">
                                    Import Attempts
                                </Typography>
                                <Table size="small" aria-label="Import Attempts">
                                    <TableHead>
                                        <TableRow>
                                            <TableCell align="right"></TableCell>
                                            <TableCell align="right">Import Name</TableCell>
                                            <TableCell align="right">Status</TableCell>
                                            <TableCell align="right">Time Created</TableCell>
                                            <TableCell align="right">Time Completed</TableCell>
                                            <TableCell align="right">Provenance URL</TableCell>
                                            <TableCell align="right">Provenance Description</TableCell>
                                        </TableRow>
                                    </TableHead>
                                    <TableBody>
                                        {this._generateAttemptRows()}
                                    </TableBody>
                                </Table>
                            </Box>
                        </Collapse>
                    </TableCell>
                </TableRow>
            </React.Fragment>
        );
    }
}


type SystemRunTableProps = {}

type SystemRunTableState = {
    runs: Array<SystemRun>
}


export default class SystemRunTable extends React.Component<SystemRunTableProps, SystemRunTableState> {

    constructor(props: SystemRunTableProps) {
        super(props)
        this.state = {
            runs: []
        }
        this._fetchRuns();
    }

    /**
     * Fetches the most recent system runs, sorts them descendingly by
     * time_created, and stores them in this.state.logs.
     */
    _fetchRuns() {
        fetch('/system_runs').then(response => response.json()).then((runs: Array<SystemRun>) => {
            runs.sort((run1: SystemRun, run2: SystemRun) => run1.time_created < run2.time_created ? 1 : -1);
            this.setState({ runs: runs });
        });
    }

    /**
     * Generates the rows, one for each system run.
     */
    _generateRows() {
        return this.state.runs.map(run => (
            <SystemRunRow key={run.run_id} run={run} />
        ));
    }

    render() {
        return (
            <TableContainer component={Paper}>
                <Table aria-label="System Run Table">
                    <TableHead>
                        <TableRow>
                            <TableCell><b>System Runs</b></TableCell>
                            <TableCell align="right">Status</TableCell>
                            <TableCell align="right">Time Created</TableCell>
                            <TableCell align="right">Time Completed</TableCell>
                            <TableCell align="right">Repo Name</TableCell>
                            <TableCell align="right">Branch Name</TableCell>
                            <TableCell align="right">PR Number</TableCell>
                            <TableCell align="right">Commit SHA</TableCell>
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {this._generateRows()}
                    </TableBody>
                </Table>
            </TableContainer>
        );
    }
}
