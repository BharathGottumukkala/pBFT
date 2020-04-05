import socketio
import time

def Report(server, handle, message):
	try:
		sio = socketio.Client()
		sio.connect(server)
		print('my sid is', sio.sid)
		sio.emit(handle, message)
		time.sleep(0.5)
		sio.disconnect()
	except Exception as e:
		print('Trying to update client again')
		time.sleep(0.2)
		Report(server, handle, message)
	


if __name__ == '__main__':
	Report('http://0.0.0.0:5000', 'clients', {'total_clients': 1})

# @sio.event
# def message(data):
#     print('I received a message!')

# @sio.on('my message')
# def my_message(data):
# 	print('I receievd')
# 	print(data)