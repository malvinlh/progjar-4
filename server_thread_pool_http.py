# server_thread_pool_http.py (Versi Final untuk mendukung LIST dan UPLOAD)

from socket import *
import socket
import time
import sys
import logging
from concurrent.futures import ThreadPoolExecutor
from http import HttpServer

httpserver = HttpServer()

def get_headers(data_bytes):
    # Fungsi bantuan untuk mem-parsing header dari bytes
    headers = {}
    # Hindari error jika tidak ada header sama sekali
    if b'\r\n' not in data_bytes:
        return headers
        
    header_str = data_bytes.split(b'\r\n\r\n')[0].decode('utf-8', errors='ignore')
    lines = header_str.split('\r\n')[1:] # Abaikan request line pertama
    for line in lines:
        if ': ' in line:
            key, value = line.split(': ', 1)
            headers[key.lower()] = value
    return headers

def ProcessTheClient(connection, address):
    try:
        # --- LOGIKA BARU YANG ANDAL ---
        
        # 1. Baca data sampai seluruh header diterima (ditandai dengan \r\n\r\n)
        header_buffer = b""
        while b'\r\n\r\n' not in header_buffer:
            data = connection.recv(1024)
            if not data:
                break
            header_buffer += data
        
        # Jika tidak ada data sama sekali, tutup koneksi
        if not header_buffer:
            connection.close()
            return
            
        # Pisahkan bagian header dan sisa body yang mungkin sudah terbaca
        header_part, _, body_spillover = header_buffer.partition(b'\r\n\r\n')
        
        # 2. Urai header untuk mendapatkan Content-Length
        headers = get_headers(header_part)
        content_length = int(headers.get('content-length', 0))
        
        # 3. Baca sisa body sesuai Content-Length
        body_buffer = body_spillover
        bytes_to_read = content_length - len(body_buffer)
        
        if bytes_to_read > 0:
            # MSG_WAITALL memastikan kita menerima semua byte yang diminta
            body_buffer += connection.recv(bytes_to_read, socket.MSG_WAITALL)

        # 4. Gabungkan semua bagian menjadi satu request utuh dan proses
        full_request = header_part + b'\r\n\r\n' + body_buffer
        
        logging.warning(f"[{address}] Full request received ({len(full_request)} bytes). Processing...")
        
        hasil = httpserver.proses(full_request)
        
        connection.sendall(hasil)

    except (socket.timeout, ConnectionResetError) as e:
        logging.error(f"[{address}] Connection error: {e}")
    except Exception as e:
        logging.error(f"[{address}] Unhandled error: {e}")
    finally:
        # Pastikan koneksi selalu ditutup
        logging.warning(f"[{address}] Closing connection.")
        connection.close()


def Server():
    my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    my_socket.bind(('0.0.0.0', 8885))
    my_socket.listen(50)
    logging.warning("[ThreadPool] Listening on 0.0.0.0:8885 ...")

    with ThreadPoolExecutor(20) as executor:
        while True:
            try:
                connection, client_address = my_socket.accept()
                logging.warning(f"[Server] Accepted connection from {client_address}")
                executor.submit(ProcessTheClient, connection, client_address)
            except KeyboardInterrupt:
                logging.warning("\n[Server] Shutting down.")
                break
            except Exception as e:
                logging.error(f"Error in server loop: {e}")

def main():
    logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s')
    Server()

if __name__ == "__main__":
    main()