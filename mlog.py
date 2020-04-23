import messaging

class MessageLog:
	def __init__(self):
		self.log = {}

	def IsUnique(self, message):
		isUnique = True
		for l in self.log:
			if l['i'] == message['i']:
				isUnique =False
		return isUnique

	def get_last_logged_seq_num(self):
		if self.log == {}:
			return -1
		return max([self.log[d]['n'] for d in self.log])

	def IsEmpty(self):
		return self.log == {}

	def HasDigestEntry(self, message):
		jwt = messaging.jwt()
		payload = jwt.get_payload(message['token'])
		return payload['d'] in self.log

	def flush(self):
		self.log = {}

	def Print(self):
		print(self.log)

	def RequestLog(self, message):
		return self.log[message['d']]

	def AddPrePrepare(self, message):
		if self.HasDigestEntry(message):
			return
		jwt = messaging.jwt()
		preprepare = jwt.get_payload(message['token'])
		m = jwt.get_payload(message['m']['token'])
		self.log[preprepare['d']] = {
				'c': m['c'],
				'n': preprepare['n'],
				'v': preprepare['v'],
				'm': message['m']['token'], 
				'preprepare': message['token'],
				'prepare': {},
				'commit': {}
		}

	def AddPrepare(self, message):
		'''
		add prepare message to log
		'''
		jwt = messaging.jwt()
		i = jwt.get_payload(message['token'])['i']
		d = jwt.get_payload(message['token'])['d']
		self.log[d]['prepare'][i] = message['token']

	def AddCommit(self, message):
		'''
		add commit message to log
		'''
		jwt = messaging.jwt()
		i = jwt.get_payload(message['token'])['i']
		d = jwt.get_payload(message['token'])['d']
		self.log[d]['commit'][i] = message
		

class CheckLog:
	def __init__(self):
		self.log = {}
		'''
		format:
		self.log = {
			i: last_checkpoint_message_from_i,
		}
		'''

	def NumMessages(self):
		return len(self.log)
	
	def AddCheckpoint(self, message):
		'''
		add Checkpoint message to log
		'''
		jwt = messaging.jwt()
		checkpoint = jwt.get_payload(message['token'])
		self.log[checkpoint['i']] = message['token']

	def flush(self):
		self.log = {}
	
	def Print(self):
		print(self.log)

class ViewChangeLog:
	def __init__(self):
		self.log = {}
		'''
		format:
		self.log = {
			i: last_view_change_message_from i,
		}
		'''

	def NumMessages(self):
		return len(self.log)

	def AddViewChangeMessage(self, message):
		'''
		add view change message to log
		'''
		jwt = messaging.jwt()
		view_change = jwt.get_payload(message['token'])
		self.log[view_change['i']] = message['token']

	def flush(self):
		self.log = {}

	def Print(self):
		print(self.log)
