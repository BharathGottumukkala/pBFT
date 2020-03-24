import socketio
import asyncio
import json
import time

# server = 'http://0.0.0.0:5000'
# handle = 'newnode'
# message = {'total_clients': '10485'}

sio = socketio.Client()
sio.connect('http://localhost:5000')
print('my sid is', sio.sid)
sio.emit('my message', {'foo': 'bar'})
time.sleep(0.5)
sio.disconnect()

# # def Report(server, handle, message):

# sio.connect('http://0.0.0.0:5000')
# print('my sid is', sio.sid)
# sio.emit('create', {'foo': 'bar'})
# sio.disconnect()


	# Report('http://0.0.0.0:5000', 'newnode', {'total_clients': '10485'})

# @sio.event
# def message(data):
#     print('I received a message!')

# @sio.on('my message')
# def my_message(data):
# 	print('I receievd')
# 	print(data)