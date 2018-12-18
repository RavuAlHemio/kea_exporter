import time

import requests

import argparse

from prometheus_client import start_http_server

from kea import KeaExporter

def parse_args():
    parser = argparse.ArgumentParser(description='Prometheus exporter for ISC Kea 1.4')

    required_named = parser.add_argument_group('required named arguments')
    required_named.add_argument('-t', '--target', help='Target address and port of Kea server, e.g. http://kea.example.com:8080', required=True)
    parser.add_argument('--port', type=int, default=9547, help='Port on which to expose metrics and web interface (default=9547)')
    parser.add_argument('--interval', type=int, default=10, help='Specify the metrics update interval in seconds.')

    return parser.parse_args()

def cli():
    try:
        args = parse_args()
        port = int(args.port)
        exporter = KeaExporter(args.target)
        exporter.update()
        start_http_server(port)
        print("Polling {}. Listening on ::{}".format(args.target, port))
        while True:
            time.sleep(args.interval)
            exporter.update()
    except KeyboardInterrupt:
        print(" Keyboard interrupt, exiting...")
        exit(0)

if __name__ == '__main__':
    cli()
