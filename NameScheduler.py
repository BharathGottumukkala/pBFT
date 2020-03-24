import random
import Node
import asyncio
import websockets
import json
import threading
import socket
import struct

from communication import *
from report import Report

class NameScheduler(object):
	"""docstring for NameScheduler"""
	def __init__(self):
		self.MaxNodes = 100
		# Ids start from 1 till MaxNodes
		self.ListOfIds = [str(i+1) for i in range(self.MaxNodes)]
		self.ConnectedClients = []
		# self.Uri = 'ws://localhost:8765'
		self.node = Node.Node(8765)
		self.node.NodeId = 0

	def register(self, id, IpAddr, port, uri, primary, public_key):
		self.ConnectedClients.append({	'id': id, 
										'IpAddr': IpAddr, 
										'port': port,
										'Uri': uri,
										'primary': primary,
										'public_key': public_key}) 

	def generateId(self, IpAddr, port, uri, primary, public_key):
		id_ = random.choice(self.ListOfIds)
		self.ListOfIds.remove(id_)
		self.register(id_, IpAddr, port, uri, primary, public_key)
		return id_

	async def BroadCastNewNode(self, message, msg):
		for client in self.ConnectedClients:
			if client['IpAddr'] != message['IpAddr'] or client['port'] != message['port']:
				await SendMsgRoutine(client['Uri'], msg)

	async def IdRoutine(self, websocket, path):
		async for message in websocket:
			message = json.loads(message)
			if message['type'].upper() == 'HANDSHAKE':
				exists = False
				client = [x for i,x in enumerate(self.ConnectedClients) if x['IpAddr']==message['IpAddr'] and x['port']==message['port']]
				# print("GODDAMN", client)
				if len(client):
					client = client[0]
					exists = True
					msg = {'id': client['id'], 'LoN': self.ConnectedClients}
					msg = json.dumps(msg)
					await websocket.send(msg)
					# server = 'http:/' + node.NodeIPAddr + ':5000'


				if not exists:
					client_id = self.generateId(message['IpAddr'], message['port'], message['Uri'], message['primary'], message['public_key'])
					print("New Client {}:{} added with ID = {}".format(message['IpAddr'], message['port'], client_id))	
					a = {'id': client_id, 'LoN': self.ConnectedClients}
					print(self.ConnectedClients)
					try:
						a = json.dumps(a)
					except TypeError as e:
						print('Cleaning Client data')
						for client in self.ConnectedClients:
							if 'websocket' in client:
								del client['websocket']
						a = json.dumps(a)
					await websocket.send(a)
					msg = {'type': 'NewNode', 'id': client_id, 'Uri': message['Uri']}

					server = 'http://0.0.0.0:5000'
					m = {'total_clients': len(self.ConnectedClients), 'clients_info': self.ConnectedClients[-1]}
					Report(server, 'client', m)
					# if len(self.ConnectedClients) > 2:
					# 	Report(server, 'check_clients', {'lol':'lol'})
					# await self.BroadCastNewNode(message, msg)
					# await BroadCast(message['IpAddr'], message['port'], self.ConnectedClients, msg)
					Multicast('224.1.1.1', 8766, msg)
					

	def SocketServer(self):
		MulticastServer('224.1.1.1', 8766, self.node)


	def Id_websocket(self):
		asyncio.get_event_loop().run_until_complete(
		    websockets.serve(self.IdRoutine, port=8765, close_timeout=10000))
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
