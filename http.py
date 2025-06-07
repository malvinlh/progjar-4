import os
from datetime import datetime, timezone

class HttpServer:
    """
    Core HTTP server functionality:
      - GET: serve files or directory listings
      - POST: upload files under /upload/
      - DELETE: remove files
    """
    def __init__(self):
        # Mapping of file extensions to MIME types
        self.types = {
            '.pdf': 'application/pdf',
            '.jpg': 'image/jpeg',
            '.txt': 'text/plain',
            '.html': 'text/html'
        }
        # Base directory for all file operations
        self.basedir = os.path.abspath('.')

    def response(self, status=404, reason='Not Found', body=b'', headers=None):
        """
        Build an HTTP/1.0 response:
         - Status line
         - Standard headers (Date, Server, Connection)
         - Content-Length + any extra headers
         - Body
        """
        if headers is None:
            headers = {}

        # Format date in GMT per RFC1123
        date_str = datetime.now(timezone.utc).strftime('%a, %d %b %Y %H:%M:%S GMT')

        # Ensure body is bytes
        if not isinstance(body, bytes):
            body = body.encode()

        # Standard response lines
        lines = [
            f"HTTP/1.0 {status} {reason}\r\n",
            f"Date: {date_str}\r\n",
            "Server: myserver/1.0\r\n",
            "Connection: close\r\n",
            f"Content-Length: {len(body)}\r\n"
        ]
        # Add custom headers
        for key, val in headers.items():
            lines.append(f"{key}: {val}\r\n")
        lines.append("\r\n")

        return ''.join(lines).encode() + body

    def proses(self, raw_request: bytes):
        """
        Parse the raw request into method, path, headers, and body,
        then dispatch to the correct handler.
        """
        header_part, _, body = raw_request.partition(b'\r\n\r\n')
        lines = header_part.decode('utf-8', 'ignore').split('\r\n')
        try:
            method, path = lines[0].split()[:2]
            method = method.upper()
        except ValueError:
            return self.response(400, 'Bad Request', b'Malformed request')

        if method == 'GET':
            return self.http_get(path, lines[1:])
        if method == 'POST':
            return self.http_post(path, lines[1:], body)
        if method == 'DELETE':
            return self.http_delete(path, lines[1:])
        return self.response(405, 'Method Not Allowed', b'')

    def get_safe_path(self, url_path: str):
        """
        Convert URL path to a filesystem path under basedir,
        preventing directory traversal.
        """
        segment = url_path.lstrip('/')
        abs_path = os.path.normpath(os.path.join(self.basedir, segment))
        if not abs_path.startswith(self.basedir):
            return None
        return abs_path

    def list_directory(self, url_path: str):
        """
        Return a plain-text index of the given directory.
        """
        fs_path = self.get_safe_path(url_path)
        if not fs_path:
            return self.response(403, 'Forbidden', b'Access denied')
        if not os.path.isdir(fs_path):
            return self.response(404, 'Not Found', b'Not a directory')

        entries = sorted(os.listdir(fs_path))
        lines = [f"Index of {url_path}", "-"*40]
        for name in entries:
            suffix = '/' if os.path.isdir(os.path.join(fs_path, name)) else ''
            lines.append(name + suffix)
        body = ('\n'.join(lines) + '\n').encode()
        return self.response(200, 'OK', body, {'Content-Type': 'text/plain'})

    def http_get(self, url_path: str, header_lines):
        """
        Serve a file or directory listing.
        """
        if url_path.endswith('/'):
            return self.list_directory(url_path)

        fs_path = self.get_safe_path(url_path)
        if not fs_path or not os.path.isfile(fs_path):
            return self.response(404, 'Not Found', b'')

        with open(fs_path, 'rb') as f:
            content = f.read()
        ext = os.path.splitext(fs_path)[1].lower()
        ctype = self.types.get(ext, 'application/octet-stream')
        return self.response(200, 'OK', content, {'Content-Type': ctype})

    def http_post(self, url_path: str, header_lines, body: bytes):
        """
        Handle file upload via POST to /upload/<filename>.
        """
        if not url_path.startswith('/upload/'):
            return self.response(400, 'Bad Request', b'Uploads must go to /upload/<filename>')

        filename = url_path[len('/upload/'):]
        fs_path = self.get_safe_path(filename)
        if not fs_path:
            return self.response(403, 'Forbidden', b'Invalid path')

        os.makedirs(os.path.dirname(fs_path), exist_ok=True)
        try:
            with open(fs_path, 'wb') as f:
                f.write(body)
            msg = f"File '{filename}' uploaded\n".encode()
            return self.response(201, 'Created', msg, {'Content-Type': 'text/plain'})
        except Exception as e:
            return self.response(500, 'Internal Server Error', str(e).encode())

    def http_delete(self, url_path: str, header_lines):
        """
        Handle file deletion via DELETE /<filename>.
        """
        fs_path = self.get_safe_path(url_path)
        if not fs_path:
            return self.response(403, 'Forbidden', b'Access denied')
        if not os.path.isfile(fs_path):
            return self.response(404, 'Not Found', b'')

        try:
            os.remove(fs_path)
            return self.response(204, 'No Content', b'')
        except Exception as e:
            return self.response(500, 'Internal Server Error', str(e).encode())