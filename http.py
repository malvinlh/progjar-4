import sys
import os
import os.path
from datetime import datetime, timezone

class HttpServer:
    def __init__(self):
        self.sessions = {}
        self.types = {}
        self.types['.pdf'] = 'application/pdf'
        self.types['.jpg'] = 'image/jpeg'
        self.types['.txt'] = 'text/plain'
        self.types['.html'] = 'text/html'
        self.basedir = os.path.abspath('.') # Jadikan direktori dasar sebagai path absolut

    def response(self, kode=404, message='Not Found', messagebody=bytes(), headers={}):
        # Gunakan datetime.utcnow() untuk waktu GMT dan format sesuai standar RFC 1123
        tanggal = datetime.now(timezone.utc).strftime('%a, %d %b %Y %H:%M:%S GMT')
        
        resp = []
        resp.append(f"HTTP/1.0 {kode} {message}\r\n")
        resp.append(f"Date: {tanggal}\r\n")
        resp.append("Connection: close\r\n")
        resp.append("Server: myserver/1.0\r\n")
        
        if not isinstance(messagebody, bytes):
            messagebody = messagebody.encode()

        resp.append(f"Content-Length: {len(messagebody)}\r\n")
        for kk in headers:
            resp.append(f"{kk}: {headers[kk]}\r\n")
        resp.append("\r\n")

        response_headers = ''.join(resp)
        return response_headers.encode() + messagebody

    def proses(self, data_bytes): # Menerima BYTES
        # Pisahkan header dan body dari bytes
        header_part, _, body_part = data_bytes.partition(b'\r\n\r\n')
        
        # Decode header untuk diproses sebagai string
        header_lines = header_part.decode('utf-8', errors='ignore').split('\r\n')
        baris = header_lines[0]
        all_headers_str = header_lines[1:]

        j = baris.split(" ")
        try:
            method = j[0].upper().strip()
            object_address = j[1].strip()

            if method == 'GET':
                return self.http_get(object_address, all_headers_str)
            if method == 'POST':
                return self.http_post(object_address, all_headers_str, body_part) # Mengirim body bytes
            if method == 'DELETE':
                return self.http_delete(object_address, all_headers_str)
            else:
                return self.response(400, 'Bad Request', b'Unsupported method')
        except IndexError:
            return self.response(400, 'Bad Request', b'Malformed request line')

    def get_safe_path(self, path_segment):
        safe_segment = path_segment.strip('/')
        requested_path = os.path.normpath(os.path.join(self.basedir, safe_segment))
        if not os.path.abspath(requested_path).startswith(self.basedir):
            return None
        return os.path.abspath(requested_path)

    def list_directory(self, path):
        safe_path = self.get_safe_path(path)
        if safe_path is None: return self.response(403, 'Forbidden', b'Access denied')
        if not os.path.isdir(safe_path): return self.response(404, 'Not Found', f'{path} is not a directory'.encode())
        try:
            items = os.listdir(safe_path)
            directories = sorted([d for d in items if os.path.isdir(os.path.join(safe_path, d))])
            files = sorted([f for f in items if os.path.isfile(os.path.join(safe_path, f))])
            output_lines = [f"Index of: {path}", "="*40]
            for d in directories: output_lines.append(f"{d}/")
            for f in files: output_lines.append(f)
            plain_text_body = "\n".join(output_lines) + "\n"
            return self.response(200, 'OK', plain_text_body.encode(), {'Content-Type': 'text/plain'})
        except Exception as e:
            return self.response(500, 'Internal Server Error', str(e).encode())

    def http_get(self, object_address, headers):
        if object_address.endswith('/'): return self.list_directory(object_address)
        safe_path = self.get_safe_path(object_address)
        if safe_path is None or not os.path.exists(safe_path) or not os.path.isfile(safe_path):
            return self.response(404, 'Not Found', b'')
        with open(safe_path, 'rb') as f: isi = f.read()
        fext = os.path.splitext(safe_path)[1]
        content_type = self.types.get(fext, 'application/octet-stream')
        return self.response(200, 'OK', isi, {'Content-type': content_type})
            
    def http_post(self, object_address, headers, body_bytes):
        if not object_address.startswith('/upload/'):
            return self.response(400, 'Bad Request', b'POST to /upload/ endpoint only')
        
        filename = object_address[len('/upload/'):]
        safe_path = self.get_safe_path(filename)
        if safe_path is None:
            return self.response(403, 'Forbidden', b'Cannot write outside base directory')

        try:
            destination_dir = os.path.dirname(safe_path)
            os.makedirs(destination_dir, exist_ok=True)
            
            with open(safe_path, 'wb') as f:
                f.write(body_bytes)
            
            # TAMBAHKAN CONTENT-TYPE DI SINI
            headers_resp = {'Content-Type': 'text/plain'}
            return self.response(201, 'Created', f'File {filename} created successfully.'.encode(), headers_resp)
            
        except Exception as e:
            return self.response(500, 'Internal Server Error', str(e).encode())
            
    def http_delete(self, object_address, headers):
        safe_path = self.get_safe_path(object_address)
        if safe_path is None:
            return self.response(403, 'Forbidden', b'Access denied')
        
        if not os.path.exists(safe_path) or not os.path.isfile(safe_path):
            return self.response(404, 'Not Found', f'File {object_address} not found.'.encode())
            
        try:
            os.remove(safe_path)
            # Kirim respons 204 tanpa body dan tanpa header tambahan
            return self.response(204, 'No Content', b'')

        except Exception as e:
            return self.response(500, 'Internal Server Error', str(e).encode())