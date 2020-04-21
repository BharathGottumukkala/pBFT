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
import time

# Custom imports

# commuication handles Sending messages to different nodes
import communication	

# Only to be used for printing log
import messaging

# Functions to handle incoming requests
import handle_requests

# Logging 
import mlog
# Report back to client for demo purposes
import report

# Dynamic Address resolution for Flask server and NameScheduler
from config import config

# for the timer
TIMER_WAITING_TIME = 2
MULTICAST_SERVER_IP = '224.1.1.1'
MULTICAST_SERVER_PORT = 8766

class Node(object):
	"""docstring for Node"""
	def __init__(self, port):
		self.NodeId = None     
		# self.NodeIPAddr = re.search(re.compile(r'(?<=inet )(.*)(?=\/)', re.M), os.popen('ip addr show enp4s0f1').read()).groups()[0] 
		# self.NodeIPAddr = self.GetIp()
		self.NodeIPAddr = communication.GetLocalIp()
		# self.NameSchedulerURI = "ws://" + self.NodeIPAddr + ':' + '8765'
		# self.NameSchedulerURI = "ws://0.0.0.0:8765"
		self.NameSchedulerURI = "ws://" + config().GetAddress('NameScheduler') + ":8765"
		self.port = port
		# Decides whether the node is primary
		# self.IsPrimary = IsPrimary
		self.Uri = "ws://" + self.NodeIPAddr + ':' + str(self.port)
		print(self.Uri)
		self.ListOfNodes = {}
		self.pre_prepare_msgs = 0
		self.mode = 'Sleep'
		self.view = 0
		self.count = 0
		self.log = mlog.MessageLog()
		self.ckpt_log = mlog.CheckLog()
		self.view_change_log = mlog.ViewChangeLog()

		self.total_allocated = 0
		self.faults = {'malicious': False, 'reboot': False, 'netdelay': False, 'benign':True}
		self.timer = threading.Timer(30, print) #print is random, just for the sake of initialisation
		"""
		self.ListOfNodes = {'NodeID': {uska details}}
		
		self.log = {
					"d": {
							'c': client_id, 
							'v': view, 
							'n': seq_num, 
							'm': Client_msg, 
							'preprepare': preprepare_msg,
							"prepare":{
										id: prepare message
									},
							"commit": {
										id: commit message
									},
						}
					}
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
		if not self.total_allocated:
			return str(self.view) == str(self.NodeId)
		else:
			return str(self.view % self.total_allocated) == str(self.NodeId)

	def SendStatusUpdate(self, new_mode):
		report.Report(self.client_uri, 'status', {'id': self.NodeId, 'view':self.view , 'status': new_mode})


	def ChangeMode(self, mode):
		possible_modes = ['Sleep', 'Prepare', 'Commit', 'Checkpoint', 'View-Change']
		if mode not in possible_modes:
			raise f"{mode} is not a valid mode. Please select from {possible_modes}"
		print(f"{self.NodeId} changing mode from {self.mode} to {mode}")
		self.mode = mode
		self.SendStatusUpdate(self.mode.lower())
		# time.sleep(0.5)


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
				print(list(self.ListOfNodes.keys()))
				self.public_key = self.ListOfNodes[self.NodeId]['public_key'].encode('utf-8')
				self.private_key = self.ListOfNodes[self.NodeId]['private_key'].encode('utf-8')

	
	def InitiateViewChange(self):
		# # # View change
		view_change_message = handle_requests.CreateViewChangeMessage(self.ckpt_log,
													self.log, self.view, self.NodeId,
													self.private_key)
		# print(view_change_message)
		communication.Multicast(MULTICAST_SERVER_IP, MULTICAST_SERVER_PORT, view_change_message)
		self.ChangeMode('View-Change')


	async def RunRoutine(self, websocket, path):
		# Defines the funcioning of each node on receiving differnet messages
		async for message in websocket:
			# message format
			# message = {'type': type, 'token': token}
			# token is generated using messaging library in handle_requests
			message = json.loads(message)

			# # # ID = 3 is faulty for testing
			if int(self.NodeId) % 3 == 1:
				return
			
			# # # We enter 'View-Change' mode when some error is detected. So no messages except VIEW-CHANGE are accepted
			if message['type'].upper() not in ['VIEW-CHANGE', 'NEW-VIEW'] and self.mode == 'View-Change':
				return #dont do anything, there is something wrong with the distributed system!


			# # # When a new node is added, Register the nde's details for future communication
			if message['type'].upper() == 'NEWNODE':
				print(f"Id {message['id']} joined the network -> {self.NodeId}")
				self.register(message)


			# # # Allocate the node to the cluster
			elif message['type'].upper() == 'ALLOCATE':
				self.ListOfNodes[self.NodeId]['allocate'] = True
				# report.Report(self.client_uri, 'allocate', {'total': str(i+1)})
				print(f"{self.NodeId} -> I got allocated")
				self.log.flush()
				self.ckpt_log.flush()
				self.view_change_log.flush()
				self.view = 1
				self.total_allocated = message['total']
				self.SendStatusUpdate('allocated')
				# report.Report(self.client_uri, 'status', {'id': self.NodeId, 'view':self.view , 'status': 'allocated'})

			# # # DeAllocate the node from the cluster
			elif message['type'].upper() == 'DEALLOCATE':
				self.ListOfNodes[self.NodeId]['allocate'] = False
				print(f"{self.NodeId} -> I got deallocated")
				self.log.flush()
				self.ckpt_log.flush()
				self.view_change_log.flush()
				self.view = 0
				self.total_allocated = message['total']
				self.SendStatusUpdate('deallocated')
				# report.Report(self.client_uri, 'status', {
				#               'id': self.NodeId, 'status': 'deallocated'})

			elif message['type'].upper() == 'MODIFYFAULT':
				del message['id']
				del message['type']
				for fault, value in message.items():
					self.faults[fault] = value
				print(f"{self.NodeId} -> Modified Fault parameters")
				print(self.faults)



			# # # Get and register client's info
			elif message['type'].upper() == 'CLIENT':
				# # # Here the message i of different format..fck. Will update this in the next release :p
				# # # message = {'type': type, 'client_id': '...', 'public_key':'...', 'Uri': '...'}
				self.client_id = message['client_id']
				self.client_public_key = message['public_key'].encode('utf-8')
				self.client_uri = message['Uri']
				print(f"{self.NodeId} -> Received Client publickey")
				# # # This report is the first report thatwas taking time for some reason
				# # # Added here so that it goes unnoticed in the startup process of emulab
				if self.IsPrimary():
					report.Report(self.client_uri, 'status', {'test': 'All the best'})


			# # # Request recieved from client
			elif message['type'].upper() == 'REQUEST' and self.mode == 'Sleep':
				if self.IsPrimary():
					print(f"I am the primary with ID = {self.NodeId}. And I have just recieved a REQUEST from the client!")

					# # # gen a new sequence number as (last+1)-----(default is 100)
					seq_num = self.log.get_last_logged_seq_num() + 1

					# # # Report UI that request has been received
					self.SendStatusUpdate("request")

					# # # Verify client's sign and returns the next message to send
					final_message = handle_requests.Request(message, self.client_public_key, self.view, seq_num, self.private_key)
					
					if final_message is not None:
						# # # sign on message verified: Multicast the request all nodes in the network
						communication.Multicast(MULTICAST_SERVER_IP, MULTICAST_SERVER_PORT, final_message, self.faults)
					else:
						# # # Client did not verify
						print(f"{self.NodeId} -> The message verification failed")
						# # # Nothing more to do
				else:
					# # # Node is not primary. Send the message to the actual 
					print(f"Well I am NOT the primary with ID = {self.NodeId} in view {self.view}. I shall forward it to the required owner!")
					await communication.SendMsgRoutine(self.ListOfNodes[str(int(self.view) % self.total_allocated)]['Uri'], message)
					self.timer = threading.Timer(TIMER_WAITING_TIME, self.InitiateViewChange)
					self.timer.start()


			# # # PREPREPARE
			elif message['type'].upper() == 'PREPREPARE' and self.mode == 'Sleep':
				#if some temporary fault happened and timer was started
				if self.timer.is_alive():
					print(f"ID = {self.NodeId}, primary={self.IsPrimary()}. Closing the timer!")
					self.timer.cancel()
				print(f"ID = {self.NodeId}, primary={self.IsPrimary()}. Starting PREPREPARE.")
				# print(message)
				public_key_primary = self.ListOfNodes[str(self.view % self.total_allocated)]['public_key']

				# # # Send all the details. It will verify and return the next packet to send
				result = handle_requests.Preprepare(message, self.client_public_key, public_key_primary, self.NodeId, self.private_key, self.view)
				
				# # # verification successful
				if result is not None:
					self.ChangeMode("Prepare")
					# print(f"{self.NodeId} -> PrePrepare logging...")
					self.log.AddPrePrepare(message)
					# print(f"{self.NodeId} -> PrePrepare logged")

					# print(f"{self.NodeId} -> self Prepare logging...")
					self.log.AddPrepare(result)
					# print(f"{self.NodeId} -> self Prepare logged")
					communication.Multicast(MULTICAST_SERVER_IP, MULTICAST_SERVER_PORT, result, self.faults)

			
			# # # PREPARE
			elif message['type'].upper() == 'PREPARE':
				# # # This verifies the message and returns back the body of the message as well for logging
				# # # Look at the initialization step for self.log definition
				verify_p, pToken = handle_requests.Prepare(message, self.ListOfNodes, self.view)
				
				# # # m should be in logs
				verify_m = (pToken['d'] in self.log.log)

				if verify_p and verify_m:
					self.log.AddPrepare(message)
					cur_log = self.log.RequestLog(pToken)
					count = len(cur_log['prepare'])

				# If enough 2f+1 nodes ready to 'Prepare', go to 'Commit'
				if count >= 2*self.total_allocated//3 :
					if self.mode == 'Prepare':
						commit = handle_requests.CreateCommit(message, self.NodeId, self.private_key)
						self.ChangeMode("Commit")
						communication.Multicast(MULTICAST_SERVER_IP, MULTICAST_SERVER_PORT, commit, self.faults)

			elif message['type'].upper() == 'COMMIT':
				verify_p, cToken = handle_requests.Prepare(message, self.ListOfNodes, self.view)
				if verify_p:
					self.log.AddCommit(message)
					# print(f"{self.NodeId} -> Commit logged")

				cur_log = self.log.RequestLog(cToken)
				count = len(cur_log['commit'])
				if count >= 2*self.total_allocated//3 and self.mode == 'Commit':
					reply = handle_requests.CreateReply(message, self.log, self.NodeId, self.private_key)
					report.Report(self.client_uri, 'reply', reply)
					self.SendStatusUpdate('reply')  # Report to UI that reply is to be sent
					print(f"{self.NodeId} -> Sent a REPLY to the client!")
					self.ChangeMode('Sleep')

					# # # CHECKPOINTING
					# if len(self.log.log) >= 2:
					# 	print(f"CHECKPOINTING, messages = {len(self.log.log)}")
					# 	# if more than 5 messages in message log, flush it!
					# 	checkpoint_message = handle_requests.CreateCheckpointMessage(self.NodeId, self.log, self.private_key)
					# 	communication.Multicast(MULTICAST_SERVER_IP, MULTICAST_SERVER_PORT, checkpoint_message)
					# 	self.ChangeMode('Checkpoint')


			elif message['type'].upper() == 'CHECKPOINT':
				# # # only do all the checkpointing stuff if there is stuff in the message log to flush
				
				if not self.log.IsEmpty():
					if handle_requests.VerifyCheckpoint(message, self.ListOfNodes):
						print(f"{self.NodeId} -> Adding checkpoint to log!")
						self.ckpt_log.AddCheckpoint(message)
						# flush logs
						if self.ckpt_log.NumMessages() >= 2*self.total_allocated//3 and self.mode == 'Checkpoint':
							self.log.flush()
							print(f"{self.NodeId} -> FLUSHING MESSAGE LOGS!")
							self.ChangeMode('Sleep')

				# print(f"I am {self.NodeId} and I recieved a checkpoint message from {messaging.jwt().get_payload(message['token'])['i']}")

			elif message['type'].upper() == 'VIEW-CHANGE':
				if handle_requests.VerifyViewChange(message, self.ListOfNodes):
					self.view_change_log.AddViewChangeMessage(message)

					if self.view_change_log.NumMessages() >= 2*self.total_allocated//3 and self.mode == 'View-Change':
						# # # if new primary, tell everyone that view change successful!
						# print(f"View = {self.view}, check = {int(self.view)+1} % {self.total_allocated} == {int(self.NodeId)}")
						if ((int(self.view)+1) % self.total_allocated) == int(self.NodeId):
							print(f"{self.NodeId} -> Okay, so I'll be the new primary for view {self.view+1}! I am telling everyone to finish changing view?")
							new_view_message = handle_requests.CreateNewViewMessage(self.view, self.view_change_log, self.private_key)
							communication.Multicast(MULTICAST_SERVER_IP, MULTICAST_SERVER_PORT, new_view_message)

				else:
					print(f"{self.NodeId} -> Verification of ViewChange failed")

			elif message['type'].upper() == 'NEW-VIEW':
				if handle_requests.VerifyNewView(message, self.ListOfNodes, int(self.view+1)%self.total_allocated):
					self.view = self.view + 1
					print(f"{self.NodeId} -> After changing views to {self.view}, I'm going to sleep....")
					# report.Report(self.client_uri, 'status', {'id': self.NodeId, 'view':self.view , 'status': 'view_change'})
					self.ChangeMode('Sleep')

				# print(f"I am {self.NodeId} and I recieved a checkpoint message from {messaging.jwt().get_payload(message['token'])['i']}")


	def HandShake(self, uri):
		loop = asyncio.new_event_loop()
		asyncio.set_event_loop(loop)
		future = asyncio.ensure_future(self.HandshakeRoutine(uri)) # tasks to do
		loop.run_until_complete(future)
		# del loop


	def run(self):
    	#get details of self
		if self.NodeId is None:
			self.HandShake(self.NameSchedulerURI)

		# MultiCastServer definition is in communication.py
		t1 = threading.Thread(target=communication.MulticastServer, args=(MULTICAST_SERVER_IP, MULTICAST_SERVER_PORT, self))
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
