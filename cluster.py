"""
Flask server creates Cluster by spawing multiple processes

"""



from multiprocessing import Process, Queue
from Node import Node
import random
import time
import socket, errno


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


def StartNode(port, IsPrimary, tries=5):
	try:
		# IsPortFree(port)
		# print("############################")
		# print('\n'*20)
		print("tries={}".format(tries))
		if not tries:
			return None
		# port = 8760
		if not IsPortFree(port):
			raise Exception

		# print("Creating Node")
		node = Node(port, IsPrimary)
		# print("Creating Node")

		p = Process(target=node.run)
		# print("Creating Node")

		p.start()
		# print("Creating Node")
		
		return p
	except Exception as e:
		print("Retrying...")
		print(e)
		port = random.randint(7000, 7100)
		
		# port = 8765
		StartNode(port, IsPrimary, tries-1)



def Cluster(size, primary):
	queue = Queue()
	processes = []
	port = random.randint(7000, 7500)
	if primary: 
		p = StartNode(port, True)
	else:
		p = StartNode(port, False)
	processes.append(p)
	print("Sleeping")
	time.sleep(0.2)

	for i in range(1, size):
		port = random.randint(7000, 7500)
		p = StartNode(port, False)
		processes.append(p)
		time.sleep(1)

	for p in processes:
		print("DAMN")
		p.join()
		print("IT")


if __name__ == '__main__':
	IsPortFree(7036)
	# queue = Queue()
	# processes = []
	# try:
	# 	p = Process(target=Cluster, args=(int(4),))
	# 	p.start()
	# except Exception as e:
	# 	pass

    # for i in range(4):
    # 	port = random.randint(2000, 8000)
    # 	node = Node(port, IsPrimary=False)
    # 	p = Process(target=node.run)
    # 	p.start()
    # 	processes.append(p)
    # 	time.sleep(1)

    # for p in processes:
    # 	print("DAMN")
    # 	p.join()
    # 	print("IT")

    # node = Node(2001, True)
    # p = Process(target=node.run)
    # p.start()
    # p.join() # this blocks until the process terminates
    # result = queue.get()
    # print(result)
