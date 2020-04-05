"""
This generates RSA KEys, and has signature and verification methods

"""



from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA512, SHA384, SHA256, SHA, MD5
from Crypto import Random
from base64 import b64encode, b64decode

hash = "SHA-256"

def GenerateKeys(keysize):
    random_generator = Random.new().read
    key = RSA.generate(keysize, random_generator)
    private, public = key, key.publickey()
    return public, private

def importKey(externKey):
    return RSA.importKey(externKey)

def getpublickey(priv_key):
    return priv_key.publickey()

def encrypt(message, pub_key):
    #RSA encryption protocol according to PKCS#1 OAEP
    cipher = PKCS1_OAEP.new(pub_key)
    return cipher.encrypt(message)

def decrypt(ciphertext, priv_key):
    #RSA encryption protocol according to PKCS#1 OAEP
    cipher = PKCS1_OAEP.new(priv_key)
    return cipher.decrypt(ciphertext)

def sign(message, priv_key, hashAlg="SHA-256"):
    global hash
    hash = hashAlg
    signer = PKCS1_v1_5.new(priv_key)
    if (hash == "SHA-512"):
        digest = SHA512.new()
    elif (hash == "SHA-384"):
        digest = SHA384.new()
    elif (hash == "SHA-256"):
        digest = SHA256.new()
    elif (hash == "SHA-1"):
        digest = SHA.new()
    else:
        digest = MD5.new()
    digest.update(message)
    return signer.sign(digest)

def verify(message, signature, pub_key, hash="SHA-256"):
    signer = PKCS1_v1_5.new(pub_key)
    if (hash == "SHA-512"):
        digest = SHA512.new()
    elif (hash == "SHA-384"):
        digest = SHA384.new()
    elif (hash == "SHA-256"):
        digest = SHA256.new()
    elif (hash == "SHA-1"):
        digest = SHA.new()
    else:
        digest = MD5.new()
    digest.update(message)
    return signer.verify(digest, signature)


if __name__ == '__main__':
	msg1 = b"Hello Tony, I am Jarvis!"
	msg2 = b"Hashello Toni, I am Jarvis!"
	keysize = 2048
	(public, private) = newkeys(keysize)
	encrypted = b64encode(encrypt(msg1, public))
	decrypted = decrypt(b64decode(encrypted), private)
	signature = b64encode(sign(msg1, private, "SHA-512"))
	verify = verify(msg1, b64decode(signature), public)

	print(private.exportKey('PEM'))
	print(public.exportKey('PEM'))
	print("Encrypted: " + encrypted.decode('utf-8'))
	print("Decrypted: '%s'" % decrypted.decode('utf-8'))
	print("Signature: " + signature.decode('utf-8'))
	print("Verify: %s" % verify)
	# verify(msg2, b64decode(signature), public)