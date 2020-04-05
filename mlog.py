import messaging

def IsUnique(message, log):
	isUnique = True
	for l in log:
		if l['i'] == message['i']:
			isUnique =False
	return isUnique


def RequestLog(message, clog):
	for log in clog:
		if message['d'] == log['d']:
			return log



def log(clog, message):
	jwt = messaging.jwt()
	if message['type'] == 'PrePrepare':
		preprepare = jwt.get_payload(message['token'])
		m = jwt.get_payload(message['m']['token'])
		clog.append({'d': preprepare['d'], 'm': m, 'preprepare': preprepare})

		return clog

	if message['type'] == 'Prepare':
		prepare = jwt.get_payload(message['token'])
		for log in clog:
			if log['d'] == prepare['d']:
				try:
					if IsUnique(prepare, log['prepare']):
						log['prepare'].append(prepare)
				except Exception as e:
					print(e)
					log['prepare'] = []
					log['prepare'].append(prepare)
		return clog

	if message['type'] == 'Commit':
		commit = jwt.get_payload(message['token'])
		for log in clog:
			if log['d'] == commit['d']:
				try:
					if IsUnique(commit, log['commit']):
						log['commit'].append(commit)
				except Exception as e:
					print(e)
					log['commit'] = []
					log['commit'].append(commit)

		return clog



		

	# clog = {}
	# clog['type'] = message['type']
	# clog['token'] = message['token']
	# jwt = messaging.jwt()

	# mbody = jwt.get_payload(message['token'])

	# result = {'type': message['type'], 'token': mbody}

	# m = None
	# if 'm' in message:
	# 	m = jwt.get_payload(message['m'])
	# 	result['m'] = m


	# return result