# server_process_pool_http.py (Versi FINAL dengan Start Method 'spawn')

import socket
import logging
import os
from concurrent.futures import ProcessPoolExecutor
from http import HttpServer
import multiprocessing # <-- Import multiprocessing

# Hapus httpserver = HttpServer() dari scope global

def get_headers(data_bytes):
    # ... (fungsi ini tidak berubah)
    headers = {}
    if b'\r\n' not in data_bytes: return headers
    header_str = data_bytes.split(b'\r\n\r\n')[0].decode('utf-8', errors='ignore')
    lines = header_str.split('\r\n')[1:]
    for line in lines:
        if ': ' in line:
            key, value = line.split(': ', 1)
            headers[key.lower()] = value
    return headers

def ProcessTheClient(client_fd, address):
    # ... (fungsi ini tidak berubah)
    httpserver = HttpServer()
    try:
        connection = socket.fromfd(client_fd, socket.AF_INET, socket.SOCK_STREAM)
        os.close(client_fd)
    except Exception as e:
        logging.error(f"[{address}] Failed to reconstruct socket from fd: {e}")
        return
    try:
        header_buffer = b""
        while b'\r\n\r\n' not in header_buffer:
            data = connection.recv(1024)
            if not data: break
            header_buffer += data
        if not header_buffer:
            connection.close()
            return
        header_part, _, body_spillover = header_buffer.partition(b'\r\n\r\n')
        headers = get_headers(header_part)
        content_length = int(headers.get('content-length', 0))
        body_buffer = body_spillover
        bytes_to_read = content_length - len(body_buffer)
        if bytes_to_read > 0:
            body_buffer += connection.recv(bytes_to_read, socket.MSG_WAITALL)
        full_request = header_part + b'\r\n\r\n' + body_buffer
        logging.warning(f"[{address}] Full request received ({len(full_request)} bytes). Processing...")
        hasil = httpserver.proses(full_request)
        connection.sendall(hasil)
    except Exception as e:
        logging.error(f"[{address}] Unhandled error: {e}")
    finally:
        try:
            connection.shutdown(socket.SHUT_WR)
        except OSError:
            pass
        logging.warning(f"[{address}] Closing connection.")
        connection.close()

def Server():
    # ... (fungsi ini tidak berubah)
    my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    my_socket.bind(('0.0.0.0', 8889))
    my_socket.listen(50)
    logging.warning("[ProcessPool] Listening on 0.0.0.0:8889 ...")
    with ProcessPoolExecutor(max_workers=20) as executor:
        while True:
            try:
                connection, client_address = my_socket.accept()
                logging.warning(f"[Server] Accepted connection from {client_address}")
                client_fd = connection.fileno()
                executor.submit(ProcessTheClient, client_fd, client_address)
                connection.close()
            except KeyboardInterrupt:
                logging.warning("\n[Server] Shutting down.")
                break
            except Exception as e:
                logging.error(f"Error in server loop: {e}")

def main():
    logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s')
    Server()

if __name__ == "__main__":
    # --- PERBAIKAN DI SINI ---
    # Set start method ke 'spawn' untuk isolasi proses yang lebih bersih
    # Ini harus dilakukan di dalam blok if __name__ == "__main__":
    # sebelum fungsi/objek multiprocessing lain dipanggil.
    try:
        multiprocessing.set_start_method('spawn')
    except RuntimeError:
        # Mungkin sudah di-set, abaikan saja errornya
        pass
        
    main()