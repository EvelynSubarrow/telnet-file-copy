#!/usr/bin/env python3

import socket, select, sys, time, os, argparse

parser = argparse.ArgumentParser()
parser.add_argument('host')
parser.add_argument("port", type=int)

parser.add_argument('file_here', type=argparse.FileType("rb"))
parser.add_argument('file_there')
parser.add_argument("-b", "--block-size", type=int, default=200, help="Number of bytes transferred each line")
parser.add_argument("--username", help="username")
parser.add_argument("--password", help="password")
args = parser.parse_args()

with args.file_here as f, socket.create_connection((args.host, args.port)) as s:
    s.setblocking(0)

    if args.username:
        s.send(args.username.encode("utf8"))
        s.send(b"\n")
    if args.password:
        s.send(args.password.encode("utf8"))
        s.send(b"\n")

    f.seek(0, os.SEEK_END)
    file_size = f.tell()
    f.seek(0)

    s.send(b"echo READY\n")

    data = f.read(args.block_size)
    buffer_read = b""
    i = 0
    start_time = time.time()
    while data:
        if select.select([s], [], [], 10)[0]:
            recv_data = s.recv(4096)
            lines = (buffer_read+recv_data).split(b"\n")
            buffer_read = b""
            if lines:
                if lines[-1]:
                    buffer_read = lines.pop(-1)

            for line in lines:
                line = line.rstrip(b"\r")
                if line==b"READY":
                    s.send("echo -ne '{}' >{} {} ; echo READY\n".format(
                            ''.join([r"\x%02X" % a for a in data]),
                            ">"*bool(i),
                            args.file_there
                        ).encode("utf8"))

                    print("\r{}/{} {}s".format(i*args.block_size + len(data), file_size, int(time.time()-start_time)), end='')
                    data = f.read(args.block_size)
                    i += 1
        else:
            print("Read timed out")
            exit()
    print()
