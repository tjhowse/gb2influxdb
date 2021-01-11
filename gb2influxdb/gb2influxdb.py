#!/usr/bin/python3
import time
import logging
import sqlite3
import pathlib
import click
import requests
from . import version

INFLUXDB_DB_NAME = "gadgetbridge"

DEFAULT_API_PARAMS = {}
DEFAULT_API_PARAMS["precision"] = "s"
DEFAULT_API_PARAMS["epoch"] = "s"
DEFAULT_API_PARAMS["db"] = INFLUXDB_DB_NAME

class gb2influxdb():
    def __init__(self, uri, username, password, database, force):
        self._uri = uri
        if not self._uri.endswith("/"):
            self._uri += "/"
        self._auth = (username, password)
        self._database = database
        self._force = force
        self._db_schema = self._get_gb_db_schema()
        self._db_update_time = 0

    def setup(self):
        try:
            result = self._do_post("CREATE DATABASE gadgetbridge").json()
            if result['results'][0]['statement_id'] != 0:
                raise Exception("Bad response from server: {}".format(result))
        except:
            logging.error("Failed to create gadgetbridge database.")
        self._process_tables()

    def _process_tables(self):
        logging.info("Updating InfluxDB with new data.")
        self._db_update_time = self._get_file_mtime(self._database)
        db = sqlite3.connect(self._database)
        db.text_factory = str
        try:
            for table in self._db_schema.keys():
                line_protocol = ''
                if 'timestamp' != self._db_schema[table][0].lower():
                    logging.debug("Skipping syncing table {} with schema {}.".format(table, self._db_schema[table]))
                    continue
                last_time = self._get_last_influxdb_timestamp_in_measurement(table)
                new_rows = self._get_gb_db_rows(db, table, last_time)
                if len(new_rows) == 0:
                    continue
                logging.info("Syncing {} entries into measurement {}".format(len(new_rows), table))
                for row in new_rows:
                    line_protocol += self._convert_row_to_influxdb_line(table, row)
                # TODO Batch these max 5k
                self._do_write(line_protocol)
        finally:
            db.close()

    def _convert_row_to_influxdb_line(self, table, row):
        column_names = self._db_schema[table]
        result = "{},SOURCE=GBDB ".format(table)
        for (i, column) in enumerate(column_names):
            if i == 0:
                # Skip the timestamp, that goes at the end
                continue
            result += "{}={},".format(column, row[i])

        # Strip the trailing comma.
        result = result[:-1]
        result += " {}\n".format(row[0])
        return result

    def _get_last_influxdb_timestamp_in_measurement(self, meas):
        # This queries influxdb for the last timestamp we wrote to it in unix time
        if self._force:
            # Sync everything, not just data since the last sync.
            return 0
        result = self._do_get("SELECT * FROM {} ORDER BY time DESC LIMIT 1".format(meas)).json()
        try:
            return result['results'][0]['series'][0]['values'][0][0]
        except:
            return 0

    def _do_get(self, query, extra_params={}):
        params = DEFAULT_API_PARAMS
        params["q"] = query
        params = {**params, **extra_params}
        return requests.get(self._uri+"query", auth=self._auth, params=params)

    def _do_post(self, query, extra_params={}):
        params = DEFAULT_API_PARAMS
        params["q"] = query
        params = {**params, **extra_params}
        return requests.post(self._uri+"query", auth=self._auth, params=params)

    def _do_write(self, data, extra_params={}):
        params = DEFAULT_API_PARAMS
        params = {**params, **extra_params}
        return requests.post(self._uri+"write", auth=self._auth, params=params, data=data)

    def _get_gb_db_schema(self):
        db = sqlite3.connect(self._database)
        db.text_factory = str
        cur = db.cursor()
        result = cur.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
        table_names = sorted(list(zip(*result))[0])
        schema = {}
        for table_name in table_names:
            result = cur.execute("PRAGMA table_info('%s')" % table_name).fetchall()
            column_names = list(zip(*result))[1]
            schema[table_name] = column_names
        db.close()
        if 'android_metadata' in schema:
            schema.pop('android_metadata')
        if 'sqlite_sequence' in schema:
            schema.pop('sqlite_sequence')
        return schema

    def _get_gb_db_rows(self, db, table, time):
        cur = db.cursor()
        result = cur.execute("SELECT * FROM {} WHERE timestamp > {};".format(table, time)).fetchall()
        return result

    def _helpful_dump(self):
        # This is just a list of potentially useful code snippets:
        # result = self._do_post("CREATE DATABASE gadgetbridge").json()
        # result = self._do_post("DROP DATABASE gadgetbridge").json()
        # result = self._do_get("SHOW DATABASES").json()
        # result = self._do_post("CREATE DATABASE gadgetbridge").json()
        pass

    def _get_file_mtime(self, file):
        # This returns the modified time of the provided time in unix epoch time
        f = pathlib.Path(file)
        if not f.exists():
            logging.error("Failed to find database at {}".format(file))
            return -1
        return f.stat().st_mtime

    def loop_forever(self):
        logging.info("Monitoring {} for changes.".format(self._database))
        while True:
            if self._db_update_time != self._get_file_mtime(self._database):
                # The database has been updated. Process it.
                self._process_tables()
            time.sleep(60)

@click.command()
@click.option('--uri', default='http://localhost:8086/', help='The URI of the InfluxDB server.', show_default=True)
@click.option('--username', default='', help='The username to authenticate to the InfluxDB server.', show_default=True)
@click.option('--password', default='', help='The password to authenticate to the InfluxDB server.', show_default=True)
@click.option('--database', default='./gbdb.sqlite3', help='The database file to sync from.', show_default=True)
@click.option('--force', default=False, help='Force a full historical sync rather than only sync new data.', show_default=True)
@click.option('--oneshot', default=False, help='Do one sync and quit. Don\'t monitor the database for changes.', show_default=True)
def main(uri, username, password, database, force, oneshot):
    logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S')
    logging.info("Starting gb2influxdb v{}".format(version.version))
    i = gb2influxdb(uri, username, password, database, force)
    i.setup()
    if not oneshot:
        i.loop_forever()

if __name__ == '__main__':
    print("Hi!")
    # main()