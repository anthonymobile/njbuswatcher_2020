#!/usr/bin/env python

import sys
import urllib.request, urllib.error, urllib.parse
# import ipgetter
import xmlrpc.client

wf_account = ''           # Your WebFaction Account Name
wf_password = ''         # Your WebFaction Control Panel Password
home_domain = ''    # The Domain to update (must exist in the Control Panel)

server = xmlrpc.client.ServerProxy('https://api.webfaction.com/')
(session_id, account) = server.login(wf_account, wf_password)

home_override = None
for override in server.list_dns_overrides(session_id):
    if override['domain'] == home_domain:
        home_override = override
        break

# my_ip = ipgetter.myip()
my_ip = urllib.request.urlopen('https://ident.me').read().decode('utf8')

if home_override and home_override['a_ip'] == my_ip:
    sys.exit(0)

if home_override:
    server.delete_dns_override(session_id, home_domain, home_override['a_ip'])

server.create_dns_override(session_id, home_domain, my_ip)
