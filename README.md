# archer-mr400
Small Python lib for communicating with the TP-Link Archer MR400 LTE V2 router. It might work with other Archer routers as well, but the MR400 v2 is the only router I've tested it on.

This library is a work in progress and I will add more functionality as I need them.

## Dependencies
The library uses the [Pure Python RSA implementation](https://pypi.org/project/rsa/) library and the [Requests](https://pypi.org/project/requests/) library. Install them using pip:
```
pip install rsa
pip install requests
```

## Usage
1. Import the library:
```python
from archer.mr400 import MR400Client
```
2. Create the client by providing the router IP:
```python
client = MR400Client("192.168.1.1")
```
3. Start by logging in:
```python
client.login("admin", "myrouterpass")
```
4. We now have a working connection to the router and can fetch info and issue commands:
```python
client.get_wan_lte_config()
client.reboot()
```
5. When you are finished, make sure to call the `logout()` function to logout, otherwise the web interface will complain about an already logged in session if you try to log in manually.
```python
client.logout()
```

The `login()` method will raise a `ConnectionFailedException` if the connection timed out (wrong router IP?) or a `LoginFailedException` if the login was unsuccessful (wrong username or password?). Any call to the endpoint methods will raise a `NotLoggedInException` if there's no active logged in session.

The functions that fetches information will return the info in a dictionary, with the same format as the router returns the information, you will have to figure out what the different key/values stand for yourself:
```python
{
  'ussdSessionStatus': '0',
  'ussdStatus': '0',
  'smsUnreadCount': '0',
  ...
}
```

The `get_clients()` and `get_sms()` functions will return a list of dictionaries, each representing one connected client or SMS, respectively:
```python
  [
    {
      'IPAddress': '192.168.1.101',
      'addressSource': 'DHCP',
      'leaseTimeRemaining': '81922',
      'MACAddress': 'AA:BB:CC:DD:EE:FF',
      'hostName': 'MacBook-Pro-M1',
      'X_TP_ConnType': '3',
      'active': '1',
      'idx': '1'
    },
    ...
  ]
```

Check the [example.py](example.py) script for a demo on how to use the library.


## How it works
The client mimics the way that the router admin web page logs in to the router and send commands. 

The login flow looks as follows:

1. The exponent and modulus values of the router's RSA public key are fetched by calling `/cgi/getParm`. The response is in the form of a javascript snippet containing variable assignments, so the library will extract those values. 
2. Using the retrieved values a public key is created and used to encrypt the `username` and the base64-encoded representation of the `password`.
3. The encrypted username and password is posted to the router in the following url: `/cgi/login?UserName={rsa_username}&Passwd={rsa_password}&Action=1&LoginStatus=0`
4. If the login is successful, a `JSESSIONID` cookie value is set in the current session and the library follows that up with a request to get the root page of the router admin web, this is done to be able to fetch a token value that is needed together with the `JSESSIONID` in order to call the command endpoints.
5. The token value is retrieved from the returned HTML by extracting it from the following text found in the HTML response: `var token="<token>";` and is added as a header on the current session with the header name `TokenID`.
6. With the `JSESSIONID` cookie and the `TokenID` header set on the current session, the library can now call various endpoints on the router to fetch information and call actions.

## Router endpoints used
The various endpoints are called by POSTing to `http://<router_ip>/cgi?<n>` with a command payload. I have only added support for some of the endpoints, but it is easy to extend this by checking the admin web page using the developer console of the web browser and mimic the commands being sent.

The log endpoint differs in that it is called using GET and doesn't require a payload. It will dump the entire router log available.

The following endpoints are implemented in the library:
| Description | URL | Payload |
| ----------- | --- | ------- |
| Get all connected clients | `/cgi?5` | `[LAN_HOST_ENTRY#0,0,0,0,0,0#0,0,0,0,0,0]0,0` |
| Fetch LTE network status | `/cgi?1` | `[LTE_NET_STATUS#2,1,0,0,0,0#0,0,0,0,0,0]0,0` |
| Fetch device information | `/cgi?1` | `[IGD_DEV_INFO#0,0,0,0,0,0#0,0,0,0,0,0]0,0` |
| Fetch WAN LTE config | `/cgi?1` | `[WAN_LTE_INTF_CFG#2,0,0,0,0,0#0,0,0,0,0,0]0,0` |
| Fetch WAN IP connection status | `/cgi?1` | `[WAN_IP_CONN#2,1,1,0,0,0#0,0,0,0,0,0]0,0` |
| Get incoming SMS'es | `/cgi?2&5` | `[LTE_SMS_RECVMSGBOX#0,0,0,0,0,0#0,0,0,0,0,0]0,1`<br />`PageNumber=1`<br />`[LTE_SMS_RECVMSGENTRY#0,0,0,0,0,0#0,0,0,0,0,0]1,5`<br />`index`<br />`from`<br />`content`<br />`receivedTime`<br />`unread` |
| Delete an SMS | `/cgi?4` | `[LTE_SMS_RECVMSGENTRY#{idx},0,0,0,0,0#0,0,0,0,0,0]0,0` |
| Send an SMS | `/cgi?2` | `[LTE_SMS_SENDNEWMSG#0,0,0,0,0,0#0,0,0,0,0,0]0,3`<br />`index=1`<br />`to={to}`<br />`textContent={message}` |
| Fetch the router log | `/log` | `N/A` |
| Reboot the router | `/cgi?7` | `[ACT_REBOOT#0,0,0,0,0,0#0,0,0,0,0,0]0,0` |
| Logout from the router | `cgi?8` | `[/cgi/logout#0,0,0,0,0,0#0,0,0,0,0,0]0,0` |
