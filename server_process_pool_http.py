import socket
import logging
import multiprocessing
from concurrent.futures import ProcessPoolExecutor
from http import HttpServer
import os

httpserver = HttpServer()


def worker_handle(client_fd_and_addr):
    """
    worker di ProcessPool: menerima tuple (fileno, (ip, port))
    Kita rekonstruksi socket dari fileno, kemudian baca data dan proses.
    """
    fileno, addr = client_fd_and_addr
    try:
        # Rekonstruksi socket dari file descriptor
        conn = socket.socket(fileno=fileno, family=socket.AF_INET, type=socket.SOCK_STREAM)
        # Setelah di‐fromfd, kita sebaiknya set socket menjadi non‐inheritable:
        conn.setblocking(True)
        # Perlu menutup 'duplikat' di os; mencegah double‐close
        # (Proses parent punya salinan, child punya salinan. Kita hanya pakai yang di child,
        #  parent akan menutup setelah fork.)
        # Di Linux, setelah fork, kedua proses punya duplikat fd. Kita cukup focus di child.
    except Exception as e:
        return

    rcv_buffer = b""
    try:
        while True:
            data = conn.recv(4096)
            if not data:
                break
            rcv_buffer += data
            if b"\r\n\r\n" in rcv_buffer:
                response_bytes = httpserver.proses(rcv_buffer)
                conn.sendall(response_bytes)
                break
    except OSError:
        pass
    finally:
        try:
            conn.close()
        except:
            pass


def Server():
    host = '0.0.0.0'
    port = 8889

    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((host, port))
    srv.listen(50)
    print(f"[ProcessPool] Listening on {host}:{port} ...")

    # Pastikan child tidak mewarisi listener socket
    srv_fd = srv.fileno()
    os.set_inheritable(srv_fd, True)

    with ProcessPoolExecutor(max_workers=10) as executor:
        while True:
            conn, addr = srv.accept()
            # Setelah accept, kita serahkan ownership FD ke child job
            fileno = conn.fileno()
            # Perintahkan OS agar FD tidak otomatis diwariskan ke generasi proses lain
            os.set_inheritable(fileno, True)
            # Submit tuple (fileno, addr) ke worker
            executor.submit(worker_handle, (fileno, addr))
            # Parent segera close socket, agar FD hanya di‐child
            conn.close()


if __name__ == "__main__":
    Server()
