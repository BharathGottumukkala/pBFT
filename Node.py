import socket
import asyncio
import websockets
import json
import random
import threading
import time
import argparse
import re
import os

# Custom imports
import communication
import sign
import messaging


class Node(object):
	"""docstring for Node"""
	def __init__(self, port, IsPrimary=False):
		self.NodeId = None     
		# self.NodeIPAddr = socket.gethostbyname(socket.gethostname())
		self.NodeIPAddr = re.search(re.compile(r'(?<=inet )(.*)(?=\/)', re.M), os.popen('ip addr show wlp3s0').read()).groups()[0] 
		# print(self.NodeIPAddr)
		# self.NameSchedulerURI = "ws://" + self.NodeIPAddr + ':' + '8765'
		self.NameSchedulerURI = "ws://localhost:8765"
		self.ListOfNodes = []
		self.port = port
		self.IsPrimary = IsPrimary
		self.Uri = "ws://" + self.NodeIPAddr + ':' + str(self.port)
		self.ListOfNodes = []

		self.public_key, self.private_key = sign.GenerateKeys(2048)

	def register(self, message):
		del message['type']
		self.ListOfNodes.append(message)


	async def HandshakeRoutine(self, uri):
		async with websockets.connect(uri) as websocket:
			if self.NodeId is not None:
				print(f"My Id is {self.NodeId}")
			else:
				message = {'type': 'handshake', 
							'IpAddr': self.NodeIPAddr, 
							'port': self.port,
							'Uri': self.Uri,
							'primary': self.IsPrimary,
							'public_key': self.public_key.exportKey('PEM').decode('utf-8')}
				message = json.dumps(message)

				await websocket.send(message)
				recv = await websocket.recv()
				recv = json.loads(recv)
				self.NodeId =recv['id']
				# print(self.NodeId)
				self.ListOfNodes = recv['LoN']
				# print(self.NodeId, self.ListOfNodes)


	async def RunRoutine(self, websocket, path):
		async for message in websocket:
			message = json.loads(message)
			if message['type'].upper() == 'NEWNODE':
				print(f"Id {message['id']} joined the network -> {self.NodeId}")
				self.register(message)

			if message['type'].upper() == 'REQUEST':
				print("Client sent a request!!")
				print(f"Am I primary: {self.IsPrimary}")


	def HandShake(self, uri):
		loop = asyncio.new_event_loop()
		asyncio.set_event_loop(loop)
		future = asyncio.ensure_future(self.HandshakeRoutine(uri)) # tasks to do
		loop.run_until_complete(future)


	def run(self):
		if self.NodeId is None:
			# print("Id not established")
			self.HandShake(self.NameSchedulerURI)

		# MultiCastServer definition is in communication.py
		t1 = threading.Thread(target=communication.MulticastServer, args=('224.1.1.1', 8766, self))
		t1.start()

		asyncio.get_event_loop().run_until_complete(
		websockets.serve(self.RunRoutine, self.NodeIPAddr, port=self.port, close_timeout=10000))
		asyncio.get_event_loop().run_forever()

		t1.join()



if __name__ == '__main__':
	parser = argparse.ArgumentParser(description="My parser")
	feature_parser = parser.add_mutually_exclusive_group(required=False)
	feature_parser.add_argument('--primary', dest='feature', action='store_true')
	feature_parser.add_argument('--secondary', dest='feature', action='store_false')
	parser.set_defaults(feature=False)
	args = parser.parse_args()
	print(args.feature)

	port = random.randint(2000, 8000)
	print(port)
	node = Node(port, args.feature)
		
	node.run()
