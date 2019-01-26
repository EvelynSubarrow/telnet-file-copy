#!/usr/bin/env python3

import socket, sys, time, os, argparse

parser = argparse.ArgumentParser()
parser.add_argument('host')
parser.add_argument("port", type=int)

parser.add_argument('file_here', type=argparse.FileType("rb"))
parser.add_argument('file_there')
parser.add_argument("-b", "--block-size", type=int, default=100, help="Number of bytes transferred each line")
parser.add_argument("-d", "--delay", type=float, default=0.4, help="Delay (in seconds) between each line")
parser.add_argument("--username", help="username")
parser.add_argument("--password", help="password")
args = parser.parse_args()

with args.file_here as f, socket.create_connection((args.host, args.port)) as s:
    if args.username:
        s.send(args.username.encode("utf8"))
        s.send(b"\n")
    if args.password:
        s.send(args.password.encode("utf8"))
        s.send(b"\n")

    f.seek(0, os.SEEK_END)
    file_size = f.tell()
    f.seek(0)

    data = f.read(args.block_size)
    i = 0
    start_time = time.time()
    while data:
        s.send("echo -ne '{}' >{} {}\n".format(
                ''.join([r"\x%02X" % a for a in data]),
                ">"*bool(i),
                args.file_there
            ).encode("utf8"))

        print("\r{}/{} {}s".format(i*args.block_size + len(data), file_size, int(time.time()-start_time)), end='')
        time.sleep(args.delay)
        data = f.read(args.block_size)
        i += 1
    print()
