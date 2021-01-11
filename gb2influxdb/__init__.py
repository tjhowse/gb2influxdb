#!/usr/bin/python3
import logging
import sqlite3
import json
import click
import requests
from requests.auth import HTTPBasicAuth
from . import version

INFLUXDB_DB_NAME = "gadgetbridge"
# TODO support any GB DB table
METADATA_TABLE = "gb2influxdb_meta"
GADGETBRIDGE_DB_TABLE = "MI_BAND_ACTIVITY_SAMPLE"

DEFAULT_API_PARAMS = {}
DEFAULT_API_PARAMS["precision"] = "s"
DEFAULT_API_PARAMS["epoch"] = "s"
DEFAULT_API_PARAMS["db"] = INFLUXDB_DB_NAME

class gb2influxdb():
    def __init__(self, uri, username, password, database):
        self._uri = uri
        if not self._uri.endswith("/"):
            self._uri += "/"
        self._username = username
        self._password = password
        self._database = database
        self._db_schema = self._get_gb_db_schema()
        print(self._db_schema)

    def setup(self):
        try:
            result = self._do_post("CREATE DATABASE gadgetbridge").json()
            if result['results'][0]['statement_id'] != 0:
                raise Exception("Bad response from server: {}".format(result))
        except:
            logging.error("Failed to create gadgetbridge database.")

        # print(self._get_gb_db_rows(GADGETBRIDGE_DB_TABLE, 1610320440))
        self._process_tables()

    def _process_tables(self):
        for table in self._db_schema.keys():
            line_protocol = ''
            if 'timestamp' != self._db_schema[table][0].lower():
                print("Skipping syncing table {} with schema {}.".format(table, self._db_schema[table]))
                continue
            last_time = self._get_last_influxdb_timestamp_in_measurement(table)
            new_rows = self._get_gb_db_rows(table, last_time)

            for row in new_rows:
                line_protocol += self._convert_row_to_influxdb_line(table, row)
            # TODO Batch these max 5k
            self._do_write(line_protocol)
        # print(line_protocol)

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
        result = self._do_get("SELECT * FROM {} ORDER BY time DESC LIMIT 1".format(meas)).json()
        try:
            return result['results'][0]['series'][0]['values'][0][0]
        except:
            return 0

    def _do_get(self, query, extra_params={}):
        params = DEFAULT_API_PARAMS
        params["q"] = query
        params = {**params, **extra_params}
        return requests.get(self._uri+"query", params=params)

    def _do_post(self, query, extra_params={}):
        params = DEFAULT_API_PARAMS
        params["q"] = query
        params = {**params, **extra_params}
        return requests.post(self._uri+"query", params=params)

    def _do_write(self, data, extra_params={}):
        params = DEFAULT_API_PARAMS
        params = {**params, **extra_params}
        return requests.post(self._uri+"write", params=params, data=data)

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

    def _get_gb_db_rows(self, table, time):
        db = sqlite3.connect(self._database)
        db.text_factory = str
        cur = db.cursor()
        result = cur.execute("SELECT * FROM {} WHERE timestamp > {};".format(table, time)).fetchall()
        # rows = sorted(list(zip(*result))[0])
        db.close()
        return result


    def loop_forever(self):
        pass
        # result = self._do_post("CREATE DATABASE gadgetbridge").json()
        # result = self._do_post("DROP DATABASE gadgetbridge").json()
        # print(result)
        # result = self._do_get("SHOW DATABASES").json()
        # print(result)
        # result = self._do_post("CREATE DATABASE gadgetbridge").json()
        # print(result)
        # result = self._do_get("SHOW DATABASES").json()
        # print(result)
        # result = self._do_post("CREATE DATABASE gadgetbridge").json()
        # print(result)
        # self._check_and_create_influxdb_database()
        # print(result.text)



@click.command()
@click.option('--uri', default='http://localhost:8086/', help='The URI of the InfluxDB server.', show_default=True)
@click.option('--username', default='', help='The username to authenticate to the InfluxDB server.', show_default=True)
@click.option('--password', default='', help='The password to authenticate to the InfluxDB server.', show_default=True)
@click.option('--database', default='./gbdb.sqlite3', help='The database file to sync from.', show_default=True)
# @click.option('--interval', default=60, help='The update interval in minutes.', show_default=True)
def main(uri, username, password, database):
    logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S')
    logging.info("Starting gb2influxdb v{}".format(version.version))
    i = gb2influxdb(uri, username, password, database)
    i.setup()
    i.loop_forever()

if __name__ == '__main__':
    print("Hi!")
    # main()