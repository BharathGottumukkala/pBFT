"""
Flask ka websockets is handled by socketio.

So in order to report we have to send a msg using socketio Client

"""


import socketio
import time
from config import config


def Report(server, handle, message):
	try:
		sio = socketio.Client()
		sio.connect(server)
		# print('my sid is', sio.sid)
		sio.emit(handle, message)
		time.sleep(0.5)
		sio.disconnect()
		del sio
	except Exception as e:
		print(e)
		time.sleep(0.5)
		server = 'http://' + config().GetAddress('client') + ":4003/"
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