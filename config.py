import json

# def GetAddress(Key):
# 	with open("config.json", "r") as con:
# 		try:
# 			config = json.load(con)
# 			return config[Key]
# 		except Exception as e:
# 			print(e)
# 			# print("Unable to load config file")
# 			print("erorr in parsing config file")
# 			# print("Reinitializing Config file...")

# def UpdateAddress(Key, value):
# 	with open("config.json", "r") as con:
# 		config = json.load(con)
# 		config[Key] = value

# 	with open("config.json", "w") as con:
# 		json.dump(con, config)


class config(object):
	"""docstring for config"""
	def __init__(self):
		self.file = "/users/ConMan/pBFT/config.json"
		exception = False
		with open(self.file, "r") as con:
			try:
				config = json.load(con)
			except Exception as e:
				print("Error in parsing config.")
				print("Initializing config")
				exception = True
		if exception:
			self.InitializeConfig()


	def UpdateAddress(self, key, value):
		with open(self.file, "r") as con:
			config = json.load(con)
		config[key] = value
		with open(self.file, "w") as con:
			json.dump(config, con)

	def GetAddress(self, key):
		with open(self.file, "r") as con:
			config = json.load(con)
			return config[key]

	def InitializeConfig(self):
		with open(self.file, "w") as con:
			json.dump({}, con)



if __name__ == '__main__':
	config = config()
	config.UpdateAddress('client', '10.1.1.1')
	print(config.GetAddress('client'))

