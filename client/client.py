import socket
import yaml
import os
import shutil

from cryptography.fernet import Fernet

with open('config.yml', 'r') as file:
	config = yaml.safe_load(file)

if config['encryption']['enabled']:
	fernet = Fernet(config['encryption']['key'].encode())

if config['autoconnect']['enabled']:
	host = config['autoconnect']['host']
	port = config['autoconnect']['port']
else:
	host = input('Host: ')
	port = input('Port: ')

client = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
client.connect((host,port))

print(f'Connected to server {host}:{port}.')

while True:
	cmd = input('> ')
	data = cmd.encode()
	if fernet: data = fernet.encrypt(data)
	client.send(data)
	if cmd.lower().startswith('tree'):
		response = client.recv(1024)
		if fernet: response = fernet.decrypt(response)
		response = response.decode()
		print(response)
	elif cmd.lower().startswith('clone'):
		fbytes = b''
		print('Downloading server storage data...')
		while fbytes[-5:] != b'<END>':
			data = client.recv(1024)
			fbytes += data

		print('Decoding data...')
		fbytes = fbytes.removesuffix(b'<END>')
		if fernet: fbytes = fernet.decrypt(fbytes)
		file_tree = eval(f'{fbytes.decode()}')

		def empty_dir(path):
			for item in os.listdir(path):
				item_path = os.path.join(path,item)
				if os.path.isfile(item_path):
					os.remove(item_path)
				else:
					empty_dir(item_path)
					os.rmdir(item_path)
		empty_dir(config['storage'])

		print('Writing data to client storage...')

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

		recursive_write_tree(file_tree,config['storage'])
		print('Done!')
	elif cmd.lower().startswith('push'):
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

		filetree = recursive_loop_dir(config['storage'])
		result = str(filetree).encode()
		if fernet: result = fernet.encrypt(result)
		client.sendall(result)
		client.send(b'<END>')