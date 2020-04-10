"""
Flask server creates Cluster by spawing multiple processes
"""
from multiprocessing import Process, Pool
from Node import Node
import random
import socket, errno
import sign

def IsPortFree(port):
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	try:
		s.bind(("0.0.0.0", port))
		s.close()
		return True
	except socket.error as e:
		if e.errno == errno.EADDRINUSE:
		    print("Port is already in use")
		else:
		    # something else raised the socket.error exception
		    print(e)
		s.close()
		return False


def Cluster(size, client_port, client_uri, client_public_key):
	#get list of available ports
	ports = list(filter(IsPortFree, list(range(7000, 7200))))[:size]
	#get list of asym. keys
	public_keys = []
	private_keys = []
	print("Creating keys.. It takes a while so wait please!")
	import time
	t = time.time()
	for i in range(size):
		pub, priv = sign.GenerateKeys(2048)
		pub, priv = pub.exportKey('PEM'), priv.exportKey('PEM')
		public_keys.append(pub)
		private_keys.append(priv)
	print("Took {} seconds to create {} key pairs.".format(time.time() - t, size))
	#gen. node info for all nodes to use
	nodes_info = {
		i: {
			'port': ports[i], 
			'public_key': public_keys[i], 
			'Uri': 'ws://127.0.0.1:' + str(ports[i])
			}
		for i in range(size)
		}
	# client info
	nodes_info['client'] = {
		'port': client_port, 
		'public_key': client_public_key, 
		'Uri': client_uri,
	}
	#start nodes
	for i in range(size):
		node = Node(node_id=i,
			private_key=private_keys[i],
			nodes_info=nodes_info)
		Process(target=node.run).start()

	print("Returning nodes", nodes_info)

	return nodes_info



if __name__ == '__main__':
	# for i in range(3000):
	# 	if not IsPortFree(7000+i):
	# 		print(i)
	Cluster(1)
