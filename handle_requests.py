import messaging
import hashlib
import json

def IsNValid(n):
	# have to do something about that h < n < H
	return True

def digest(message:dict, hash="SHA256"):
	message = json.dumps(message).encode('utf-8')
	return hashlib.sha256(message).hexdigest()



def Request(message, public_key, view, n, private_key):
	verifier = messaging.jwt(jwt=message['token'])
	# Verify the signatue on the token
	verify = verifier.verify(public_key, message['token'])
	final = None
	if verify:
		# If verified, create a new message to forward to other nodes
		pre_prepare = {"v": view,"n": n, "d": digest(message)}
		pre_prepare = json.dumps(pre_prepare)
		pre_prepare = json.loads(pre_prepare)
		# Sign the meessage to generate the token using your privte_key
		pre_prepare = messaging.jwt(json=pre_prepare, header={"alg": "RSA"}, key=private_key)
		pre_prepare = pre_prepare.get_token()

		final = {'type': 'PrePrepare', 'token': pre_prepare, 'm': message}
	return final

def Preprepare(message, public_key_client, public_key_primary, NodeId, private_key_self, view):
	jwt = messaging.jwt()
	m = message['m']['token']
	pre_prepare = message['token']

	result = None
	# Verify both message and pre_prepare
	verify_m = jwt.verify(public_key_client, m)
	verify_p = jwt.verify(public_key_primary, pre_prepare) 
	dnv = jwt.get_payload(pre_prepare)

	_digest = digest(message['m'])

	verify_d = (dnv['d'] == _digest) 
	verify_v = (dnv['v'] == view)
	verify_n = IsNValid(dnv['n'])
	# print(verify_m, verify_p, verify_d)

	if verify_m and verify_p and verify_d and verify_v and verify_n:
		prepare = {"d": dnv['d'], "n": dnv['n'], "v": dnv['v'], "i": NodeId}
		prepare = messaging.jwt(json=prepare, header={"alg": "RSA"}, key=private_key_self)
		prepare = prepare.get_token()
		result = {'type': 'Prepare', 'token': prepare}

	return result


def Prepare(message, ListOfNodes, view):
	# Similarly as per the algorithms. I am lazy.
	token = message['token']
	jwt = messaging.jwt()
	body = jwt.get_payload(token)
	id = body['i']
	# print(ListOfNodes)
	# import time
	# time.sleep(10)

	verify_p = False
	if view == body['v']:
		public_key_i = ListOfNodes[id]['public_key']
		verify_p = jwt.verify(public_key_i, token)

	return verify_p, body

def CreateCommit(message, NodeId, private_key_self):
	jwt = messaging.jwt()
	token = jwt.get_payload(message['token'])
	token['i'] = NodeId
	message['type'] = 'Commit'
	# message['token'] = token
	token = messaging.jwt(json=token, header={"alg": "RSA"}, key=private_key_self)
	token = token.get_token()
	message['token'] = token


	return message

def CreateReply(message, clog, NodeId, private_key_self):
	jwt = messaging.jwt()
	payload = jwt.get_payload(message['token'])
	cur_log = clog.log[payload['d']]
	original_message = jwt.get_payload(cur_log['m'])
	
	reply = {'v': payload['v'], 't': original_message['t'], 'c': original_message['c'], 'i': NodeId}
	op = original_message['o']
	if op == 'add':
		result = int(original_message['args']['num1']) + int(original_message['args']['num2'])
		result = str(result) 

	reply['r'] = result
	token = messaging.jwt(json=reply, header={"alg": "RSA"}, key=private_key_self)
	token = token.get_token()
	reply = {'type': 'Reply', 'token': token}
	return reply


def CreateCheckpointMessage(my_id, message_log, private_key):
	# # # get n and d of the last message executed
	n = -1
	d = ''
	for digest in message_log.log:
		if message_log.log[digest]['n'] > n:
			n = message_log.log[digest]['n']
			d = digest
	# # # create the message to send
	message = {'d': d, 'n': n, 'i':my_id}
	token = messaging.jwt(json=message, header={"alg": "RSA"}, key=private_key)
	token = token.get_token()
	message = {'type': 'CHECKPOINT', 'token': token}
	return message

def VerifyCheckpoint(message, node_list):
	# # # Get the id of the node correspoding to the message so we can retrieve the pubkey
	jwt = messaging.jwt()
	payload = jwt.get_payload(message['token'])
	node_id = payload['i']
	pubkey = node_list[node_id]['public_key']
	
	# Verify 
	return jwt.verify(pubkey, message['token']) 

def CreateViewChangeMessage(checkpoint_log, message_log, v, i, private_key):
	'''
	<”VIEW-CHANGE”, v+1, n, C, P, i)signed by
	'''
	# # # checkpoinging
	C = checkpoint_log.log
	jwt = messaging.jwt()
	n = max([-1] + [jwt.get_payload(C[i])['n'] for i in C])
	# print("View change", i, v, n)
	# print(C)

	# # # message log
	m = message_log.log
	P = {}
	'''
	P = {
		digest: {
			preprepare: ''
			prepare: {
				id: ''
			}
		}
	}
	'''
	for d in m:
		P[d] = {}
		P[d]['preprepare'] = m[d]['preprepare']
		P[d]['prepare'] = m[d]['prepare']
	# print(P)

	view_change_message = {'v': v+1, 'n': n, 'C': C, 'P': P, 'i': i}
	token = messaging.jwt(json=view_change_message, header={
	                      "alg": "RSA"}, key=private_key)
	token = token.get_token()
	message = {'type': 'VIEW-CHANGE', 'token': token}
	return message


def VerifyViewChange(message, node_list):
	jwt = messaging.jwt()
	payload = jwt.get_payload(message['token'])
	node_id = payload['i']
	pubkey = node_list[node_id]['public_key']

	return jwt.verify(pubkey, message['token'])

def CreateNewViewMessage(view, change_view_log, private_key):
	# jwt = messaging.jwt()
	# payload = jwt.get_payload(message['token'])
	new_view_message = {"v": view, "V":change_view_log.log}
	token = messaging.jwt(json=new_view_message, header={
	                      "alg": "RSA"}, key=private_key)
	token = token.get_token()
	message = {'type': 'NEW-VIEW', 'token': token}
	return message


def VerifyNewView(message, list_of_nodes, primary_id):
	# # # check new primary sign is correct
	primary_pubkey = list_of_nodes[str(primary_id)]['public_key']
	if not jwt.verify(primary_pubkey, message['token']):
		return False
	
	# # # check rest of the signs
	jwt = messaging.jwt()
	payload = jwt.get_payload(message['token'])
	for node_id in payload:
		if not jwt.verify(list_of_nodes[str(node_id)]['public_key'], payload[node_id]):
			print(f"{node_id} didn't verify so everything is not ruined!")
			return False
	return True