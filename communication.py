#!/usr/bin/env python3

import socket
import struct
import asyncio
import websockets
import json
import time

from netifaces import interfaces, ifaddresses, AF_INET

import report
from config import config


def GetLocalIp():
	for ifaceName in interfaces():
		addresses = [i['addr'] for i in ifaddresses(ifaceName).setdefault(AF_INET, [{'addr':'No IP addr'}] )]
		f = addresses[0].split('.')
		if f[0] == '10':
			return addresses[0]
		elif f[0] == '192':
			return addresses[0]


def UpdateNodeDetails(NameSchedulerURI):
	# Check If NameScheduler is online
	try:
		# Send an empty msg to NameScheduler
		SendMsg(NameSchedulerURI, {'type': 'Null'})
		# If NameScheduler is online
		try:
			message = {'type': "UpdateDetails"}
			SendMsg(NameSchedulerURI, message)

		except Exception as e:
			print("Nested try")
			print(e)

	except Exception as e:
		# If exception occurs, NameScheduler is offilne. Nothing to update
		return




async def SendMsgRoutine(uri, message):
	# Asyncronous send used by websockets
	try:
		# Connect to node's Uri and send anything
		async with websockets.connect(uri) as websocket:
			# print(f"Connected to {uri}")
			# We can only send a string
			if isinstance(message, dict):
				message = json.dumps(message)
			else:
				message = str(message)
			# print("sending msg")
			await websocket.send(message)
			# print("sent message")
	except Exception as e:
		# pass
		print("Error:{}".format(e))
		print('Retrying...')
		time.sleep(0.5)
		await SendMsgRoutine(uri, message)


def SendMsg(uri, message):
	# Used by synchronous servers ike flask to send "sort of" async msgs I guess
	# Mainly for flask to send msgs to websocket servers
	loop = asyncio.new_event_loop()
	# print("Loop created")
	asyncio.set_event_loop(loop)
	# print("set set_event_loop")
	# loop.create_task(SendMsgRoutine(uri, message))
	future = asyncio.ensure_future(SendMsgRoutine(uri, message))
	# print("after future command") # tasks to do
	loop.run_until_complete(future)
	# print("After loop.run()")
	del loop


async def BroadCast(SenderIp, SenderPort, ListOfClients, Msg):
	# Basically send msgs in a loop. Not a good Idea
	try:
		for client in ListOfClients.values():
			if client['IpAddr'] != SenderIp or client['port'] != SenderPort:
				await SendMsgRoutine(client['Uri'], Msg)

	except RuntimeError as e:
		print("More Clients found. Updating..")
		await BroadCast(SenderIp, SenderPort, ListOfClients, Msg)



def Multicast(MCAST_GRP, MCAST_PORT, msg):
	# Multicast Send to the multicast server running on each node
	# I found only 2 multicast grps : 224.1.1.1, 225.1.1.1
	# We can have any port

	# MCAST_GRP = '225.1.1.1'
	# MCAST_PORT = 8766
	MULTICAST_TTL = 10

	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
	sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, MULTICAST_TTL)
		
	message = json.dumps(msg).encode('utf-8')
	
	sent = sock.sendto(message, (MCAST_GRP, MCAST_PORT))


def MulticastServer(MCAST_GRP, MCAST_PORT, node):
	# Defines the server that is running on each node
	# It receives the message and forwards it to its own websocket server where the request is handled


	# MCAST_GRP = '225.1.1.1'
	# MCAST_PORT = 8766
	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
	sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	port = 8766
	print("Socket created")
	sock.bind((MCAST_GRP, MCAST_PORT))
	# sock.bind(('', port))  
	mreq = struct.pack("4sl", socket.inet_aton(MCAST_GRP), socket.INADDR_ANY)
	sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
	while True:
		data = sock.recv(50240)
		# print(data)
		data = json.loads(data)

		# if data['type'] == 'Allocate':
		# 	node.ListOfNodes[node.NodeId]['allocate'] = True

		if data['type'] == 'NewNode':
			SendMsg(node.Uri, data)
			
		# Every node except NameScheduler
		if node.NodeId != -1:
			if node.ListOfNodes[node.NodeId]['allocate']:
				SendMsg(node.Uri, data)
			

if __name__ == '__main__':
	# Multicast('224.1.1.1', 8766)
	message = {'type': 'Request', 'num1': 1, 'num2': 2}
	SendMsg("ws://192.168.0.113:7086", message)
	# await SendMsg('ws://localhost:8765', message)

