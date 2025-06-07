from socket import AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR
import socket
import logging
from concurrent.futures import ThreadPoolExecutor
from http import HttpServer

# Initialize HTTP server logic
httpserver = HttpServer()

def get_headers(data_bytes):
    """
    Parse HTTP headers from raw request bytes up to "\r\n\r\n".
    Returns a dict mapping lowercase header names to values.
    """
    if b'\r\n' not in data_bytes:
        return {}
    header_str = data_bytes.split(b'\r\n\r\n', 1)[0].decode('utf-8', errors='ignore')
    lines = header_str.split('\r\n')[1:]  # Skip the request line
    headers = {}
    for line in lines:
        if ': ' in line:
            key, val = line.split(': ', 1)
            headers[key.lower()] = val
    return headers

def ProcessTheClient(conn, addr):
    """
    Handle a single client connection:
     1. Read request headers until "\r\n\r\n"
     2. Parse Content-Length and read the body
     3. Process the full request via HttpServer.proses()
     4. Send the response and close the connection
    """
    try:
        # 1) Read headers
        buffer = b''
        while b'\r\n\r\n' not in buffer:
            chunk = conn.recv(1024)
            if not chunk:
                conn.close()
                return
            buffer += chunk

        header_part, _, spill = buffer.partition(b'\r\n\r\n')

        # 2) Read body if Content-Length is set
        headers = get_headers(header_part)
        length = int(headers.get('content-length', 0))
        body = spill
        if len(body) < length:
            body += conn.recv(length - len(body), socket.MSG_WAITALL)

        # 3) Process request
        full_request = header_part + b'\r\n\r\n' + body
        logging.warning(f"[{addr}] Processing {len(full_request)} bytes")
        response = httpserver.proses(full_request)

        # 4) Send response
        conn.sendall(response)

    except (socket.timeout, ConnectionResetError) as e:
        logging.error(f"[{addr}] Connection error: {e}")
    except Exception as e:
        logging.error(f"[{addr}] Unexpected error: {e}")
    finally:
        logging.warning(f"[{addr}] Closing connection")
        conn.close()

def Server():
    """
    Listen on 0.0.0.0:8885 and dispatch each connection
    to a thread from a fixed-size pool.
    """
    srv = socket.socket(AF_INET, SOCK_STREAM)
    srv.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    srv.bind(('0.0.0.0', 8885))
    srv.listen(50)
    logging.warning("Listening on 0.0.0.0:8885 (ThreadPool mode)")

    with ThreadPoolExecutor(max_workers=20) as pool:
        while True:
            try:
                conn, addr = srv.accept()
                logging.warning(f"Accepted connection from {addr}")
                pool.submit(ProcessTheClient, conn, addr)
            except KeyboardInterrupt:
                logging.warning("Server shutting down")
                break
            except Exception as e:
                logging.error(f"Server loop error: {e}")

def main():
    logging.basicConfig(level=logging.WARNING,
                        format="%(asctime)s %(levelname)s %(message)s")
    Server()

if __name__ == "__main__":
    main()