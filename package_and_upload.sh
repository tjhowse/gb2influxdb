#!/bin/bash
version=v`cat ./gb2influxdb/version.py | cut -d\" -f2`
rm ./dist/gb2influxdb*.whl
rm ./dist/gb2influxdb*.tar.gz
python3 setup.py bdist_wheel
python3 -m twine upload dist/*
# docker build -t tjhowse/gb2influxdb:latest -t tjhowse/gb2influxdb:"$version" .
# docker push tjhowse/gb2influxdb:latest
# docker push tjhowse/gb2influxdb:"$version"
