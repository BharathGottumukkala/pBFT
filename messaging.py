import json as js
import base64
from Cijfer import hmac, rsa
from collections import OrderedDict 


def list_algo(algorithm):
	default_algos = { 'HS256': hmac('sha256'),
					  'HS348': hmac('sha384'),
					  'HS512': hmac('sha512'),
					  'RSA': rsa('sha256')
					}

	return default_algos[algorithm]

def json_encoding(json_object):
	encoded = base64.urlsafe_b64encode(js.dumps(json_object).encode('utf-8')).decode('utf-8')
	encoded = encoded.replace('=', '')
	return encoded

class jwt:

    def __init__(self, json=None, jwt=None, header=None, key=b'secret'):
        
        if json is None and jwt is not None:
            self.token = jwt

            # Parse JWT
            parsed_jwt = [base64.b64decode(x + '==') for x in jwt.split('.', 3)]
            self.header, self.payload = [js.loads(x.decode('utf-8')) for x in parsed_jwt[:-1]]
            self.header = OrderedDict(sorted(self.header.items()))
            self.payload = OrderedDict(sorted(self.payload.items()))

            self.signature = parsed_jwt[2]

        elif json is not None and jwt is None:
        	if header is None:
        		raise ValueError("headers not provided")
        	self.payload = OrderedDict(sorted(json.items()))
        	self.header = OrderedDict(sorted(header.items()))

        	self.algorithm = self.header['alg']

        	# msg_to_sign = (base64.urlsafe_b64encode(js.dumps(self.header).encode('utf-8')).decode('utf-8') + "." + base64.urlsafe_b64encode(js.dumps(self.payload).encode('utf-8')).decode('utf-8'))
        	msg_to_sign = json_encoding(self.header) + "." + json_encoding(self.payload)
        	self.signature = list_algo(self.algorithm).sign(key, msg_to_sign.encode('utf-8'))

        	self.token = msg_to_sign + "." + base64.b64encode(self.signature).decode('utf-8')
        	# print(base64.b64encode(self.signature).decode('utf-8'))
        else:
        	pass


    def verify(self, key, token):
    	
    	count = 0
    	# print(token.split('.'))
    	parsed_token = token.split('.')

    	for index in range(len(parsed_token[:-1])):
    		parsed_token[index] = base64.b64decode(parsed_token[index] + "==")

    	parsed_token[2] = parsed_token[2]
    	header, payload = [OrderedDict(sorted(js.loads(x.decode('utf-8')).items())) for x in parsed_token[:-1]]

    	signature = parsed_token[2]
    	if isinstance(signature, str):
    		signature = base64.b64decode(signature.encode('utf-8'))
    	return list_algo(header['alg']).verify(key, (json_encoding(header) + "." + json_encoding(payload)).encode('utf-8'), signature)

    def get_token(self):
    	return self.token

    def get_header(self, token):
    	header = token.split('.')[0]
    	header = base64.b64decode(header + "==")
    	header = js.loads(header.decode('utf-8'))
    	header = OrderedDict(sorted(header.items()))
    	print(header)
    	return header

    def get_payload(self, token):
    	payload = token.split('.')[1]
    	payload = base64.b64decode(payload + "==")
    	payload = js.loads(payload.decode('utf-8'))
    	payload = OrderedDict(sorted(payload.items()))
    	# print(payload)
    	return payload

    def __print_token(self):
    	print(self.token)

if __name__ == '__main__':
	pass

	# import communication
	# import time
	# import sign

	# pub, priv = sign.GenerateKeys(2048)
	# pub, priv = pub.exportKey('PEM'), priv.exportKey('PEM')

	# message = {"op": 'add',"args": {"num1": 5, "num2": 6}, "public_key": pub.decode('utf-8	')}
	# msg = jwt(json=message, header={"alg": "RSA","typ": "Request", "timestamp": int(time.time())}, key=priv)
	# message = msg.get_token()
	# reply = communication.SendMsg('ws://192.168.0.107:3932', message)

	# # a = jwt(json={"sub": "1234567890","name": "John Doe","iat": "1516239022"}, header={"alg": "RSA","typ": "JWT"}, key=priv)
	# # b = a.get_token()
	# print(message)
	# # a.get_payload()

	# d = msg.verify(pub, message)
	# print(d)