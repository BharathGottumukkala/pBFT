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
	def __init__(self, node_id, private_key, nodes_info, view=0):
		self.NodeId = node_id
		self.NodeIPAddr = '127.0.0.1'
		# self.NameSchedulerURI = "ws://localhost:8765"
		self.port = nodes_info[self.NodeId]['port']
		# Decides whether the node is primary
		self.view = view
		# self.Uri = "ws://" + self.NodeIPAddr + ':' + str(self.port)
		self.ListOfNodes = nodes_info.copy()
		print(list(self.ListOfNodes.keys()))
		self.client_public_key = self.ListOfNodes['client']['public_key']
		self.client_uri = self.ListOfNodes['client']['Uri']
		del self.ListOfNodes['client']
		self.NumNodes = len(list(nodes_info.keys())) 
		self.private_key = private_key
		self.pre_prepare_msgs = 0
		self.mode = 'Sleep'
		self.log = []
		"""
		self.ListOfNodes = {'NodeID': {uska details}}
		
		self.log = ["d": digest_m, 'm': Client_msg, 'preprepare': preprepare_msg,
					"prepare":[List of received prepare msgs],
					"commit": [List od commit messages]]
		"""

	def primary_id(self):
		return self.view % self.NumNodes

	def _REQUEST(self, message):
		print("View: {}, My_ID: {}, num_nodes: {}".format(self.view, self.NodeId, self.NumNodes))
		if self.NodeId == self.primary_id():
			# Current node is primary
			print(f"I am the primary with ID = {self.NodeId}")
		else:
			# TO DO: Redirect to primary
			print(f"Well I am not the primary with ID = {self.NodeId}")

	async def RunRoutine(self, websocket, path):
		# Defines the funcioning of each node on receiving differnet messages
		async for message in websocket:
			# message format
			# message = {'type': type, 'token': token}
			# token is generated using messaging library in handle_requests
			message = json.loads(message)
			if message['type'].upper() == 'REQUEST':
				self._REQUEST(message)
				# Verify request and returns the next message to send
				print("type of private_key", type(self.private_key))
				final = handle_requests.Request(message, self.client_uri, self.view, 100, self.private_key)
				
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

			elif message['type'].upper() == 'CLIENT':
				# Here the message i of different format..fck. Will update this in the next release :p
				# message = {'type': type, 'client_id': '...', 'public_key':'...', 'Uri': '...'}
				self.client_id = message['client_id']
				self.client_public_key = message['public_key'].encode('utf-8')
				self.client_uri = message['Uri']
				print(f"{self.NodeId} -> Received Client publickey")

			elif message['type'].upper() == 'PREPREPARE':
				print(f"ID = {self.NodeId}, primary={self.IsPrimary}")
				# print(message)
				public_key_primary = None

				# Get primary's public key to verify the signature
				for client in self.ListOfNodes.values():
					if client['primary']:
						public_key_primary = client['public_key']

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


	def run(self):
		print("I AM ID: {}".format(self.NodeId))
		#MultiCastServer definition is in communication.py
		t1 = threading.Thread(target=communication.MulticastServer, args=('224.1.1.1', 8766, self))
		t1.start()

		#websocket for p2p
		loop = asyncio.new_event_loop()
		asyncio.set_event_loop(loop)
		loop.run_until_complete(
		websockets.serve(self.RunRoutine, self.NodeIPAddr, port=self.port, close_timeout=10000))
		asyncio.get_event_loop().run_forever()



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
