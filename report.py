import socketio
import time

sio = socketio.Client()

def Report(server, handle, message):
	try:
		sio.connect(server)
	except ValueError as e:
		pass
	print('my sid is', sio.sid)
	sio.emit(handle, message)
	time.sleep(1)
	sio.disconnect()


if __name__ == '__main__':
	Report('http://0.0.0.0:5000', 'clients', {'total_clients': 1})

# @sio.event
# def message(data):
#     print('I received a message!')

# @sio.on('my message')
# def my_message(data):
# 	print('I receievd')
# 	print(data)