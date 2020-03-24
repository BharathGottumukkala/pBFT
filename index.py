# from flask import Flask
# import asyncio
# import websockets
# import json

# app = Flask(__name__)


# @app.route("/index")
# def hello():
# 	return "Hello World"


# # @app.route("/")
# async def connect_routine():
# 	uri = "ws://localhost:8765"
# 	async with websockets.connect(uri) as websocket:
# 		message = {'type': 'handshake', 
# 					'IpAddr': '127.0.0.1', 
# 					'port': 8000,
# 					'Uri': "Mydick"}
# 		message = json.dumps(message)
# 		await websocket.send(message)
# 		id_ = await websocket.recv()
# 		print(id_)
# 		print()
# 		return str(id_)

# @app.route("/")
# def connect():
# 	loop = asyncio.new_event_loop()
# 	asyncio.set_event_loop(loop)
# 	future = asyncio.ensure_future(connect_routine()) # tasks to do
# 	id_ = loop.run_until_complete(future)
# 	return str(id_)

# if __name__ == '__main__':
# 	app.run("0.0.0.0", 1234, debug=True)

from flask import Flask, render_template, request
from flask_socketio import SocketIO, join_room, emit, send
import asyncio
from multiprocessing import Process
import time

from cluster import Cluster
import communication
import messaging
import sign as s

# initialize Flask
app = Flask(__name__)
socketio = SocketIO(app)
primary = False
ROOMS = {} # dict to track active rooms

ConnectedClients = []
primary = None

public, private = s.GenerateKeys(2048)
public, private = public.exportKey('PEM'), private.exportKey('PEM')


def Primary(ConnectedClients):
	for Client in ConnectedClients:
		if Client['primary']:
			return Client['Uri']

@app.route('/', methods=['GET', 'POST'])
def index():
    
	if request.method == 'GET':
		return render_template('home.html')
	if request.method == 'POST':

		print(request.form.get('nodes'))
		return render_template('index.html')


@app.route('/request_client', methods=['POST'])
def interactive():
	data = request.values
	num1 = data['n1']
	num2 = data['n2']
	oper = 'add'

	# Primary = ConnectedClients[0]
	primary = Primary(ConnectedClients)
	print(primary)
	# socketio.emit

	message = {"op": oper,"args": {"num1": num1, "num2": num2}, "public_key": public.decode('utf-8	')}
	message = messaging.jwt(json=message, header={"alg": "RSA","typ": "Request", "timestamp": int(time.time())}, key=private)
	message = message.get_token()
	reply = communication.SendMsg(primary, message)
	# reply = await SendMsg(primary['Uri'], message)
	# return render_template('interactive.html')
	# return 'reply'

@socketio.on('create')
def on_create(data):
	# emit('join_room', {'room': "gaand"})
	print(data)
	if len(ConnectedClients):
		primary = False
	primary = True
	p = Process(target=Cluster, args=(int(data['nodes']), primary))
	p.start()
	# Cluster(data['nodes'])

@socketio.on('client')
def on_connect(data):
	print('connect initialized')
	# print(data['clients_info'])
	ConnectedClients.append(data['clients_info'])
	primary = ConnectedClients[0]

	# message = {'type': 'Request', 'num1': 1, 'num2': 2}
	# reply = SendMsg_reg(primary['Uri'], message)
	socketio.emit('clients', {'number': data['total_clients']})
	# socketio.emit('log', {'no_clients': len(ConnectedClients), 'recv_client_info': ConnectedClients})

@socketio.on('check_clients')
def on_log(data):
	print("\n"*4)
	print("con Clients= ", ConnectedClients)
	print("\n"*4)

if __name__ == '__main__':
    socketio.run(app, '0.0.0.0', 5000, debug=True)