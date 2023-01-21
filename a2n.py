#!/usr/bin/python3

import sys

# Faux sanity check
if len(sys.argv) > 3:
    print("Converting file: " + sys.argv[1])
    site = sys.argv[1]
    apache_path = sys.argv[2]
    nginx_path = sys.argv[3]
    nginx_site = site.replace(".conf","").replace("-le-ssl","").replace("-ssl","")
else:
	print("Please provide input arguments.")\
    print("Usage: a2n.py <config_file> <apache_path> <nginx_path>")

# Read Apache config
f = open(apache_path + site,'r')
lines = f.readlines()
f.close()

# Go through the apache config and identify config stuff
site_header = ""
site_name = ""
site_aliases = ""
site_root = ""
site_proxy = ""
proxy = False
for line in lines:
    if '###' in line and 'SSL' in line:
        site_header = line.strip()
    if 'ServerName' in line:
        site_name = line.split()[1]
    if 'ServerAlias' in line:
        site_name = site_name + " " + line.replace("ServerAlias ","").strip()
    if 'DocumentRoot' in line:
        site_root = line.split()[1]
    if 'ProxyPass /' in line:
    	proxy = True
    	print("Detected proxy config")
    	site_proxy = line.replace("ProxyPass / ","").strip()


# Define a basic non-proxy template
template = """\
{}

server {{
		server_name {};
		root {};
		listen 80;

		# Include some security defaults
		include security_defaults.conf;

		# index is index.php
		location / {{
			index index.php;
			try_files $uri $uri/ =404;
		}}

		# Enable PHP for the site
		location ~ \\.php?$ {{
			include php.conf;
			fastcgi_pass unix:/var/run/php/mtp-generic-7.4.sock;
			fastcgi_param PHP_ADMIN_VALUE "open_basedir={}/:/tmp/";
		}}
}}
"""

# Define a proxy template
proxy_template = """\
{}

server {{
		server_name {};
		listen 80;

		# Include some security defaults
		include security_defaults.conf;

		location / {{
        		proxy_pass			{};
        		proxy_pass_header	Server;
        		proxy_set_header	Host $host;
        		proxy_set_header	X-Real-IP $remote_addr;
        		proxy_set_header	X-Forwarded-For $remote_addr;
        		proxy_buffering		off;
        		proxy_http_version	1.1;

		        # To preclude timeouts
        		proxy_connect_timeout       600;
        		proxy_send_timeout          600;
        		proxy_read_timeout          600;
        		send_timeout                600;
    	}}
}}
"""

# Output the converted config to nginx_path
f = open(nginx_path + nginx_site,'w')
if proxy:
	f.write(proxy_template.format(site_header, site_name, site_proxy))
else:
	f.write(template.format(site_header, site_name, site_root, site_root))
f.close()