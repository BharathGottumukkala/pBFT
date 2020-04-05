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
		pre_prepare = {"v": view,"n": 100, "d": digest(message)}
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
	token = jwt.get_payload(message['token'])
	for log in clog:
		if token['d'] == log['d']:
			cur_log = log

	reply = {'v': token['v'], 't': cur_log['m']['t'], 'c': cur_log['m']['c'], 'i': NodeId}
	op = cur_log['m']['o']
	if op == 'add':
		result = int(cur_log['m']['args']['num1']) + int(cur_log['m']['args']['num2'])
		result = str(result) 

	reply['r'] = result
	token = messaging.jwt(json=reply, header={"alg": "RSA"}, key=private_key_self)
	token = token.get_token()
	reply = {'type': 'Reply', 'token': token}
	return reply



