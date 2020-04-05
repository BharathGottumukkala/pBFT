"""
Class contains the methods used in messaging

messaging imports class rsa to sign using those keys

"""




import hashlib
import hmac as hm
import base64

import sign as s


class cijfer:

    '''
    Base Class for Signature Algorithms
    Methods - prepare_key(key), sign(key,msg), verify(key, msg, sign)
    Override Methods in inheriting class to implement new signature algorithm.

    class newCipher(cijfer):
        def prepare_key(self, key):
            # Define key formatting / preparation procedure
            pass
        
        def sign(self, key, msg):
            # Implement Signature scheme
            # Return a bytes Object
            pass
        
        def verify(self, key, msg, sign):
            # Verify digest with msg
            # Return bool
            pass

    '''

    def prepare_key(self, key):

        ''' Prepare the key in the correct format for the cipher '''
        
        raise NotImplementedError

    def sign(self, key, msg):

        ''' Sign The msg using the key using the cipher '''

        raise NotImplementedError

    def verify(self, key, msg, sign):

        ''' Verify the msg using the sign '''

        raise NotImplementedError



class hmac(cijfer):

    __hash_list = { 'sha256': hashlib.sha256, 'sha384':hashlib.sha384, 'sha512':hashlib.sha512 }


    def __init__(self, hash_alg):
        self.__hash_alg = self.__hash_list[hash_alg.lower()]

    @staticmethod
    def hash_list():
        return ["sha256", "sha512"]

    def sign(self, key, msg):
        if not isinstance(key, bytes) or not isinstance(msg, bytes):
            raise TypeError
        else:
            return base64.urlsafe_b64encode(hm.new(key, msg, self.__hash_alg).digest())


    def prepare_key(self, key):
        
        ''' Should be in string '''
        if not isinstance(key, string):
            raise TypeError
        else:
            return key.encode('utf-8')

    def verify(self, key, msg, sign):
        # print()
        # print(sign, base64.urlsafe_b64encode(hm.new(key, msg, self.__hash_alg).digest()))
        # print()
        return hm.compare_digest(sign, base64.urlsafe_b64encode(hm.new(key, msg, self.__hash_alg).digest()) ) 

class rsa(cijfer):
    """docstring for rsa"""
    __hash_list = { 'sha256': hashlib.sha256, 'sha384':hashlib.sha384, 'sha512':hashlib.sha512 }

    def __init__(self, hash_alg):
        self.__hash_alg = self.__hash_list[hash_alg.lower()]

    def sign(self, key, msg):
        if not isinstance(key, bytes) or not isinstance(msg, bytes):
            raise TypeError
        else:
            return s.sign(msg, s.importKey(key), self.__hash_alg)
        
    def verify(self, key, msg, sign):
        return s.verify(msg, sign, s.importKey(key), self.__hash_alg)