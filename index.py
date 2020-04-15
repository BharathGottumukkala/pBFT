from flask import Flask, render_template, request
from flask_socketio import SocketIO, join_room, emit, send
import asyncio
from multiprocessing import Process
import time
import json
import re
import os
import socket
from cluster import Cluster
import communication
import messaging
import sign
from config import config

# initialize Flask
app = Flask(__name__)
socketio = SocketIO(app)

ROOMS = {} # dict to track active rooms

port = 4003
MaxNodes = 19

ConnectedClients = {}
reply = {}
primary = None
n = 0
view = 0

nodes_info = {'available': 0, 'faulty': 0,
				'allocated': 0}

public, private = sign.GenerateKeys(2048)
public, private = public.exportKey('PEM'), private.exportKey('PEM')

mode = "Emulab"


# def Primary(ConnectedClients):
# 	for Client in ConnectedClients.values():
# 		if Client['primary']:
# 			return Client['Uri']

def GetIp():
	return (
			(
				[ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] 
				if not ip.startswith("127.")] or 
				[[(s.connect(("8.8.8.8", 53)), s.getsockname()[0], s.close()) 
					for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]]
			) 
			+ ["no IP found"]
		   )[0]


IpAddr = GetIp()
config().UpdateAddress('client', IpAddr)


def Allocate(size):
	print(f"Received Allocate request for {size} nodes")
	for i in range(size):
		communication.SendMsg(ConnectedClients[str(i)]['Uri'], {'type': "Allocate"})
		socketio.emit('allocated', {'total': str(i+1)})
		# time.sleep(0.2)

def DeAllocate(size):
	print(f"Received DeAllocate request for {size} nodes")
	for i in range(size):
		communication.SendMsg(ConnectedClients[str(size - i - 1)]['Uri'], {'type': "DeAllocate"})
		nodes_info['allocated'] -= 1
		socketio.emit('allocated', {'total': str(nodes_info['allocated'])})





@app.route('/', methods=['GET', 'POST'])
def index():
	return render_template('index.html', nodes_info=nodes_info)
    
	# if request.method == 'GET':
	# 	return render_template('home.html')
	# if request.method == 'POST':

	# 	print(request.form.get('nodes'))
	# 	return render_template('index.html')

@app.route('/request_client', methods=['POST'])
def interactive():
	# data = request.values
	data = request.json
	num1 = data['n1']
	num2 = data['n2']
	oper = 'add'

	# Primary = ConnectedClients[0]
	# primary = Primary(ConnectedClients)
	print(ConnectedClients)
	primary = ConnectedClients[str(view)]['Uri']
	# print(ConnectedClients)
	print(primary)
	# socketio.emit

	message = {"o": oper,"args": {"num1": num1, "num2": num2}, "t": int(time.time()), "c": 1234567}
	message = messaging.jwt(json=message, header={"alg": "RSA"}, key=private)
	message = message.get_token()
	reply = communication.SendMsg(primary, json.dumps({'token': message, 'type': 'Request'}))
	# reply = await SendMsg(primary['Uri'], message)
	# return render_template('interactive.html')
	# return render_template('index.html', num_nodes=len(ConnectedClients))
	return "Success"

@socketio.on('create')
def on_create(data):
	print(data, n)
	if mode == "Emulab":
		Allocate(int(data['nodes']))
	else:
		# if len(ConnectedClients):
		# 	primary = False
		# primary = True
		p = Process(target=Cluster, args=(int(data['nodes']), ))
		p.start()
		# Cluster(data['nodes'])

	print(data, n)	

@socketio.on('allocate')
def on_allocate(data):
	global nodes_info, n
	print(data, n)
	if mode == "Emulab":
		Allocate(min(int(data['nodes']), nodes_info['available']))
		nodes_info['allocated'] = min(int(data['nodes']), nodes_info['available'])
		n = min(int(data['nodes']), nodes_info['available'])
	print(nodes_info, data)


@socketio.on('deallocate')
def on_deallocate(data):
	global nodes_info, n
	print(data, n)
	if mode == "Emulab":
		DeAllocate(min(int(data['nodes']), nodes_info['allocated']))
		nodes_info['allocated'] -= min(int(data['nodes']), nodes_info['allocated'])
		n -= min(int(data['nodes']), nodes_info['allocated'])
	print(nodes_info, data)

@socketio.on('client')
def on_connect(data):
	print('connect initialized')
	# print(data['clients_info'])
	ConnectedClients[data['id']] = data['clients_info']
	nodes_info['available'] = len(ConnectedClients)
	# primary = ConnectedClients[0]
	IpAddr = GetIp()
	message = {'type': 'Client', 'client_id': 1234567890, 'public_key': public.decode('utf-8'), 'Uri': 'http://'+IpAddr+':'+str(port) }
	socketio.emit('clients', {'number': data['total_clients']})
	time.sleep(1)
	reply = communication.SendMsg(data['clients_info']['Uri'], message)
	# socketio.emit('log', {'no_clients': len(ConnectedClients), 'recv_client_info': ConnectedClients})

@socketio.on('check_clients')
def on_log(data):
	print("\n"*4)
	print("con Clients= ", ConnectedClients)
	print("\n"*4)

@socketio.on('reply')
def on_reply(data):
	print(data)
	jwt = messaging.jwt()
	token = jwt.get_payload(data['token'])
	print(token)
	if token['t'] in reply:
		if token['r'] == reply[token['t']]['r']:
			reply[token['t']]['count'] += 1
	else:
		reply[token['t']] = {'r': token['r'], 'count': 0}

	print(f"Count = {reply[token['t']]['count']}")
	if reply[token['t']]['count'] >= (len(ConnectedClients)//3) + 1:
		print("Socket emiting")
		socketio.emit('Reply', {'reply': reply[token['t']]['r'] })
		print("Socket emited")


if __name__ == '__main__':
    socketio.run(app, '0.0.0.0', port, debug=True)
