import socket
import os
import shutil
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
	def Push(self):
		fbytes = b''

		while fbytes[-5:] != b'<END>':
			data = self.conn.recv(1024)
			fbytes += data
		
		fbytes = fbytes.removesuffix(b'<END>')
		if self.fernet: fbytes = self.fernet.decrypt(fbytes)
		file_tree = eval(f'{fbytes.decode()}')

		def empty_dir(path):
			for item in os.listdir(path):
				item_path = os.path.join(path,item)
				if os.path.isfile(item_path):
					os.remove(item_path)
				else:
					empty_dir(item_path)
					os.rmdir(item_path)
		empty_dir(self.config['storage'])

		def recursive_write_tree(tree: dict,full_path):
			for name, item in tree.items():
				file_path = os.path.join(full_path,name)
				print(f'-> Writing {name} to {file_path}')
				if type(item) is bytes:
					f = open(file_path,'wb')
					f.write(item)
					f.close()
				elif type(item) is dict:
					os.makedirs(file_path)
					recursive_write_tree(item,file_path)

		recursive_write_tree(file_tree,self.config['storage'])
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
			par = ' '.join(par)

			match cmd:
				case 'tree':
					self.Tree(self.config['storage'])
				case 'clone':
					self.Clone()
				case 'push':
					self.Push()
				case 'exec':
					os.system(par)