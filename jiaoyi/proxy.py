#!/usr/bin/env python3
"""简单的端口转发：80 -> 5000"""
import socket
import threading

def forward(source, dest):
    try:
        while True:
            data = source.recv(4096)
            if not data:
                break
            dest.sendall(data)
    except:
        pass
    finally:
        source.close()
        dest.close()

def handle(client, addr):
    try:
        server = socket.create_connection(('127.0.0.1', 5000), timeout=5)
        t1 = threading.Thread(target=forward, args=(client, server))
        t2 = threading.Thread(target=forward, args=(server, client))
        t1.daemon = True
        t2.daemon = True
        t1.start()
        t2.start()
    except Exception as e:
        print(f"连接错误: {e}")
        client.close()

s = socket.socket(socket.AF_INET, socket.SO_REUSEADDR, 0)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(('0.0.0.0', 80))
s.listen(100)
print("端口转发: 80 -> 5000")

while True:
    client, addr = s.accept()
    threading.Thread(target=handle, args=(client, addr), daemon=True).start()
