from flask import Flask, render_template, request
from flask_socketio import SocketIO, join_room, emit, send
import asyncio
from multiprocessing import Process
import time
import json
import re
import os
import socket
import threading

from cluster import Cluster
import communication
import messaging
import sign
from config import config
# import timeout


# initialize Flask
app = Flask(__name__)
socketio = SocketIO(app)

ROOMS = {} # dict to track active rooms

MULTICAST_SERVER_IP = '224.1.1.1'
MULTICAST_SERVER_PORT = 8766

port = 4003
MaxNodes = 19

ConnectedClients = {}
reply = {}
view_change = {}
primary = None
n = 0
view = 0

nodes_info = {'available': 0, 'faulty': 0,
				'allocated': 0}

public, private = sign.GenerateKeys(2048)
public, private = public.exportKey('PEM'), private.exportKey('PEM')

mode = "Emulab"

# recieve_reply = False


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

# NameSchedulerURI = config().GetAddress('NameScheduler')
# communication.UpdateNodeDetails("ws://" + NameSchedulerURI + ":8765")


def NumberOfAllocated(ConnectedClients):
	count = 0
	for key, value in ConnectedClients.items():
		if value['allocate']:
			count += 1

	return count

def Allocate(size, nodes_info):
	print(f"Received Allocate request for {size} nodes")
	for i in range(size):
		t1 = threading.Thread(target=communication.SendMsg, args=(ConnectedClients[str(i)]['Uri'], {'type': "Allocate", 'total': size}))
		t1.start()
		ConnectedClients[str(i)]['allocate'] = True
		# communication.SendMsg(ConnectedClients[str(i)]['Uri'], {'type': "Allocate"})
		socketio.emit('allocated', {'total': str(i+1)})
	nodes_info['allocated'] = NumberOfAllocated(ConnectedClients)
	return nodes_info
		# socketio.emit('allocated', {'total': str(i+1)})
		# socketio.emit('status', {'id': i, 'status': 'allocated'})
		# time.sleep(0.2)

def DeAllocate(size, nodes_info):
	print(f"Received DeAllocate request for {size} nodes")
	for i in range(size):
		t1 = threading.Thread(target=communication.SendMsg, args=(ConnectedClients[str(nodes_info['allocated']-i-1)]['Uri'], {'type': "DeAllocate", 'total': nodes_info['allocated']-size }))
		t1.start()
		ConnectedClients[str(nodes_info['allocated']-i-1)]['allocate'] = False
		# communication.SendMsg(ConnectedClients[str(nodes_info['allocated'] - i - 1)]['Uri'], {'type': "DeAllocate"})
		socketio.emit('allocated', {'total': str(nodes_info['allocated'] - i -1)})
		socketio.emit('status', {'id': str(nodes_info['allocated'] - i -1), 'status': 'allocated'})
		# nodes_info['allocated'] -= 1
	nodes_info['allocated'] = NumberOfAllocated(ConnectedClients)



@app.route('/', methods=['GET', 'POST'])
def index():
	return render_template('index.html', nodes_info=nodes_info)
    


@app.route('/request_client', methods=['POST'])
def interactive():
	data = request.json
	num1 = data['n1']
	num2 = data['n2']
	oper = 'add'

	# Primary = ConnectedClients[0]
	# primary = Primary(ConnectedClients)
	print(ConnectedClients)
	primary = ConnectedClients[str(view % nodes_info['allocated'])]['Uri']
	# print(ConnectedClients)
	print(primary)
	# socketio.emit

	message = {"o": oper,"args": {"num1": num1, "num2": num2}, "t": int(time.time()), "c": 1234567}
	message = messaging.jwt(json=message, header={"alg": "RSA"}, key=private)
	token = message.get_token()
	t1 = threading.Thread(target=communication.SendMsg, args=(primary, json.dumps({'token': token, 'type': 'Request'})))
	t1.start()

	print(reply)
	t2 = threading.Thread(target=communication.Timeout, args=(5, 'client', token, reply, ConnectedClients))
	t2.start()
	# communication.Timeout(10, 'client', message, reply)
	# communication.SendMsg(primary, json.dumps({'token': message, 'type': 'Request'}))
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
		nodes_info = Allocate(min(int(data['nodes']), nodes_info['available']), nodes_info)
		n = nodes_info['allocated']
	print(nodes_info, data)


@socketio.on('deallocate')
def on_deallocate(data):
	global nodes_info, n
	print(data, n)
	if mode == "Emulab":
		DeAllocate(min(int(data['nodes']), nodes_info['allocated']), nodes_info)
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
	print(IpAddr)
	message = {'type': 'Client', 'client_id': 1234567890, 'public_key': public.decode('utf-8'), 'Uri': 'http://'+IpAddr+':'+str(port) }
	socketio.emit('clients', {'number': data['total_clients']})
	print("Socket Emitted")
	# time.sleep(1)
	print("Sending msg")
	t1 = threading.Thread(target=communication.SendMsg, args=(data['clients_info']['Uri'], message))
	t1.start()
	# communication.SendMsg(data['clients_info']['Uri'], message)
	print("Sent msg")
	# socketio.emit('log', {'no_clients': len(ConnectedClients), 'recv_client_info': ConnectedClients})

@socketio.on('check_clients')
def on_log(data):
	print("\n"*4)
	print("con Clients= ", ConnectedClients)
	print("\n"*4)

@socketio.on('reply')
def on_reply(data):
	global reply, view
	print(data)
	jwt = messaging.jwt()
	token = jwt.get_payload(data['token'])
	print(token)
	if token['t'] in reply:
		if token['r'] == reply[token['t']]['r']:
			reply[token['t']]['count'] += 1
	else:
		reply[token['t']] = {'r': token['r'], 'count': 0, 'view': token['v']}

	print(f"Count = {reply[token['t']]['count']}")
	if reply[token['t']]['count'] >= (len(ConnectedClients)//3) + 1:
		view = reply[token['t']]['view']
		print("Socket emiting. view:", view)
		socketio.emit('Reply', {'reply': reply[token['t']]['r'] })
		print("Socket emited. view:", view)


@socketio.on('status')
def on_status(data):
	global view, view_change
	print("In status")
	print(f'status received {data}')
	# if data['view'] != view:
	# 	if data['view'] not in view_change:
	# 		view_change[data['view']] = 1
	# 	else:
	# 		view_change[data['view']] += 1
	# 		if view_change[data['view']] >= (len(ConnectedClients)//3) + 1:
	# 			view = data['view']
	# 			view_change = {}
	socketio.emit('status', data)


@socketio.on('faults')
def on_faults(data):
	print(f"Fault update received for Node {data['id']}")
	data['type'] = "ModifyFault"
	t1 = threading.Thread(target=communication.SendMsg, args=(ConnectedClients[data['id']]['Uri'], data))
	t1.start()


@socketio.on('debug')
def on_debug(data):
	if not 'view' in data:
		print(f"Debug Node {data['id']}")
		data['type'] = "Debug"
		t1 = threading.Thread(target=communication.SendMsg, args=(ConnectedClients[data['id']]['Uri'], data))
		t1.start()

	else:
		socketio.emit('debug', data)

@socketio.on('ForceViewChange')
def on_forced_view_change(data):
	print("Forced View  Change Initiated")
	communication.Multicast(MULTICAST_SERVER_IP, MULTICAST_SERVER_PORT, {'type': 'Force-View-Change'})





# @socketio.on('view-change')
# def on_view_change(data):
# 	global view_change, view
# 	jwt = messaging.jwt()
# 	payload = jwt.get_payload(data)

# 	#verify
# 	if True: #change to verification
# 		view_in_consideration = int(payload['v'])
# 		if view_in_consideration not in view_change:
# 			view_change[view_in_consideration] = 1
# 		else:
# 			view_change[view_in_consideration] += 1
# 			if view_change[view_in_consideration] >= (len(ConnectedClients)//3) + 1:
# 				view = int(view_in_consideration)
# 				print("BEWARE! CLIENT GOING INTO VIEW", view)				
# 				view_change = {}


if __name__ == '__main__':
    socketio.run(app, '0.0.0.0', port, debug=True)

