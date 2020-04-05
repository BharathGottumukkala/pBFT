from Crypto.PublicKey import RSA
from Crypto import Random

def GenerateKeys(keysize):
	# print('a')
	random_generator = Random.new().read
	# print('b')
	key = RSA.generate(keysize, random_generator)
	# print('c')

	private, public = key, key.publickey()
	# print('c')

	return public, private

def importKey(externKey):
    return RSA.importKey(externKey)

def getpublickey(priv_key):
    return priv_key.publickey()


if __name__ == '__main__':
	import time
	start = time.time()
	GenerateKeys(2048)
	print(time.time() - start)