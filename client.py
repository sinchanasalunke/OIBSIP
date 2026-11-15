import socket
import threading
import tkinter as tk
from tkinter import simpledialog, messagebox
from tkinter.scrolledtext import ScrolledText
import json
import queue
from datetime import datetime

HOST = "127.0.0.1"
PORT = 5000

# Message queue for safe GUI updates
message_queue = queue.Queue()

client = None
connected = False
receive_buffer = ""


def send_data(data):
    try:
        message = json.dumps(data) + "\n"
        client.sendall(message.encode("utf-8"))
        return True
    except OSError:
        return False


def receive_messages():
    global receive_buffer, connected

    while connected:
        try:
            chunk = client.recv(4096)

            if not chunk:
                break

            receive_buffer += chunk.decode("utf-8")

            while "\n" in receive_buffer:
                line, receive_buffer = receive_buffer.split("\n", 1)

                if line.strip():
                    data = json.loads(line)
                    message_queue.put(data)

        except (OSError, json.JSONDecodeError):
            break

    connected = False
    message_queue.put({
        "type": "disconnected"
    })


def display_message(username, message):
    chat_area.config(state="normal")

    timestamp = datetime.now().strftime("%H:%M")

    chat_area.insert(
        tk.END,
        f"[{timestamp}] {username}: {message}\n"
    )

    chat_area.see(tk.END)
    chat_area.config(state="disabled")


def send_message(event=None):
    message = message_entry.get().strip()

    if not message:
        return

    if send_data({
        "type": "message",
        "message": message
    }):
        message_entry.delete(0, tk.END)


def process_queue():
    global connected

    while True:
        try:
            data = message_queue.get_nowait()
        except queue.Empty:
            break

        if data["type"] == "message":
            display_message(
                data["username"],
                data["message"]
            )

        elif data["type"] == "users":
            user_list.delete(0, tk.END)

            for username in data["users"]:
                user_list.insert(tk.END, username)

        elif data["type"] == "error":
            connected = False
            messagebox.showerror(
                "Connection Error",
                data["message"]
            )
            root.destroy()
            return

        elif data["type"] == "disconnected":
            chat_area.config(state="normal")
            chat_area.insert(
                tk.END,
                "\nDisconnected from server.\n"
            )
            chat_area.config(state="disabled")
            send_button.config(state="disabled")
            message_entry.config(state="disabled")

    if root.winfo_exists():
        root.after(100, process_queue)


def close_app():
    global connected

    connected = False

    try:
        if client:
            client.shutdown(socket.SHUT_RDWR)
            client.close()
    except OSError:
        pass

    root.destroy()


# Ask for username
root = tk.Tk()
root.withdraw()

username = simpledialog.askstring(
    "Login",
    "Enter your username:",
    parent=root
)

if not username or not username.strip():
    root.destroy()
    raise SystemExit

username = username.strip()

if len(username) > 20 or "\n" in username:
    messagebox.showerror(
        "Invalid Username",
        "Username must be 1-20 characters."
    )
    root.destroy()
    raise SystemExit

# Connect to server
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    client.connect((HOST, PORT))

    send_data({
        "type": "join",
        "username": username
    })

    # Wait for server to accept username
    file = client.makefile("r", encoding="utf-8")
    response = json.loads(file.readline())
    file.close()

    if response["type"] != "joined":
        raise ConnectionError(
            response.get("message", "Unable to join chat.")
        )

except (OSError, ConnectionError, json.JSONDecodeError) as error:
    messagebox.showerror(
        "Connection Error",
        f"Could not connect to chat server.\n{error}"
    )
    root.destroy()
    raise SystemExit

connected = True

# Main GUI
root.deiconify()
root.title(f"Chat Application - {username}")
root.geometry("750x520")
root.configure(bg="#20232b")
root.minsize(600, 400)

# Header
header = tk.Frame(root, bg="#343a46", height=65)
header.pack(fill="x")

title = tk.Label(
    header,
    text=f"Python Chat Room | {username}",
    font=("Arial", 18, "bold"),
    bg="#343a46",
    fg="white"
)
title.pack(pady=18)

# Main content
main_frame = tk.Frame(root, bg="#20232b")
main_frame.pack(fill="both", expand=True, padx=12, pady=12)

# Online users section
users_frame = tk.Frame(main_frame, bg="#343a46", width=160)
users_frame.pack(side="right", fill="y", padx=(10, 0))
users_frame.pack_propagate(False)

tk.Label(
    users_frame,
    text="ONLINE USERS",
    font=("Arial", 11, "bold"),
    bg="#343a46",
    fg="white"
).pack(pady=12)

user_list = tk.Listbox(
    users_frame,
    bg="#252a34",
    fg="white",
    font=("Arial", 11),
    borderwidth=0,
    highlightthickness=0
)
user_list.pack(fill="both", expand=True, padx=8, pady=8)

# Chat section
chat_frame = tk.Frame(main_frame, bg="#20232b")
chat_frame.pack(side="left", fill="both", expand=True)

chat_area = ScrolledText(
    chat_frame,
    state="disabled",
    wrap=tk.WORD,
    bg="#292e39",
    fg="white",
    font=("Arial", 11),
    insertbackground="white",
    borderwidth=0
)
chat_area.pack(fill="both", expand=True)

# Message input section
input_frame = tk.Frame(chat_frame, bg="#20232b")
input_frame.pack(fill="x", pady=(10, 0))

message_entry = tk.Entry(
    input_frame,
    font=("Arial", 12),
    bg="#343a46",
    fg="white",
    insertbackground="white",
    relief="flat"
)
message_entry.pack(
    side="left",
    fill="x",
    expand=True,
    ipady=10,
    padx=(0, 8)
)

message_entry.bind("<Return>", send_message)

send_button = tk.Button(
    input_frame,
    text="SEND",
    command=send_message,
    bg="#2878d0",
    fg="white",
    font=("Arial", 10, "bold"),
    relief="flat",
    padx=18,
    pady=9
)
send_button.pack(side="right")

# Start receiving messages in background
threading.Thread(
    target=receive_messages,
    daemon=True
).start()

root.after(100, process_queue)

root.protocol("WM_DELETE_WINDOW", close_app)
root.mainloop()