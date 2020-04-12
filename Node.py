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

# commuication handles Sending messages to different nodes
import communication	

# messaging defines the sent token structure and handles creation and verifiction of messages
# import messaging

# Functions to handle incoming requests
import handle_requests

# Logging 
import mlog

# Report back to client for demo purposes
import report


class Node(object):
	"""docstring for Node"""
	def __init__(self, port):
		self.NodeId = None     
		# self.NodeIPAddr = re.search(re.compile(r'(?<=inet )(.*)(?=\/)', re.M), os.popen('ip addr show enp4s0f1').read()).groups()[0] 
		self.NodeIPAddr = self.GetIp()
		print(self.NodeIPAddr)
		# self.NameSchedulerURI = "ws://" + self.NodeIPAddr + ':' + '8765'
		self.NameSchedulerURI = "ws://localhost:8765"
		self.port = port
		# Decides whether the node is primary
		# self.IsPrimary = IsPrimary
		self.Uri = "ws://" + self.NodeIPAddr + ':' + str(self.port)
		self.ListOfNodes = {}
		self.pre_prepare_msgs = 0
		self.mode = 'Sleep'
		self.view = 0
		self.count = 0
		self.log = []
		"""
		self.ListOfNodes = {'NodeID': {uska details}}
		
		self.log = ["d": digest_m, 'm': Client_msg, 'preprepare': preprepare_msg,
					"prepare":[List of received prepare msgs],
					"commit": [List od commit messages]]
		"""

	def GetIp(self):
		return (
				(
					[ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] 
					if not ip.startswith("127.")] or 
					[[(s.connect(("8.8.8.8", 53)), s.getsockname()[0], s.close()) 
						for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]]
				) 
				+ ["no IP found"]
			   )[0]

	def IsPrimary(self):
		return self.view == self.NodeId


	def register(self, message):
		# Add newnodes into ListOfNodes
		del message['type']
		self.ListOfNodes[message['id']] = message['info']


	async def HandshakeRoutine(self, uri):
		# Get an ID from the NameScheduler for future communication
		async with websockets.connect(uri) as websocket:
			if self.NodeId is not None:
				print(f"My Id is {self.NodeId}")
			else:
				message = {'type': 'handshake', 
							'IpAddr': self.NodeIPAddr, 
							'port': self.port,
							'Uri': self.Uri,
							'allocate': False
							}
				message = json.dumps(message)

				await websocket.send(message)
				recv = await websocket.recv()
				recv = json.loads(recv)
				self.NodeId =recv['id']
				self.ListOfNodes = recv['LoN']
				print(self.ListOfNodes)
				self.public_key = self.ListOfNodes[self.NodeId]['public_key'].encode('utf-8')
				self.private_key = self.ListOfNodes[self.NodeId]['private_key'].encode('utf-8')


	async def RunRoutine(self, websocket, path):
		# Defines the funcioning of each node on receiving differnet messages
		async for message in websocket:
			# message format
			# message = {'type': type, 'token': token}
			# token is generated using messaging library in handle_requests
			message = json.loads(message)
			if message['type'].upper() == 'NEWNODE':
				# When a new node is added, Register the nde's details for future communication
				print(f"Id {message['id']} joined the network -> {self.NodeId}")
				self.register(message)

			elif message['type'].upper() == 'REQUEST':
				# I am yet to implement client broadcasting the reqiest to all secondary nodes
				if self.IsPrimary():
					print(f"I am the primary with ID = {self.NodeId}")
				else:
					print(f"Well I am not the primary with ID = {self.NodeId}")
				# Verify request and returns the next message to send
				final = handle_requests.Request(message, self.client_public_key, self.view, 100, self.private_key)
				
				if final is not None:
					print(len(self.ListOfNodes))
					# Multicast the request all nodes in the network
					communication.Multicast('224.1.1.1', 8766, final)


					# await communication.BroadCast(self.NodeIPAddr, self.port, self.ListOfNodes, final)
					# BroadCast doesnot send this msg to Primary. Therefore a msg has to be sent manually
					# await communication.SendMsgRoutine(self.Uri, final)
					# Logging message from client and PrePrepare msg
					# print(f"{self.NodeId} -> Message logging...")
					# self.log.append(mlog.log(message))
					# print(f"{self.NodeId} -> Message logged")

				else:
					print(f"{self.NodeId} -> The message verification failed")

			elif message['type'].upper() == 'ALLOCATE':
				self.ListOfNodes[self.NodeId]['allocate'] = True

			elif message['type'].upper() == 'CLIENT':
				# Here the message i of different format..fck. Will update this in the next release :p
				# message = {'type': type, 'client_id': '...', 'public_key':'...', 'Uri': '...'}
				self.client_id = message['client_id']
				self.client_public_key = message['public_key'].encode('utf-8')
				self.client_uri = message['Uri']
				print(f"{self.NodeId} -> Received Client publickey")

			elif message['type'].upper() == 'PREPREPARE':
				print(f"ID = {self.NodeId}, primary={self.IsPrimary()}")
				# print(message)
				public_key_primary = self.ListOfNodes[str(self.view)]['public_key']

				# Get primary's public key to verify the signature
				# for client in self.ListOfNodes.values():
				# 	if client['primary']:
				# 		public_key_primary = client['public_key']


				# Send all the details. It will verify and return the next packet to send
				result = handle_requests.Preprepare(message, self.client_public_key, public_key_primary, self.NodeId, self.private_key, self.view)
				if result is not None:
					self.mode = 'Prepare'
					# await communication.BroadCast(self.NodeIPAddr, self.port, self.ListOfNodes, result)
					# print(f"{self.NodeId} -> PrePrepare logging...")
					self.log = mlog.log(self.log, message)
					print(f"{self.NodeId} -> PrePrepare logged")

					# print(f"{self.NodeId} -> self Prepare logging...")
					self.log = mlog.log(self.log, result)
					print(f"{self.NodeId} -> self Prepare logged")
					# await communication.BroadCast(self.NodeIPAddr, self.port, self.ListOfNodes, result)
					communication.Multicast('224.1.1.1', 8766, result)


			elif message['type'].upper() == 'PREPARE':


				# This verifies the message and returns back the body of the message as well for logging
				# Look at the initialization step for self.log definition
				verify_p, pToken = handle_requests.Prepare(message, self.ListOfNodes, self.view)
				verify_m = False
				for log in self.log:
					if pToken['d'] == log['d']:
						if 'm' in log:
							verify_m = True
				if verify_p and verify_m:
					self.log = mlog.log(self.log, message)
					cur_log = mlog.RequestLog(pToken, self.log)
					self.count = len(cur_log['prepare'])
					# print(f"{self.NodeId} -> others Prepare logged")
				print(f"Count = {self.count}, ID = {self.NodeId}")

				if self.count >= 2*len(self.ListOfNodes)//3 :
					if self.mode == 'Prepare':
						# print(f"{self.NodeId} -> CreateCommit##")
						commit = handle_requests.CreateCommit(message, self.NodeId, self.private_key)
						# await communication.BroadCast(self.NodeIPAddr, self.port, self.ListOfNodes, commit)
						communication.Multicast('224.1.1.1', 8766, commit)
						self.mode = 'Commit'
						# self.count = 0

			elif message['type'].upper() == 'COMMIT':
				verify_p, cToken = handle_requests.Prepare(message, self.ListOfNodes, self.view)
				if verify_p:
					# print(f"{self.NodeId} -> Commit logging...")
					# self.log.append(mlog.log(result))
					self.log = mlog.log(self.log, message)
					# print(f"{self.NodeId} -> Commit logged")

				cur_log = mlog.RequestLog(cToken, self.log)
				count = len(cur_log['commit'])
				if count >= 2*len(self.ListOfNodes)//3 and self.mode == 'Commit':
					print(f'LOG of {self.NodeId}')
					print('\n'*10)
					print(json.dumps(self.log))
					reply = handle_requests.CreateReply(message, self.log, self.NodeId, self.private_key)
					report.Report(self.client_uri, 'reply', reply)
					self.mode = 'Sleep'


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
	# parser = argparse.ArgumentParser(description="My parser")
	# feature_parser = parser.add_mutually_exclusive_group(required=False)
	# feature_parser.add_argument('--primary', dest='feature', action='store_true')
	# feature_parser.add_argument('--secondary', dest='feature', action='store_false')
	# parser.set_defaults(feature=False)
	# args = parser.parse_args()
	# print(args.feature)

	port = random.randint(7000, 7500)
	print(port)
	node = Node(port)
		
	node.run()
