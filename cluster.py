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


def StartNode(port, tries=5):
	try:
		print("tries={}".format(tries))
		if not tries:
			return None
		if not IsPortFree(port):
			raise Exception

		node = Node(port)

		p = Process(target=node.run)

		p.start()
		
		return p
	except Exception as e:
		print("Retrying...")
		print(e)
		port = random.randint(7000, 7100)
		
		StartNode(port, tries-1)



def Cluster(size):

	queue = Queue()
	processes = []
	# port = random.randint(7000, 7500)
	# if primary: 
	# 	p = StartNode(port, True)
	# else:
	# 	p = StartNode(port, False)
	# processes.append(p)
	print("Sleeping")
	time.sleep(1)

	for i in range(0, size):
		port = random.randint(7000, 7500)
		p = StartNode(port)
		processes.append(p)
		time.sleep(1)


if __name__ == '__main__':
	# IsPortFree(7036)
	Cluster(5)
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
