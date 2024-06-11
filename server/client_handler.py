import socket
import os

class ClientHandler:
	def __init__(self,client: tuple[socket.socket,tuple[str,str]]) -> None:
		self.conn = client[0]
		self.addr = client[1]
	def Tree(self):
		tree = ''
		for root, dirs, files in os.walk('.'):
			level = root.replace('.', '').count(os.sep)
			indent = ' ' * 3 * (level) + '└─'
			tree += f'{indent}{os.path.basename(root)}/\n'
			subindent = ' ' * 3 * (level + 1) + '└─'
			for f in files:
				tree += f'{subindent}{f}\n'

		self.conn.send(str(tree).encode())
	def Get(self,par):
		f = open(par,'rb')
		bytes = f.read()
		self.conn.send(str(os.path.basename(par)).encode())
		self.conn.send(str(os.path.getsize(par)).encode())
		self.conn.sendall(bytes)
		self.conn.send(b'<END>')
		f.close()
	def Handle(self):
		while True:
			try:
				task = self.conn.recv(1024).decode()
			except Exception as e:
				print(f'Lost connection to client {self.addr[0]}:{self.addr[1]}.')
				return
			
			print(f'Received task: {task}')

			cmd = task.split(' ')[0]
			par = task.split(' ')
			par.remove(cmd)
			par = ' '.join(par)

			match cmd:
				case 'tree':
					self.Tree()
				case 'get':
					self.Get(par)