from archer import mr400

if __name__ == "__main__":
	mr400 = mr400.MR400Client("192.168.1.1")
	mr400.login("admin", "myrouterpass")
	print(mr400.get_lte_info())
	print(mr400.get_device_info())
	print(mr400.get_wan_lte_config())
	print(mr400.get_wan_ip_connection())
	#archer.reboot()