# gb2influxdb

https://github.com/tjhowse/gb2influxdb

https://pypi.org/project/gb2influxdb/

A tool for syncing a Gadgetbridge database export to InfluxDB.

## Installation

### Python module

```bash
$ pip3 install --user gb2influxdb
$ gb2influxdb --help
```

## Usage

I have a Mi Band 5 synchronising to my phone using [Gadgetbridge](https://codeberg.org/Freeyourgadget/Gadgetbridge). I have Gadgetbridge set to
automatically export its database to an SQLite3 database every hour. I use [Syncthing](https://github.com/syncthing/syncthing) to sync that database export to my server. I use gb2influxdb to monitor the synchronised database for changes and push updated data to
my InfluxDB server.

This whole system is a nightmare of interlocking fragile dependencies. I would much rather sync directly from Gadgetbridge to InfluxDB,
but there are [issues](https://codeberg.org/Freeyourgadget/Gadgetbridge/issues/2159) with that approach.