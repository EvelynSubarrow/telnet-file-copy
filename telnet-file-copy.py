#!/usr/bin/env python3

import socket, select, sys, time, os, argparse, hashlib

parser = argparse.ArgumentParser()
parser.add_argument('host')
parser.add_argument("port", type=int)

parser.add_argument('file_here', type=argparse.FileType("rb"))
parser.add_argument('file_there')
parser.add_argument("-v", "--verbose", action="store_true", help="verbose output")
parser.add_argument("-b", "--block-size", type=int, default=200, help="Number of bytes transferred each line")
parser.add_argument("-R", "--no_removal", action="store_true", help="Do not attempt to remove file first")
parser.add_argument("-H", "--no-hash-verification", action="store_true", default=False, help="Do not attempt to verify file hash")
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

    if not args.no_removal:
        s.send("rm {}\n".format(args.file_there).encode("utf8"))
    s.send(b"echo READY\n")

    hash = hashlib.new("md5")

    data = f.read(args.block_size)
    hash.update(data)

    buffer_read = b""
    i = 0

    done = False
    start_time = time.time()
    while not done:
        if select.select([s], [], [], 10)[0]:
            recv_data = s.recv(4096)
            lines = (buffer_read+recv_data).split(b"\n")
            buffer_read = b""
            if lines:
                if lines[-1]:
                    buffer_read = lines.pop(-1)

            for line in lines:
                line = line.rstrip(b"\r")
                if args.verbose:
                    print(line)
                if line==b"READY" and data:
                    s.send("echo -ne '{}' >{} {} ; echo READY\n".format(
                            ''.join([r"\x%02X" % a for a in data]),
                            ">"*bool(i),
                            args.file_there
                        ).encode("utf8"))

                    print("\r{}/{} {}s".format(i*args.block_size + len(data), file_size, int(time.time()-start_time)), end='')
                    data = f.read(args.block_size)
                    hash.update(data)
                    i += 1
                elif line==b"READY":
                    if not args.no_hash_verification:
                        s.send("echo HASH `md5sum {}`\n".format(args.file_there).encode("utf8"))
                    else:
                        done=True
                elif line.startswith(b"HASH "):
                    remote_hash = line.split(b" ")[1].decode("utf8")
                    local_hash = hash.hexdigest()
                    print()
                    print("Local  hash {}".format(local_hash))
                    print("Remote hash {}".format(remote_hash))
                    print("Hashes {}".format("match"*(local_hash==remote_hash) or "do not match"))
                    if local_hash==remote_hash:
                        exit(os.EX_OK)
                    else:
                        exit(os.EX_PROTOCOL)
        else:
            print()
            print("Read timed out")
            exit(os.EX_IOERR)
    print()
    exit(os.EX_OK)
