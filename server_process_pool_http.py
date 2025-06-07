#!/usr/bin/env python3
import os
import socket
import logging
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor
from http import HttpServer

# 1) Force fork start-method before anything else
mp.set_start_method('fork', force=True)

httpserver = HttpServer()

def worker_loop(listener_fd):
    """
    Each worker reconstructs the listening socket from listener_fd,
    then runs accept()/handle() in a loop.
    """
    proc = mp.current_process().name
    # Recreate the listening socket in this child
    srv = socket.socket(fileno=listener_fd,
                        family=socket.AF_INET,
                        type=socket.SOCK_STREAM)
    # Now enter the accept loop
    while True:
        try:
            conn, addr = srv.accept()
            logging.warning(f"[{proc}] Accepted connection from {addr}")

            # Read full request (headers + body)
            buf = b""
            while b"\r\n\r\n" not in buf:
                chunk = conn.recv(4096)
                if not chunk:
                    break
                buf += chunk

            if not buf:
                conn.close()
                continue

            header, _, spill = buf.partition(b'\r\n\r\n')
            # Parse Content-Length if present
            headers = {}
            for line in header.split(b'\r\n')[1:]:
                if b': ' in line:
                    k,v = line.split(b': ',1)
                    headers[k.lower()] = v
            length = int(headers.get(b'content-length', b'0'))
            body = spill
            to_read = length - len(body)
            while to_read > 0:
                chunk = conn.recv(to_read)
                if not chunk:
                    break
                body += chunk
                to_read -= len(chunk)

            full_req = header + b'\r\n\r\n' + body
            logging.warning(f"[{proc}] Processing {len(full_req)} bytes...")
            resp = httpserver.proses(full_req)
            conn.sendall(resp)
            conn.close()

        except Exception as e:
            logging.error(f"[{proc}] Error: {e}")
            # If accept fails fatally, optionally break
            # break

def main():
    logging.basicConfig(
        level=logging.WARNING,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )

    host, port = '0.0.0.0', 8889
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((host, port))
    srv.listen(50)
    logging.warning(f"[ProcessPool] Listening on {host}:{port} ...")

    # 2) Make the listener FD inheritable
    listener_fd = srv.fileno()
    os.set_inheritable(listener_fd, True)

    # 3) Pre-fork WORKERS processes, each running worker_loop
    WORKERS = 20
    with ProcessPoolExecutor(max_workers=WORKERS) as pool:
        # Submit one long-running worker_loop per process
        for _ in range(WORKERS):
            pool.submit(worker_loop, listener_fd)

        try:
            # Wait here until Ctrl+C
            pool.shutdown(wait=True)
        except KeyboardInterrupt:
            logging.warning("[Server] Shutting down")
        finally:
            srv.close()

if __name__ == "__main__":
    main()
