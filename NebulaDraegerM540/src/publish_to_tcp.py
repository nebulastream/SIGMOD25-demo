import socket
import logging
import threading

tcp_servers = {}
tcp_clients = {}
client_lock = threading.Lock()

def publish_tcp(signal_name, timestamp_iso, param_value, config):
    """send data to a single connected client on the specified TCP server"""

    server_key = f"{config['tcp_host']}:{config['tcp_port']}"

    # start server in background if not already running
    if server_key not in tcp_servers:
        start_tcp_server(config)

    with client_lock:
        client_socket = tcp_clients.get(server_key)

    if client_socket:
        try:
            message = f"{timestamp_iso},{param_value}\n"
            client_socket.sendall(message.encode())
            logging.info(f"[TCP] Sent to {server_key}: {message.strip()}")
        except Exception as e:
            logging.warning(f"[TCP] Error sending data to {server_key}: {e}")
            with client_lock:
                client_socket.close()
                tcp_clients[server_key] = None  # Reset on failure
    else:
        logging.warning(f"[TCP] No active client for {server_key}")


def start_tcp_server(config):
    """starts the TCP server in a separate thread and listens for connections"""
    server_key = f"{config['tcp_host']}:{config['tcp_port']}"

    if server_key not in tcp_servers:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # allow reuse of address
        server_socket.bind((config['tcp_host'], config['tcp_port']))
        server_socket.listen(1)  # only one connection at a time
        logging.info(f"Server started at {server_key}")
        tcp_servers[server_key] = server_socket

    def accept_clients():
        while True:
            try:
                client_socket, client_address = server_socket.accept()
                logging.info(f"Client connected: {client_address} on {server_key}")
                with client_lock:
                    tcp_clients[server_key] = client_socket
            except Exception as e:
                logging.error(f"Error accepting client on {server_key}: {e}")

    # start server in a new thread
    server_thread = threading.Thread(target=accept_clients, daemon=True)
    server_thread.start()


'''
# no server just clients sending to server
import socket
import logging

tcp_clients = {}

def publish_tcp(signal_name, timestamp_iso, param_value, config):

    broker_key = f"{config['tcp_host']}:{config['tcp_port']}"

    # reuse existing connection or create a new one
    if broker_key not in tcp_clients:
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect((config["tcp_host"], config["tcp_port"]))
            tcp_clients[broker_key] = client
            logging.info(f"Connected to TCP server {broker_key}")
        except Exception as e:
            logging.warning(f"Failed to connect to TCP server {broker_key}: {e}")
            return

    client = tcp_clients[broker_key]

    message = f"{timestamp_iso},{param_value}\n"
    try:
        client.sendall(message.encode())
        logging.info(f"TCP SENT {signal_name}: {message.strip()}")
    except Exception as e:
        logging.warning(f"Failed to send data to {broker_key}: {e}")
        client.close()
        del tcp_clients[broker_key]  # remove bad connection

'''

'''
import queue
import socket
import time
from threading import Thread, Lock

BUFFER = queue.Queue() # thread-safe shared buffer
BUFFER_LOCK = Lock() # lock for buffer manipulation

def handle_tcp_client(client_socket):
    try:
        while True:
            with BUFFER_LOCK:
                if not BUFFER.empty():
                    data = []
                    while not BUFFER.empty():
                        data.append(BUFFER.get())
                    message = "\n".join(data) + "\n"
                    client_socket.send(message.encode())
            time.sleep(1)
    except:
        client_socket.close()

def start_tcp_server(host='172.18.0.1', port=5000):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen(5)

    print(f"Server listening on {host}:{port}")

    while True:
        client, addr = server.accept()
        print(f"Connected to client: {addr}")
        client_thread = Thread(target=handle_tcp_client, args=(client,))
        client_thread.daemon = True
        client_thread.start()

def add_to_buffer(data):
    with BUFFER_LOCK:
        BUFFER.put(data)

def buffer_filler():
    counter = 0
    while True:
        add_to_buffer(f"Message {counter}")
        counter += 1
        time.sleep(2)

if __name__ == "__main__":
    #start_tcp_server("172.18.0.1",5000)
    Thread(target=start_tcp_server, args=("172.18.0.1",5000,), daemon=True).start()
    #run()

connection = None

def publish_tcp(signal_name, timestamp_iso, param_value, config):
    """Send data over TCP based on the signal configuration."""

    global connection

    tcp_host = "localhost"
    tcp_port = 12345

    if connection is None:
        connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        connection.connect((tcp_host, tcp_port))
        print(f"connected to {tcp_host}:{tcp_port}")

    # Prepare the message to be sent
    message = f"{timestamp_iso},{param_value}"
    connection.sendall(message.encode())
    print(f"TCP SENT {signal_name}: {message}")
'''

