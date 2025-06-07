import socket
import sys
import os

def send_request(request_bytes):
    """
    Open a TCP connection to server_address, send the raw request bytes,
    receive the full response, and return it as bytes.
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(server_address)
        sock.sendall(request_bytes)

        response = b""
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            response += chunk

        sock.close()
        return response

    except Exception as e:
        return f"Error: {e}".encode()


def list_files(server_address, directory):
    """
    Send a GET request to list the contents of a directory.
    Print response headers and body separately.
    """
    print(f"\n-> Listing '{directory}' on {server_address}")
    request = (
        f"GET {directory} HTTP/1.0\r\n"
        f"Host: {server_address[0]}\r\n"
        "\r\n"
    )
    raw = send_request(request.encode())

    try:
        header, body = raw.split(b'\r\n\r\n', 1)
        print("\n<- Server Response")
        print("--- Headers ---")
        print(header.decode())
        print("\n--- Body ---")
        print(body.decode())
    except (ValueError, UnicodeDecodeError) as e:
        print(f"<- Malformed response: {e}")
        print(raw)


def upload_file(server_address, local_path, remote_name):
    """
    Read a local file and upload it via POST to /upload/<remote_name>.
    """
    print(f"\n-> Uploading '{local_path}' as '{remote_name}' to {server_address}")
    if not os.path.exists(local_path):
        print(f"Error: local file '{local_path}' not found.")
        return

    with open(local_path, 'rb') as f:
        content = f.read()

    header = (
        f"POST /upload/{remote_name} HTTP/1.0\r\n"
        f"Host: {server_address[0]}\r\n"
        f"Content-Length: {len(content)}\r\n"
        "\r\n"
    )
    full_request = header.encode() + content
    response = send_request(full_request)
    print("<- Server Response:\n" + response.decode())


def delete_file(server_address, remote_name):
    """
    Send a DELETE request for /<remote_name>.
    """
    print(f"\n-> Deleting '{remote_name}' on {server_address}")
    request = (
        f"DELETE /{remote_name} HTTP/1.0\r\n"
        f"Host: {server_address[0]}\r\n"
        "\r\n"
    )
    response = send_request(request.encode())
    print("<- Server Response:\n" + response.decode())


if __name__ == "__main__":
    """
    Usage:
      python client_advanced.py host:port list [directory]
      python client_advanced.py host:port upload local_file remote_file
      python client_advanced.py host:port delete remote_file
    """
    if len(sys.argv) < 3:
        print("Usage:")
        print("  python client_advanced.py host:port list [directory]")
        print("  python client_advanced.py host:port upload [local_file] [remote_file]")
        print("  python client_advanced.py host:port delete [remote_file]")
        sys.exit(1)

    host, port_str = sys.argv[1].split(':')
    server_address = (host, int(port_str))
    operation = sys.argv[2].lower()

    if operation == "list":
        dir_path = sys.argv[3] if len(sys.argv) > 3 else "/"
        list_files(server_address, dir_path)
    elif operation == "upload":
        if len(sys.argv) < 5:
            print("Usage: python client_advanced.py host:port upload local_file remote_file")
            sys.exit(1)
        upload_file(server_address, sys.argv[3], sys.argv[4])
    elif operation == "delete":
        if len(sys.argv) < 4:
            print("Usage: python client_advanced.py host:port delete remote_file")
            sys.exit(1)
        delete_file(server_address, sys.argv[3])
    else:
        print(f"Unknown operation: {operation}")
        sys.exit(1)