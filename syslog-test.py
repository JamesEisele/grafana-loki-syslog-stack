'''
This script sends test syslog messages over TCP and UDP to syslog servers
passed on run. Run `python3 syslog-test.py --help` for more info.

Based on Github user xtavras's scripts:
  - https://gist.github.com/xtavras/be13760713e2a9ee1a8bdae2ed6d2565
  - https://gist.github.com/xtavras/4a01f7d1f94237a4abcdfb02074453c1
'''

import argparse
import socket
import logging
from rfc5424logging import Rfc5424SysLogHandler

def main():

    args = parse_arguments()
    syslog_hosts = args.list

    for host in syslog_hosts:
        send_syslog_msg(host=host, port=514, protocol='tcp')
        send_syslog_msg(host=host, port=514, protocol='udp')

def parse_arguments():

    parser = argparse.ArgumentParser(
        prog='syslog-test.py',
        usage='%(prog)s [options]\nexample: python3 %(prog)s syslog-test.py --host 127.0.0.1',
        description='Send test TCP and UDP syslog messages to remote syslog servers.')

    parser.add_argument('-l', '--list', help='List of IPs or hostnames of syslog servers to send messages to.', nargs='+', default=[])  # one or more parameters

    args = parser.parse_args()

    if not args.list:
        parser.error('No syslog host specified to send test messages to. Run with -h flag for more info. Defaulting to "127.0.0.1"...')
        args.list = ['127.0.0.1']
    return args

def send_syslog_msg(host, port, protocol):

    if protocol == 'tcp':
        logger = logging.getLogger('syslog-tcp-test-script')
        rfc5424Handler = Rfc5424SysLogHandler(address=(host, port), socktype=socket.SOCK_STREAM)
        rfc5424Handler.setLevel(logging.DEBUG)
        logger.addHandler(rfc5424Handler)
        logger.warning('this is a TCP test', extra={'msgid': 1})

    elif protocol == 'udp':
        logger = logging.getLogger('syslog-udp-test-script')
        rfc5424Handler = Rfc5424SysLogHandler(address=(host, port), socktype=socket.SOCK_DGRAM)
        rfc5424Handler.setLevel(logging.DEBUG)
        logger.addHandler(rfc5424Handler)
        logger.warning('this is a UDP test', extra={'msgid': 1})

    else:
        print(f' > Unrecognized sylog protocol {protocol}')

    print(f' > Sent syslog message via {protocol.upper()} to {host}:{port}')

if __name__ == '__main__':
    main()