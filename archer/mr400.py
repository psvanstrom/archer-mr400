import rsa
import binascii
import base64
import requests
import re

class NotLoggedInException(Exception):
	pass

class LoginFailedException(Exception):
	pass

class ConnectionFailedException(Exception):
	pass

class MR400Client:
	def __init__(self, router_ip):
		self.router_ip = router_ip
		self.cgi_url = f"http://{router_ip}/cgi"
		self.session = requests.Session()
		self.session.headers = {'referer': f'http://{self.router_ip}/', 'origin': f'http://{self.router_ip}'}

	def __get_params(self, retry=False):
		try:
			r = self.session.get(f"{self.cgi_url}/getParm", timeout=5)
			result = {}
			for line in r.text.splitlines()[0:2]:
				match = re.search(r"var (.*)=\"(.*)\"", line)
				result[match.group(1)] = int(match.group(2), 16)
			return result
		except:
			if not retry:
				# allow one retry, first try to get params sometimes fail 
				return self.__get_params(True)
			raise ConnectionFailedException()

	def __check_login_status(self):
		if not "TokenID" in self.session.headers or not "JSESSIONID" in self.session.cookies:
			raise NotLoggedInException()

	def login(self, username, password):
		params = self.__get_params()
		pub_key = rsa.PublicKey(n=params["nn"], e=params["ee"])

		rsa_username = binascii.hexlify(rsa.encrypt(username.encode('utf8'), pub_key)).decode('utf8')
		rsa_password = binascii.hexlify(rsa.encrypt(base64.b64encode(password.encode('utf8')), pub_key)).decode('utf8')

		self.session.post(f'{self.cgi_url}/login?UserName={rsa_username}&Passwd={rsa_password}&Action=1&LoginStatus=0')
		r = self.session.get(f'http://{self.router_ip}/')
		try:
			self.session.headers["TokenID"] = re.search(r"var token=\"(.*)\";", r.text).group(1)
		except AttributeError:
			raise LoginFailedException()

	def __make_dict(self, response_text):
		result = {}
		for line in response_text.splitlines():
			if "=" in line:
				split_str = line.split("=")
				result[split_str[0]] = split_str[1]
		return result

	def __make_list_dict(self, response_text):
		l = []
		d = {}
		for line in response_text.splitlines():
			match = re.search("\\[([0-9]*),.*", line)
			if match != None:
				if d:
					d["idx"] = i
					l.append(d)
					d = {}
				i = int(match.group(1))
			elif "=" in line:
				split_str = line.split("=")
				d[split_str[0]] = split_str[1]
		if d:
			d["idx"] = i
			l.append(d)
		return l

	def get_clients(self):
		self.__check_login_status()
		r = self.session.post(f'{self.cgi_url}?5', data="[LAN_HOST_ENTRY#0,0,0,0,0,0#0,0,0,0,0,0]0,0\r\n")
		return self.__make_list_dict(r.text)

	def get_lte_info(self):
		self.__check_login_status()
		r = self.session.post(f'{self.cgi_url}?1', data="[LTE_NET_STATUS#2,1,0,0,0,0#0,0,0,0,0,0]0,0\r\n")
		return self.__make_dict(r.text)

	def get_device_info(self):
		self.__check_login_status()
		r = self.session.post(f'{self.cgi_url}?1', data="[IGD_DEV_INFO#0,0,0,0,0,0#0,0,0,0,0,0]0,0\r\n")
		return self.__make_dict(r.text)

	def get_wan_lte_config(self):
		self.__check_login_status()
		r = self.session.post(f'{self.cgi_url}?1', data="[WAN_LTE_INTF_CFG#2,0,0,0,0,0#0,0,0,0,0,0]0,0\r\n")
		return self.__make_dict(r.text)

	def get_wan_ip_connection(self):
		self.__check_login_status()
		r = self.session.post(f'{self.cgi_url}?1', data="[WAN_IP_CONN#2,1,1,0,0,0#0,0,0,0,0,0]0,0\r\n")
		return self.__make_dict(r.text)

	def get_log(self):
		self.__check_login_status()
		r = self.session.get(f'{self.cgi_url}/log')
		return r.text.splitlines()

	def get_sms(self):
		self.__check_login_status()
		r = self.session.post(f'{self.cgi_url}?2&5', data="[LTE_SMS_RECVMSGBOX#0,0,0,0,0,0#0,0,0,0,0,0]0,1\r\nPageNumber=1\r\n[LTE_SMS_RECVMSGENTRY#0,0,0,0,0,0#0,0,0,0,0,0]1,5\r\nindex\r\nfrom\r\ncontent\r\nreceivedTime\r\nunread\r\n")
		return self.__make_list_dict(r.text)

	def delete_sms(self, idx):
		self.__check_login_status()
		r = self.session.post(f'{self.cgi_url}?4', data=f"[LTE_SMS_RECVMSGENTRY#{idx},0,0,0,0,0#0,0,0,0,0,0]0,0\r\n")

	def send_sms(self, to, message):
		self.__check_login_status()
		self.session.post(f'{self.cgi_url}?2', data=f"[LTE_SMS_SENDNEWMSG#0,0,0,0,0,0#0,0,0,0,0,0]0,3\r\nindex=1\r\nto={to}\r\ntextContent={message}\r\n")

	def reboot(self):
		self.__check_login_status()
		self.session.post(f'{self.cgi_url}?7', data="[ACT_REBOOT#0,0,0,0,0,0#0,0,0,0,0,0]0,0\r\n")

	def logout(self):
		self.__check_login_status()
		self.session.post(f'{self.cgi_url}?8', data="[/cgi/clearBusy#0,0,0,0,0,0#0,0,0,0,0,0]0,0\r\n")
		self.session.post(f'{self.cgi_url}?8', data="[/cgi/logout#0,0,0,0,0,0#0,0,0,0,0,0]0,0\r\n")
		del self.session.headers["TokenID"]
