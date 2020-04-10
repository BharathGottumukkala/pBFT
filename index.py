from flask import Flask, render_template, request
from flask_socketio import SocketIO, join_room, emit, send
import asyncio
from multiprocessing import Process
import time
import json
import re
import os

from cluster import Cluster
import communication
import messaging
import sign

# initialize Flask
app = Flask(__name__)
socketio = SocketIO(app)

#server info
ConnectedClients = {}
port = 4003
reply = {}

# client info
view = 0
client_id = 45023
client_public_key, client_private_key = sign.GenerateKeys(2048)
client_public_key, client_private_key = client_public_key.exportKey(
	'PEM'), client_private_key.exportKey('PEM')


# def Primary(ConnectedClients):
# 	for Client in ConnectedClients.values():
# 		if Client['primary']:
# 			return Client['Uri']

@app.route('/', methods=['GET', 'POST'])
def index():
	global ConnectedClients
	if request.method == 'GET':
		return render_template('home.html')
	if request.method == 'POST':
		nodes = request.form.get('nodes')
		faulty_nodes = request.form.get('faulty_nodes')
		print("nodes: {}, faulty_nodes: {}".format(nodes, faulty_nodes))
		#create nodes
		ConnectedClients = Cluster(
								size=int(nodes), 
								client_port=port, 
								client_uri='http://127.0.0.1:' +str(port), 
								client_public_key=client_public_key)
		return render_template('index.html')


@app.route('/request_client', methods=['POST'])
def interactive():
	data = request.values
	num1 = data['n1']
	num2 = data['n2']
	oper = 'add'

	# Primary = ConnectedClients[0]
	print(ConnectedClients)
	# import time
	# time.sleep(5)
	primary = ConnectedClients[view % len(ConnectedClients)]
	# print(ConnectedClients)
	print()
	print("Primary URI", primary['Uri'])
	# socketio.emit
	message = {"o": oper,"args": {"num1": num1, "num2": num2}, "t": int(time.time()), "c": 1234567}
	message = messaging.jwt(json=message, header={"alg": "RSA"}, key=client_private_key)
	message = message.get_token()
	reply = communication.SendMsg(primary['Uri'], json.dumps({'token': message, 'type': 'Request'}))
	# reply = await SendMsg(primary['Uri'], message)
	# return render_template('interactive.html')
	return render_template('index.html', num_nodes=len(ConnectedClients))

# @socketio.on('create')
# def on_create(data):
# 	# emit('join_room', {'room': "gaand"})
# 	print("data", data)
# 	if len(ConnectedClients):
# 		primary = False
# 	primary = True
# 	p = Process(target=Cluster, args=(int(data['nodes']), primary))
# 	p.start()
	# Cluster(data['nodes'])


@socketio.on('client')
def on_connect(data):
	print('connect initialized')
	# print(data['clients_info'])
	ConnectedClients[data['id']] = data['clients_info']
	# primary = ConnectedClients[0]
	IpAddr = 'localhost'#re.search(re.compile(r'(?<=inet )(.*)(?=\/)', re.M), os.popen('ip addr show wlp3s0').read()).groups()[0] 
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
