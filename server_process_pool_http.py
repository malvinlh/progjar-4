import os
import socket
import logging
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor
from http import HttpServer

# Force 'fork' start method so worker processes inherit the listener FD
mp.set_start_method('fork', force=True)

httpserver = HttpServer()

def worker_loop(listener_fd):
    """
    Worker process:
     1. Reconstruct the listening socket from listener_fd
     2. Loop: accept connections, read request, process, send response
    """
    proc_name = mp.current_process().name
    # Recreate the listening socket in this worker
    srv = socket.socket(fileno=listener_fd,
                        family=socket.AF_INET,
                        type=socket.SOCK_STREAM)

    while True:
        try:
            conn, addr = srv.accept()
            logging.warning(f"[{proc_name}] Accepted connection from {addr}")

            # Read request headers
            buffer = b''
            while b'\r\n\r\n' not in buffer:
                chunk = conn.recv(4096)
                if not chunk:
                    break
                buffer += chunk
            if not buffer:
                conn.close()
                continue

            # Split header/body and parse Content-Length
            header_part, _, spill = buffer.partition(b'\r\n\r\n')
            headers = {}
            for line in header_part.split(b'\r\n')[1:]:
                if b': ' in line:
                    key, val = line.split(b': ', 1)
                    headers[key.lower()] = val
            length = int(headers.get(b'content-length', b'0'))

            # Read remaining body
            body = spill
            remaining = length - len(body)
            while remaining > 0:
                chunk = conn.recv(remaining)
                if not chunk:
                    break
                body += chunk
                remaining -= len(chunk)

            # Process the complete request
            full_request = header_part + b'\r\n\r\n' + body
            logging.warning(f"[{proc_name}] Processing {len(full_request)} bytes")
            response = httpserver.proses(full_request)

            # Send response and close
            conn.sendall(response)
            conn.close()

        except Exception as e:
            logging.error(f"[{proc_name}] Error: {e}")

def main():
    logging.basicConfig(level=logging.WARNING,
                        format="%(asctime)s %(levelname)s %(message)s")

    host, port = '0.0.0.0', 8889
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((host, port))
    srv.listen(50)
    logging.warning("Listening on 0.0.0.0:8889 (ProcessPool mode)")

    # Mark listener FD as inheritable by fork
    listener_fd = srv.fileno()
    os.set_inheritable(listener_fd, True)

    WORKERS = 20
    # Pre-fork WORKERS long-running worker_loop tasks
    with ProcessPoolExecutor(max_workers=WORKERS) as pool:
        for _ in range(WORKERS):
            pool.submit(worker_loop, listener_fd)

        try:
            # Keep workers running until shutdown
            pool.shutdown(wait=True)
        except KeyboardInterrupt:
            logging.warning("Server shutting down")
        finally:
            srv.close()

if __name__ == "__main__":
    main()