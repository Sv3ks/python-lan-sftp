import socket

host = 'localhost' 
port = 9450

client = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
client.connect((host,port))

print(f'Connected to server {host}:{port}.')

while True:
	cmd = input('> ')
	data = cmd.encode()
	client.send(data)
	if cmd.lower().startswith('tree'):
		response = client.recv(1024).decode()
		print(response)
	if cmd.lower().startswith('get'):
		print('Getting file information...')
		name = client.recv(1024).decode()
		size = client.recv(1024).decode()
		file = open(name,'wb')
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

		print('Writing file...')
		file.write(fbytes)
		file.close()
		print('Done!')