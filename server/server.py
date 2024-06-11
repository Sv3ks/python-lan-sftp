import socket
import threading

from client_handler import ClientHandler

host = 'localhost'
port = 9450

server = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
server.bind((host,port))
server.listen()
print(f'Server is now open on {host}:{port}.')

while True:
	print('Server is now listening...')
	client = ClientHandler(server.accept())
	print(f'Accepted client {client.addr[0]}:{client.addr[1]}.')
	thread = threading.Thread(target=client.Handle)
	thread.start()