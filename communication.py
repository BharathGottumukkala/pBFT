#!/usr/bin/env python3

import socket
import struct
import asyncio
import websockets
import json


async def SendMsgRoutine(uri, message):
	try:
		async with websockets.connect(uri) as websocket:
			if isinstance(message, dict):
				message = json.dumps(message)
			else:
				message = str(message)
			await websocket.send(message)
	except Exception as e:
		print("Error:{}".format(e))


def SendMsg(uri, message):
	loop = asyncio.new_event_loop()
	asyncio.set_event_loop(loop)
	future = asyncio.ensure_future(SendMsgRoutine(uri, message)) # tasks to do
	loop.run_until_complete(future)


async def BroadCast(SenderIp, SenderPort, ListOfClients, Msg):
	print(ListOfClients)
	for client in ListOfClients:
		if client['IpAddr'] != SenderIp or client['port'] != SenderPort:
			await SendMsg(client['Uri'], Msg)


def Multicast(MCAST_GRP, MCAST_PORT, msg):
	# MCAST_GRP = '225.1.1.1'
	# MCAST_PORT = 8766
	MULTICAST_TTL = 10

	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
	sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, MULTICAST_TTL)
		
	message = json.dumps(msg).encode('utf-8')
	
	sent = sock.sendto(message, (MCAST_GRP, MCAST_PORT))


def MulticastServer(MCAST_GRP, MCAST_PORT, node):
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
		data = sock.recv(10240)
		# print(data)
		data = json.loads(data)
		if data['type'].upper() == "NEWNODE":
			print(f"Id {data['id']} joined the network -> {node.NodeId}")
			

if __name__ == '__main__':
	# Multicast('224.1.1.1', 8766)
	message = {'type': 'Request', 'num1': 1, 'num2': 2}
	# await SendMsg('ws://localhost:8765', message)

