from archer.mr400 import MR400Client, ConnectionFailedException, LoginFailedException 

if __name__ == "__main__":
	client = MR400Client("192.168.1.1")
	try:
		client.login("admin", "myrouterpass")
	except ConnectionFailedException:
		print("Cannot connect to router")
		exit()
	except LoginFailedException:
		print("Bad login")
		exit()
	try:
		print(client.get_clients())
		print(client.get_lte_info())
		print(client.get_device_info())
		print(client.get_wan_lte_config())
		print(client.get_wan_ip_connection())
		#client.reboot()
	except NotLoggedInException:
		print("Not logged in")
