import random
import Node
import asyncio
import websockets
import json
import threading
import socket
import struct
from utils import boolean

#for quicker testing
import argparse
parser = argparse.ArgumentParser(description='To get same results without a lot of effort.')
parser.add_argument('--OPTIMIZE', type=boolean, help='Do NOT use this for the final result', default=False)
args = parser.parse_args()

from communication import *
from report import Report
import sign
from config import config


class NameScheduler(object):
	"""docstring for NameScheduler"""
	def __init__(self):
		self.MaxNodes = 100
		# Ids start from 1 till MaxNodes
		self.ListOfIds = [str(i) for i in range(self.MaxNodes)]
		self.ConnectedClients = {}
		config().UpdateAddress('NameScheduler', GetLocalIp())

		# self.Uri = 'ws://localhost:8765'
		self.node = Node.Node(8765)
		self.node.NodeId = -1
		self.flag = True

	def register(self, id, IpAddr, port, uri, allocate, public_key, private_key):
		self.ConnectedClients[id] = {	'IpAddr': IpAddr, 
										'port': port,
										'Uri': uri,
										'allocate': allocate,
										'public_key': public_key,
										'private_key': private_key} 

	def generateId(self, IpAddr, port, uri, allocate):
		# id_ = random.choice(self.ListOfIds)
		id_ = self.ListOfIds[0]
		if args.OPTIMIZE:
			import pickle
			print("Unpickling keys for id:", id_)
			pub = pickle.load(open("keys/pub{}.pickle".format(id_), 'rb'))
			priv = pickle.load(open("keys/priv{}.pickle".format(id_), 'rb'))
		else:
			pub, priv = sign.GenerateKeys(2048)
			pub, priv = pub.exportKey('PEM').decode('utf-8'), priv.exportKey('PEM').decode('utf-8')
		self.ListOfIds.remove(id_)
		self.register(id_, IpAddr, port, uri, allocate, pub, priv)
		return id_, pub

	# Update Broadcast

	# async def BroadCastNewNode(self, message, msg):
	# 	for _, client in self.ConnectedClients.items():
	# 		if client['IpAddr'] != message['IpAddr'] or client['port'] != message['port']:
	# 			await SendMsgRoutine(client['Uri'], msg)

	async def IdRoutine(self, websocket, path):
		async for message in websocket:
			# server = 'http://0.0.0.0:4003/'
			server = 'http://' + config().GetAddress('client') + ":4003/"
			message = json.loads(message)
			if message['type'].upper() == 'HANDSHAKE':
				# if self.flag:
				# 	reply = Report(server, 'new_client')

				exists = False
				client = [(i,x) for i,x in self.ConnectedClients.items() if x['IpAddr']==message['IpAddr'] and x['port']==message['port']]
				# print("GODDAMN", client)
				if len(client):
					client = client[0]
					exists = True
					msg = {'id': client[0], 'LoN': self.ConnectedClients}
					msg = json.dumps(msg)
					await websocket.send(msg)
					# server = 'http:/' + node.NodeIPAddr + ':5000'


				if not exists:
					client_id ,client_pub = self.generateId(message['IpAddr'], message['port'], message['Uri'], message['allocate'])
					print("New Client {}:{} added with ID = {}".format(message['IpAddr'], message['port'], client_id))	
					a = {'id': client_id, 'LoN': self.ConnectedClients}
					# print(self.ConnectedClients)
					try:
						a = json.dumps(a)
					except TypeError as e:
						print('Cleaning Client data')
						for client in self.ConnectedClients:
							if 'websocket' in client:
								del client['websocket']
						a = json.dumps(a)
					await websocket.send(a)
					del self.ConnectedClients[client_id]['private_key']

					msg = {'type': 'NewNode', 'id': client_id, 'Uri': message['Uri'], 'info': self.ConnectedClients[client_id]}

					
					m = {'total_clients': len(self.ConnectedClients), 'id': client_id, 'clients_info': self.ConnectedClients[client_id]}
					# print(m)
					Report(server, 'client', m)

					# if len(self.ConnectedClients) > 2:
					# 	Report(server, 'check_clients', {'lol':'lol'})
					# await self.BroadCastNewNode(message, msg)
					# await BroadCast(message['IpAddr'], message['port'], self.ConnectedClients, msg)
					Multicast('224.1.1.1', 8766, msg)
					
			if message['type'].upper() == 'UPDATEDETAILS':
				if len(self.ConnectedClients):
					print("Updating Details of Nodes")
					for key, value in self.ConnectedClients.items():
						m = {'total_clients': int(key)+1, 'id': key, 'clients_info': value}
						Report(server, 'client', m)

	def SocketServer(self):
		MulticastServer('224.1.1.1', 8766, self.node)


	def Id_websocket(self):
		asyncio.get_event_loop().run_until_complete(websockets.serve(self.IdRoutine, port=8765, close_timeout=10000))
		asyncio.get_event_loop().run_forever()

	def Id(self):
		# t1 = threading.Thread(target=self.Id_websocket)
		t2 = threading.Thread(target=self.SocketServer)
		# print('a')
		# t1.start()
		t2.start()
		# print('b')
		self.Id_websocket()
		# t1.join()
		t2.join()
		# print('c')




if __name__ == '__main__':
	ns = NameScheduler()
	ns.Id()
