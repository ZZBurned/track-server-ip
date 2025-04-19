#!/bin/env python3
# 通过服务器尚未失效的动态IPv6获取最新IPv6并更新相关配置文件
#

import datetime
import logging
import os
import sys
import subprocess

def get_ipv6_remote(command:str="ssh your-server ip -6 a") -> list:
	try:
		process = subprocess.Popen(command.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		stdout, stderr = process.communicate()

		if stderr:
			logging.warning(f"Error executing command: {stderr.decode()}")

		output = stdout.decode()
		ipv6addrs = []

		for line in output.splitlines():
			if line.strip().startswith('inet6 2'):
				ip6begin = line.find('2')
				ip6end = line.find('/')
				ipv6addrs.append(line[ip6begin:ip6end])

		logging.info(f"Find {len(ipv6addrs)} IPv6 Addresses.")
		return ipv6addrs

	except Exception as e:
		logging.error(f"get_ipv6_remote error occurred: {e}")
		return []
# 使用 subprocess 模块执行 ssh 命令获取远程服务器 IPv6 地址。

def manage_ipv6_log(ipv6addrs:list, log_file:str="ipv6_log.txt", cache_days:int=0) -> None:
	now = datetime.datetime.now()

	with open(log_file, "a") as f:
		f.write(f"{now}\t{ipv6addrs[0]}\n")
		logging.info("Write latest IPv6 address to log file.")

	if cache_days > 0:
		cutoff_date = now - datetime.timedelta(days=cache_days)

		# 清理旧的日志条目
		with open(log_file, "r") as f:
			lines = f.readlines()

		new_lines = []
		for line in lines:
			date_str = line.split("\t")[0].strip()
			try:
				date = datetime.datetime.fromisoformat(date_str)
				if date >= cutoff_date:
					new_lines.append(line)
			except Exception as e:
				logging.error(e)

		with open(log_file, "w") as f:
			f.writelines(new_lines)

	else:
		logging.info("Not clean log file.")
# 记录IPv6到日志

def get_current_ipv6(host:str, ssh_config_path:str="~/.ssh/config") -> str:
	ssh_config_path = os.path.expanduser(ssh_config_path)
	with open(ssh_config_path) as f:
		lines = f.readlines()

	for i, line in enumerate(lines):
		if line.strip().lower().startswith("host") and line.split("#")[0].strip().endswith(host):
			for j in range(i+1, len(lines)):
				line2 = lines[j].split("#")[0].strip()
				if not line2:
					break
				if line2.lower().startswith("hostname"):
					assert ":" in line2
					return line2.split()[-1]
			break

	raise ValueError(f"Not found host {host} in {ssh_config_path}.")
# 获取ssh配置中指定host的当前IPv6地址

def refresh_related_conf(host:str, new_ipv6:str, conf_list:list=["~/.ssh/config"]):
	current_ipv6 = get_current_ipv6(host)
	assert current_ipv6 and new_ipv6
	assert isinstance(conf_list, list)
	conf_list = [os.path.expanduser(path) for path in conf_list]

	if not conf_list:
		return None

	command = ["sed", "-i", f"s/{current_ipv6}/{new_ipv6}/g"] + conf_list
	logging.info(f"refresh_related_conf command: {command}")

	process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	stdout, stderr = process.communicate()
	if stderr:
		logging.error(stderr)
	return stdout
# 将相关配置文件中特定远端主机的IPv6地址更新

if __name__ == "__main__":
	logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

	if len(sys.argv) < 2 or sys.argv[1] in ["-h", "--help", "?"]:
		print(f"Usage:\n\t{sys.argv[0]} HOST config_file1 config_file2 ...")
		exit(0)
	else:
		host = sys.argv[1]
		conf_list = sys.argv[2:]

	try:
		ipv6addrs = get_ipv6_remote(f"ssh {host} ip -6 a")

		if ipv6addrs:
			print("Latest IPv6 Addresses:", ipv6addrs[0])
			manage_ipv6_log(ipv6addrs, cache_days=7)
			refresh_related_conf(host, ipv6addrs[0], conf_list)
			print("Refresh config files: ", conf_list)
		else:
			print("No IPv6 addresses found.")

	except Exception as e:
		logging.error(f"An error occurred: {e}")
		exit(1)
