from Crypto.PublicKey import RSA
from Crypto import Random

def GenerateKeys(keysize):
	random_generator = Random.new().read
	key = RSA.generate(keysize, random_generator)
	private, public = key, key.publickey()

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