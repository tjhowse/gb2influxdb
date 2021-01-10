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
GADGETBRIDGE_DB_TABLE = "MI_BAND_ACTIVITY_SAMPLE"

class gb2influxdb():
    def __init__(self, uri, username, password, database):
        self._uri = uri
        if not self._uri.endswith("/"):
            self._url += "/"
        self._username = username
        self._password = password
        self._database = database
        self._last_update = 0

    def setup(self):
        try:
            result = self._do_post("CREATE DATABASE gadgetbridge").json()
            if result['results'][0]['statement_id'] != 0:
                raise Exception("Bad response from server: {}".format(result))
        except:
            logging.ERROR("Failed to create gadgetbridge database.")
        # self._do_write("{},TAG1=HI VALUE1=1 1610286963".format(GADGETBRIDGE_DB_TABLE))
        self._get_last_influxdb_timestamp()



    def _get_last_influxdb_timestamp(self):
        # This queries influxdb for the last time we wrote to the gadgetbridge database
        result = self._do_get("SELECT VALUE1 FROM {} ORDER BY time DESC LIMIT 1".format(GADGETBRIDGE_DB_TABLE)).json()
        # {'results': [{'series': [{'name': 'MI_BAND_ACTIVITY_SAMPLE', 'columns': ['time', 'VALUE1'], 'values': [['2021-01-10T13:56:03Z', 1]]}], 'statement_id': 0}]}
        # read out the timestamp it's bedtime.
        print(result)


    def _do_get(self, query):
        params = {}
        params["q"] = query
        params["db"] = INFLUXDB_DB_NAME
        return requests.get(self._uri+"query", params=params)

    def _do_post(self, query):
        params = {}
        params["q"] = query
        params["db"] = INFLUXDB_DB_NAME
        return requests.post(self._uri+"query", params=params)

    def _do_write(self, data):
        params = {}
        params["precision"] = "s"
        params["db"] = INFLUXDB_DB_NAME
        return requests.post(self._uri+"write", params=params, data=data)

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