import socket
import logging
from concurrent.futures import ThreadPoolExecutor
from http import HttpServer

httpserver = HttpServer()


def ProcessTheClient(conn, addr):
    """
    Fungsi worker untuk masing-masing koneksi. 
    Menerima data hingga menemukan '\r\n\r\n', lalu parsing dan response.
    """
    rcv_buffer = b""
    try:
        while True:
            data = conn.recv(4096)
            if not data:
                break
            rcv_buffer += data
            # Jika sudah ada header lengkap (deteksi '\r\n\r\n')
            if b"\r\n\r\n" in rcv_buffer:
                # Panggil proses() dengan keseluruhan bytes 
                response_bytes = httpserver.proses(rcv_buffer)
                conn.sendall(response_bytes)
                break
    except OSError:
        pass
    finally:
        conn.close()


def Server():
    the_clients = []
    host = '0.0.0.0'
    port = 8885

    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((host, port))
    srv.listen(50)
    print(f"[ThreadPool] Listening on {host}:{port} ...")

    with ThreadPoolExecutor(max_workers=20) as executor:
        while True:
            conn, addr = srv.accept()
            # Submit ke pool
            future = executor.submit(ProcessTheClient, conn, addr)
            the_clients.append(future)


if __name__ == "__main__":
    Server()
