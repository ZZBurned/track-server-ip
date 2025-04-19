#!/bin/env python3
# 获取本机公网IPv6并通过邮箱发送
#

import email
import os
import smtplib
import subprocess

def get_v6_popen() -> list:
	output = subprocess.Popen(['ip', 'a'], stdout=subprocess.PIPE).communicate()
	lines = output[0].decode().split('\n')
	ipv6addr = []
	for line in lines:
		if line.strip().startswith('inet6 2'):
			ip6begin = line.find('2')
			ip6end = line.find('/')
			ipv6addr.append(line[ip6begin:ip6end])
	return ipv6addr
# 通过字符串出来ip命令输出获取本机公网IPv6地址

def check_v6_change(ipv6addr: list, logfile:str) -> bool:
	if not os.path.exists(logfile):
		print('Init IPv6 Address')
		return True
	with open(logfile, 'r') as f:
		lines = f.read().strip().split('\n')
		if len(ipv6addr) != len(lines):
			print('More or Less Address')
			return True
		for i in range(len(lines)):
			if ipv6addr[i] != lines[i]:
				print('Get Diff Address')
				return True
	return False

def send_email(ipv6addr: list, mail_config:dict) -> bool:
	message = email.message.EmailMessage()
	message['From'] = mail_config["sender"]
	message['Subject'] = mail_config["subject"]
	message['To'] = mail_config["receivers"]
	message.set_content('\n'.join(ipv6addr))
	print("message is:\n", message.as_string())
	smtp_ssl = smtplib.SMTP_SSL(mail_config["host"])	# default port 465
	smtp_ssl.set_debuglevel(1)
	smtp_ssl.login(mail_config["user"], mail_config["password"])
	smtp_ssl.sendmail(mail_config["sender"], mail_config["receivers"], message.as_string())
	return True
# send global IPv6 address to the E-mail via smtp+ssl

def cache_v6addr(ipv6addr: list, logfile:str):
	with open(logfile, 'w') as f:
		f.write('\n'.join(ipv6addr))

if __name__ == '__main__':
	config = dict()
	config["log_file"] = "last_v6.txt"
	mail_config = dict()
	mail_config["host"] = "mail.example"
	mail_config["user"] = "username@mail.example"
	mail_config["password"] = "SMTP专门密码"
	mail_config["sender"] = mail_config["user"]
	mail_config["receivers"] = [mail_config["user"]]	# 收件人列表
	mail_config["subject"] = "Global IPv6"
	config["mail_config"] = mail_config
	ipv6s = get_v6_popen()
	if ipv6s and check_v6_change(ipv6s, config['log_file']) and send_email(ipv6s, mail_config):
		cache_v6addr(ipv6s, config['log_file'])
	# 缓存当前发送成功的ipv6地址
