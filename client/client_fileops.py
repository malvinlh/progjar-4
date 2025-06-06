# client_fileops.py

import socket
import sys
import os
import logging

def send_raw_request(host, port, raw_request_bytes):
    """
    Kirim request mentah (bytes) ke server di host:port, 
    lalu tunggu sampai '\r\n\r\n' sebagai penanda akhir response.
    Kembalikan isi response (strings).
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))
    except Exception as e:
        print(f"[Error] Cannot connect to {host}:{port} → {e}")
        return None

    try:
        sock.sendall(raw_request_bytes)
        data_received = b""
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            data_received += chunk
            if b"\r\n\r\n" in data_received:
                break
    except Exception as e:
        print(f"[Error] During send/receive → {e}")
    finally:
        sock.close()

    try:
        return data_received.decode(errors='ignore')
    except:
        return data_received.decode('iso-8859-1', errors='ignore')


def do_list(host, port):
    """
    Mengirim GET /list HTTP/1.0
    """
    request = (
        "GET /list HTTP/1.0\r\n"
        "Host: {}\r\n"
        "User-Agent: client-fileops/1.0\r\n"
        "Accept: text/plain\r\n"
        "\r\n"
    ).format(host)

    resp = send_raw_request(host, port, request.encode())
    print("=== RESPONSE (LIST) ===")
    print(resp)
    print("========================")


def do_upload(host, port, local_path, target_name=None):
    """
    Mengunggah file lokal local_path ke server dengan nama target_name.
    Jika target_name None → gunakan basename(local_path).
    Kirim request:
      POST /upload/<target_name> HTTP/1.0
      Content-Length: <panjang body>
      Content-Type: application/octet-stream
      \r\n
      <isi file biner>
    """
    if not os.path.exists(local_path) or not os.path.isfile(local_path):
        print(f"[Error] File lokal '{local_path}' tidak ditemukan.")
        return

    if target_name is None:
        target_name = os.path.basename(local_path)

    # Baca seluruh file dalam mode biner
    with open(local_path, 'rb') as f:
        isi = f.read()

    # Bangun header
    hdr = (
        f"POST /upload/{target_name} HTTP/1.0\r\n"
        f"Host: {host}\r\n"
        f"User-Agent: client-fileops/1.0\r\n"
        f"Content-Length: {len(isi)}\r\n"
        f"Content-Type: application/octet-stream\r\n"
        f"\r\n"
    )

    # gabungkan header (bytes) + body (bytes)
    raw = hdr.encode('iso-8859-1') + isi
    resp = send_raw_request(host, port, raw)
    print("=== RESPONSE (UPLOAD) ===")
    print(resp)
    print("==========================")


def do_delete(host, port, target_name):
    """
    Menghapus file di server dengan nama target_name:
      DELETE /delete/<target_name> HTTP/1.0
      Host: <host>
      User-Agent: client-fileops/1.0
      \r\n
    """
    hdr = (
        f"DELETE /delete/{target_name} HTTP/1.0\r\n"
        f"Host: {host}\r\n"
        f"User-Agent: client-fileops/1.0\r\n"
        f"\r\n"
    )
    resp = send_raw_request(host, port, hdr.encode())
    print("=== RESPONSE (DELETE) ===")
    print(resp)
    print("==========================")


if __name__ == "__main__":
    """
    Cara pemanggilan:
    1) python client_fileops.py list <thread|process>
    2) python client_fileops.py upload <thread|process> <path_local> [<nama_target>]
    3) python client_fileops.py delete <thread|process> <nama_target>
    """

    if len(sys.argv) < 3:
        print("Usage:")
        print("  python client_fileops.py list <thread|process>")
        print("  python client_fileops.py upload <thread|process> <path_local> [<nama_target>]")
        print("  python client_fileops.py delete <thread|process> <nama_target>")
        sys.exit(1)

    operasi = sys.argv[1].lower()
    mode = sys.argv[2].lower()
    if mode == 'thread':
        host, port = 'localhost', 8885
    elif mode == 'process':
        host, port = 'localhost', 8889
    else:
        print("Mode harus 'thread' atau 'process'.")
        sys.exit(1)

    if operasi == 'list':
        do_list(host, port)

    elif operasi == 'upload':
        if len(sys.argv) < 4:
            print("Contoh: python client_fileops.py upload thread ./test.txt file_baru.txt")
            sys.exit(1)
        path_local = sys.argv[3]
        nama_target = None
        if len(sys.argv) == 5:
            nama_target = sys.argv[4]
        do_upload(host, port, path_local, nama_target)

    elif operasi == 'delete':
        if len(sys.argv) < 4:
            print("Contoh: python client_fileops.py delete process file_baru.txt")
            sys.exit(1)
        target = sys.argv[3]
        do_delete(host, port, target)

    else:
        print("Operasi tidak dikenal:", operasi)
        sys.exit(1)
