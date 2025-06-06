import socket
import sys
import os

def send_request(request_bytes):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(server_address)
        
        sock.sendall(request_bytes)
        
        response = b""
        while True:
            data = sock.recv(4096)
            if not data:
                break
            response += data
        
        sock.close()
        return response
    except Exception as e:
        return f"Error: {e}".encode()

def list_files(server_address, directory):
    print(f"\n-> Listing files in '{directory}' on {server_address}...")
    request_str = f"GET {directory} HTTP/1.0\r\nHost: {server_address[0]}\r\n\r\n"
    raw_response_bytes = send_request(request_str.encode())

    try:
        # Pisahkan header dan body dari respons bytes
        header_part, body_part = raw_response_bytes.split(b'\r\n\r\n', 1)
        
        print("\n<- Server Response:")
        print("--- [Headers] ---")
        # Decode dan print header
        print(header_part.decode())
        print("\n--- [Body] ---")
        # Decode dan print body (yang sudah diformat oleh server)
        print(body_part.decode())

    except (ValueError, UnicodeDecodeError) as e:
        print(f"<- Invalid or malformed response from server: {e}")
        print(raw_response_bytes)


def upload_file(server_address, local_filepath, remote_filename):
    print(f"\n-> Uploading '{local_filepath}' to '{remote_filename}' on {server_address}...")
    if not os.path.exists(local_filepath):
        print(f"Error: File '{local_filepath}' not found.")
        return

    with open(local_filepath, 'rb') as f:
        file_content = f.read()

    request_header_str = (
        f"POST /upload/{remote_filename} HTTP/1.0\r\n"
        f"Host: {server_address[0]}\r\n"
        f"Content-Length: {len(file_content)}\r\n\r\n"
    )
    
    full_request_bytes = request_header_str.encode() + file_content
    response_bytes = send_request(full_request_bytes)
    print("<- Server Response:\n" + response_bytes.decode())


def delete_file(server_address, remote_filename):
    print(f"\n-> Deleting '{remote_filename}' from {server_address}...")
    request_str = f"DELETE /{remote_filename} HTTP/1.0\r\nHost: {server_address[0]}\r\n\r\n"
    response_bytes = send_request(request_str.encode())
    print("<- Server Response:\n" + response_bytes.decode())

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage:")
        print("  python client_advanced.py [host:port] list [directory]")
        print("  python client_advanced.py [host:port] upload [local_file] [remote_file]")
        print("  python client_advanced.py [host:port] delete [remote_file]")
        sys.exit(1)

    host, port_str = sys.argv[1].split(':')
    server_address = (host, int(port_str))
    operation = sys.argv[2]

    if operation == "list":
        dir_path = sys.argv[3] if len(sys.argv) > 3 else "/"
        list_files(server_address, dir_path)
    elif operation == "upload":
        if len(sys.argv) < 5:
            print("Usage: python client_advanced.py [host:port] upload [local_file] [remote_file]")
            sys.exit(1)
        local_file = sys.argv[3]
        remote_file = sys.argv[4]
        upload_file(server_address, local_file, remote_file)
    elif operation == "delete":
        if len(sys.argv) < 4:
            print("Usage: python client_advanced.py [host:port] delete [remote_file]")
            sys.exit(1)
        remote_file = sys.argv[3]
        delete_file(server_address, remote_file)
    else:
        print(f"Unknown operation: {operation}")