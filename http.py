import os
import sys
import uuid
from glob import glob
from datetime import datetime

class HttpServer:
    def __init__(self):
        self.sessions = {}
        self.types = {
            '.pdf': 'application/pdf',
            '.jpg': 'image/jpeg',
            '.png': 'image/png',
            '.txt': 'text/plain',
            '.html': 'text/html',
            '.json': 'application/json'
        }

    def response(self, kode=404, message='Not Found', messagebody=b'', headers=None):
        """
        Membangun response HTTP lengkap:
          - Status line: HTTP/1.0 <kode> <message>
          - Header: Date, Server, Content-Length, + custom headers
          - Body: messagebody (bytes)
        """
        if headers is None:
            headers = {}

        tanggal = datetime.now().strftime('%a, %d %b %Y %H:%M:%S %Z')
        resp = []
        resp.append(f"HTTP/1.0 {kode} {message}\r\n")
        resp.append(f"Date: {tanggal}\r\n")
        resp.append("Connection: close\r\n")
        resp.append("Server: myserver/1.0\r\n")

        # Jika body bukan bytes, ubah ke bytes
        if not isinstance(messagebody, bytes):
            messagebody = messagebody.encode()

        resp.append(f"Content-Length: {len(messagebody)}\r\n")
        # Custom headers
        for kk, vv in headers.items():
            resp.append(f"{kk}: {vv}\r\n")
        # Akhiri header
        resp.append("\r\n")

        response_headers = "".join(resp).encode()  # jadi bytes
        return response_headers + messagebody  # gabungkan header+body

    def proses(self, data: bytes):
        """
        data: seluruh request dalam bentuk bytes.
        Kita perlu memisahkan "header" dan "body" (jika ada).
        Struktur request minimal:
            <request‐line>\r\n
            <header1>\r\n
            <header2>\r\n
            ...
            \r\n
            <body (jika ada)>
        """

        try:
            text = data.decode(errors='ignore')
        except:
            # jika gagal decode, langsung return 400
            return self.response(400, 'Bad Request', '')

        # Pisahkan header dan body (hanya sekali split pada \r\n\r\n)
        parts = text.split("\r\n\r\n", maxsplit=1)
        header_part = parts[0]
        body_part = parts[1] if len(parts) > 1 else ""

        lines = header_part.split("\r\n")
        request_line = lines[0].strip()
        header_lines = lines[1:]

        # Parse request line
        try:
            method, raw_path, _ = request_line.split(" ", 2)
            method = method.upper().strip()
            path = raw_path.strip()
        except ValueError:
            return self.response(400, 'Bad Request', '')

        # Parse header ke dict (opsional, bisa digunakan untuk Content-Length, dll)
        headers = {}
        for h in header_lines:
            if ":" in h:
                k, v = h.split(":", 1)
                headers[k.strip().lower()] = v.strip()

        if method == 'GET':
            return self.http_get(path, headers)
        elif method == 'POST':
            return self.http_post(path, headers, body_part)
        elif method == 'DELETE':
            return self.http_delete(path, headers)
        else:
            return self.response(405, 'Method Not Allowed', f"Method {method} not supported.")

    def http_get(self, path, headers):
        """
        - Jika path == '/list', tampilkan daftar file di direktori './'
        - Jika path == '/', tampilkan halaman default
        - Jika path == '/video' atau '/santai', sesuai contoh sebelumnya
        - Jika path merujuk ke file yang ada, kirim file
        """

        # 1) Listing direktori
        if path == '/list':
            try:
                semua = os.listdir('./')
                # Filter hanya file (bukan direktori)
                daftar_file = [f for f in semua if os.path.isfile(f)]
                body = "\r\n".join(daftar_file)
                return self.response(200, 'OK', body, {'Content-Type': 'text/plain'})
            except Exception as e:
                return self.response(500, 'Internal Server Error', f"Error listing: {str(e)}")

        # 2) Halaman default root
        if path == '/':
            body = "Ini Adalah web Server percobaan"
            return self.response(200, 'OK', body, {'Content-Type': 'text/plain'})

        # 3) Redirect contoh
        if path == '/video':
            return self.response(302, 'Found', '',
                                 {'Location': 'https://youtu.be/katoxpnTf04'})

        if path == '/santai':
            return self.response(200, 'OK', 'santai saja', {'Content-Type': 'text/plain'})

        # 4) Jika path merujuk ke file
        # Hilangkan leading '/'
        target = path.lstrip('/')
        if not os.path.exists(target) or not os.path.isfile(target):
            return self.response(404, 'Not Found', 'File not found.')

        # Baca isi file secara binary
        try:
            with open(target, 'rb') as fp:
                isi = fp.read()
            ext = os.path.splitext(target)[1].lower()
            content_type = self.types.get(ext, 'application/octet-stream')
            return self.response(200, 'OK', isi, {'Content-Type': content_type})
        except Exception as e:
            return self.response(500, 'Internal Server Error', f"Cannot read file: {str(e)}")

    def http_post(self, path, headers, body):
        """
        Rute upload:
          POST /upload/<filename> HTTP/1.0
          <headers termasuk Content-Length>
          \r\n
          <body adalah konten file (binary disampaikan “mentah” dalam request)>

        Kita ambil nama file dari path, lalu tulis body (yang mungkin biner).
        """
        # Cek apakah path mengikuti pola /upload/<nama_file>
        if path.startswith("/upload/"):
            nama_file = path[len("/upload/"):]
            if nama_file == "":
                return self.response(400, 'Bad Request', 'Filename tidak diberikan.')

            # Body saat ini diambil sebagai string, tapi file bisa biner → kita kembalikan ke bytes melalui encoding iso-8859-1
            try:
                # decode body asli: 
                isi_bytes = body.encode('iso-8859-1', errors='ignore')
            except:
                isi_bytes = body.encode()

            try:
                with open(nama_file, 'wb') as fw:
                    fw.write(isi_bytes)
                return self.response(201, 'Created', f"File '{nama_file}' berhasil diupload.", {'Content-Type': 'text/plain'})
            except Exception as e:
                return self.response(500, 'Internal Server Error', f"Cannot write file: {str(e)}")

        else:
            return self.response(404, 'Not Found', 'Unknown POST path.')

    def http_delete(self, path, headers):
        """
        Rute delete:
          DELETE /delete/<filename> HTTP/1.0
        """
        if path.startswith("/delete/"):
            nama_file = path[len("/delete/"):]
            if nama_file == "":
                return self.response(400, 'Bad Request', 'Filename tidak diberikan.')

            if not os.path.exists(nama_file) or not os.path.isfile(nama_file):
                return self.response(404, 'Not Found', f"File '{nama_file}' tidak ada.")

            try:
                os.remove(nama_file)
                return self.response(200, 'OK', f"File '{nama_file}' berhasil dihapus.", {'Content-Type': 'text/plain'})
            except Exception as e:
                return self.response(500, 'Internal Server Error', f"Cannot delete file: {str(e)}")
        else:
            return self.response(404, 'Not Found', 'Unknown DELETE path.')
