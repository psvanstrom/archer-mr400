from archer.mr400 import MR400Client, ConnectionFailedException, LoginFailedException, NotLoggedInException

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
		print(client.get_sms())
		#client.delete_sms(2)
		client.send_sms("0700000000", "Test SMS from Archer MR400Client".)
		#client.reboot()
		client.logout()
	except NotLoggedInException:
		print("Not logged in")
