import socket
import threading
import json

HOST = "127.0.0.1"
PORT = 5000

clients = {}
lock = threading.Lock()


def send_data(client, data):
    message = json.dumps(data) + "\n"
    client.sendall(message.encode("utf-8"))


def broadcast(data, exclude=None):
    with lock:
        disconnected = []

        for client in clients:
            if client != exclude:
                try:
                    send_data(client, data)
                except OSError:
                    disconnected.append(client)

        for client in disconnected:
            clients.pop(client, None)
            try:
                client.close()
            except OSError:
                pass


def update_user_list():
    with lock:
        users = list(clients.values())

    broadcast({
        "type": "users",
        "users": users
    })


def handle_client(client):
    username = None
    buffer = ""

    try:
        while True:
            chunk = client.recv(4096)

            if not chunk:
                break

            buffer += chunk.decode("utf-8")

            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)

                if not line.strip():
                    continue

                data = json.loads(line)

                if data["type"] == "join":
                    requested_name = data["username"].strip()

                    with lock:
                        if any(
                            name.lower() == requested_name.lower()
                            for name in clients.values()
                        ):
                            send_data(client, {
                                "type": "error",
                                "message": "Username already taken."
                            })
                            return

                        username = requested_name
                        clients[client] = username

                    send_data(client, {"type": "joined"})

                    broadcast({
                        "type": "message",
                        "username": "SERVER",
                        "message": f"{username} joined the chat."
                    }, exclude=client)

                    update_user_list()

                elif data["type"] == "message" and username:
                    message = data["message"].strip()

                    if message:
                        broadcast({
                            "type": "message",
                            "username": username,
                            "message": message
                        })

    except (OSError, json.JSONDecodeError):
        pass

    finally:
        with lock:
            old_username = clients.pop(client, None)

        try:
            client.close()
        except OSError:
            pass

        if old_username:
            broadcast({
                "type": "message",
                "username": "SERVER",
                "message": f"{old_username} left the chat."
            })

            update_user_list()


def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    server.bind((HOST, PORT))
    server.listen()

    print(f"Chat server running on {HOST}:{PORT}")
    print("Waiting for clients...")

    try:
        while True:
            client, address = server.accept()

            print("New connection:", address)

            thread = threading.Thread(
                target=handle_client,
                args=(client,),
                daemon=True
            )

            thread.start()

    except KeyboardInterrupt:
        print("\nServer shutting down...")

    finally:
        with lock:
            connected_clients = list(clients.keys())
            clients.clear()

        for client in connected_clients:
            try:
                client.close()
            except OSError:
                pass

        server.close()


if __name__ == "__main__":
    start_server()