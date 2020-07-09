import http

import flask_restful
from flask_restful import reqparse

from app import utils
from app.resource import import_attempt
from app.resource import system_run
from app.resource import progress_log
from app.service import import_attempt_database
from app.service import progress_log_database
from app.service import system_run_database


def add_log_to_entity(log_id, entity):
    log_ids = entity.setdefault('logs', [])
    if log_id not in log_ids:
        log_ids.append(log_id)
    return entity


class ProgressLogList(flask_restful.Resource):
    parser = reqparse.RequestParser()
    required_fields = [('level',), ('message',)]
    optional_fields = [('time_logged',), ('run_id',), ('attempt_id',)]
    utils.add_fields(parser, required_fields, required=True)
    utils.add_fields(parser, optional_fields, required=False)

    def __init__(self):
        """Constructs an ImportLog."""
        self.bucket = utils.create_storage_bucket()
        self.datastore_client = utils.create_datastore_client()
        self.run_database = system_run_database.SystemRunDatabase(
            client=self.datastore_client)
        self.log_database = progress_log_database.ProgressLogDatabase(
            client=self.datastore_client)
        self.attempt_database = import_attempt_database.ImportAttemptDatabase(
            client=self.datastore_client)

    def post(self):
        args = ProgressLogList.parser.parse_args()
        if args['level'] not in progress_log.LOG_LEVELS:
            return ('Log level {} is not allowed'.format(args['level']),
                    http.HTTPStatus.FORBIDDEN)
        time_logged = args.setdefault('time_logged', utils.utctime())
        if not utils.iso_utc(time_logged):
            return ('time_logged is not in ISO format with UTC timezone',
                    http.HTTPStatus.FORBIDDEN)

        run_id = args.get('run_id')
        attempt_id = args.get('attempt_id')
        if not run_id and not attempt_id:
            return ('Neither run_id or attempt_id is present',
                    http.HTTPStatus.BAD_REQUEST)
        if run_id:
            run = self.run_database.get_by_id(run_id)
            if not run:
                return system_run.NOT_FOUND_ERROR, http.HTTPStatus.NOT_FOUND
        if attempt_id:
            attempt = self.attempt_database.get_by_id(attempt_id)
            if not attempt:
                return import_attempt.NOT_FOUND_ERROR, http.HTTPStatus.NOT_FOUND
        if run_id and attempt_id:
            if attempt_id not in run['import_attempts']:
                return ('attempt_id in request body not found in the run',
                        http.HTTPStatus.NOT_FOUND)
            # This should never happen
            if attempt['run_id'] != run_id:
                return ('run_id in request body does not match run_id of the '
                        'import attempt',
                        http.HTTPStatus.INTERNAL_SERVER_ERROR)

        log = self.log_database.get_by_id(entity_id=None, make_new=True)
        log.update(args)

        with self.datastore_client.transaction():
            self.log_database.save(log)
            if run_id:
                self.run_database.save(
                    add_log_to_entity(log.id, run)
                )
            if attempt_id:
                self.attempt_database.save(
                    add_log_to_entity(log.id, attempt)
                )

        return args
