import socket
import os
import yaml

from cryptography.fernet import Fernet

class ClientHandler:
	def __init__(self,client: tuple[socket.socket,tuple[str,str]]) -> None:
		with open('config.yml', 'r') as file:
			self.config = yaml.safe_load(file)
		if self.config['encryption']['enabled']:
			self.fernet = Fernet(self.config['encryption']['key'].encode())
		self.conn = client[0]
		self.addr = client[1]
	def Tree(self,path):
		tree = ''
		for root, dirs, files in os.walk(path):
			level = root.replace('.', '').count(os.sep)
			indent = ' ' * 3 * (level) + '└─'
			tree += f'{indent}{os.path.basename(root)}/\n'
			subindent = ' ' * 3 * (level + 1) + '└─'
			for f in files:
				tree += f'{subindent}{f}\n'

		tree = tree.encode()
		if self.fernet: tree = self.fernet.encrypt(tree)
		self.conn.send(tree)
	def Get(self,path: str):
		f = open(path,'rb')

		name = str(os.path.basename(path)).encode()
		if self.fernet: name = self.fernet.encrypt(name)
		self.conn.send(name)

		size = str(os.path.getsize(path)).encode()
		if self.fernet: size = self.fernet.encrypt(size)
		self.conn.send(size)

		bytes = f.read()
		if self.fernet: bytes = self.fernet.encrypt(bytes)
		self.conn.sendall(bytes)

		self.conn.send(b'<END>')
		f.close()
	def Clone(self):
		def recursive_loop_dir(path):
			result = {}
			for item in os.listdir(path):
				item_path = os.path.join(path,item)
				if os.path.isfile(item_path):
					f = open(item_path,'rb')
					result[item] = f.read()
					f.close()
				elif os.path.isdir(item_path):
					result[item] = recursive_loop_dir(item_path)
			return result

		filetree = recursive_loop_dir(self.config['storage'])
		result = str(filetree).encode()
		if self.fernet: result = self.fernet.encrypt(result)
		self.conn.sendall(result)
		self.conn.send(b'<END>')
	def Handle(self):
		while True:
			try:
				task = self.conn.recv(1024)
				if self.fernet: task = self.fernet.decrypt(task)
				task = task.decode()
			except Exception as e:
				print(f'Lost connection to client {self.addr[0]}:{self.addr[1]}.')
				return
			
			print(f'Received task: {task}')

			cmd = task.split(' ')[0]
			par = task.split(' ')
			par.remove(cmd)

			match cmd:
				case 'tree':
					self.Tree(self.config['storage'])
				case 'get':
					self.Get(f'{self.config['storage'].removesuffix('/')}/{par[0].replace('/',' ')}')
				case 'clone':
					self.Clone()