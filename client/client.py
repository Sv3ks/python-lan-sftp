import socket
import yaml
import os

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

		print('Writing data to client storage...')
		#os.rmdir(config['storage'])

		def recursive_write_tree(tree: dict,full_path):
			for name, item in tree.items():
				file_path = os.path.join(full_path,name)
				print(f'Writing {name} to {file_path}')
				if type(item) is bytes:
					f = open(file_path,'wb')
					f.write(item)
					f.close()
				elif type(item) is dict:
					os.makedirs(file_path)
					recursive_write_tree(item,file_path)
		print(file_tree)
		recursive_write_tree(file_tree,config['storage'])
		print('Done!')

	elif cmd.lower().startswith('get'):
		print('Getting file information...')
		name = client.recv(1024)
		if fernet: name = fernet.decrypt(name)
		name = name.decode()

		size = client.recv(1024)
		if fernet: size = fernet.decrypt(size)
		size = size.decode()

		file = open(f'{config['storage'].removesuffix('/')}/{name}','wb')
		fbytes = b''

		print('Getting file data...')
		progress = 0
		print(f'\r{progress}/{size}',end='')
		while fbytes[-5:] != b'<END>':
			data = client.recv(1024)
			fbytes += data
			progress += 1024
			print(f'\r{progress}/{size}',end='')
		
		print(f'\r{size}/{size}',end='\n')

		fbytes = fbytes.removesuffix(b'<END>')
		if fernet: fbytes = fernet.decrypt(fbytes)

		print('Writing file...')
		file.write(fbytes)
		file.close()
		print('Done!')