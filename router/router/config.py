import jinja2
import os
import shutil
import subprocess

class Config(object):

	def __init__(self):
		self.upstreams = []
		self.servers = []
		self.nginx_config_path = os.environ.get("NGINX_CONF_PATH", "/etc/nginx/conf.d/")
		self.nginx_restart_command = os.environ.get("NGINX_RESTART", "/usr/sbin/nginx -s reload")
		self.upstream_config = self.nginx_config_path + "paas-upstreams.conf"
		self.server_config = self.nginx_config_path + "paas-servers.conf"

	def return_config(self):
		upstream_data = ""
		server_data = ""
		try:
			with open(self.upstream_config, "r") as f:
				upstream_data = f.read()
		except:
			pass

		try:
			with open(self.server_config, "r") as f:
				server_data = f.read()
		except:
			pass

		return { "upstreams": upstream_data, "servers": server_data }

	def update_config(self,data):
			print "Updating config"

			JINJA_ENVIRONMENT = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),extensions=['jinja2.ext.autoescape'],autoescape=True)

			upstream_template = JINJA_ENVIRONMENT.get_template('upstream.conf')
			server_template = JINJA_ENVIRONMENT.get_template('server.conf')

			upstreams = {}
			servers = {}
			invalid_upstreams = []

			#Generate upstreams
			if "containers" in data:
				for upstream in data['containers']:
					if data['containers'][upstream]:
						if upstream != "":
							upstreams[upstream] = data['containers'][upstream]
						#upstreams.append(upstream_template.render(name=upstream, containers = data['containers'][upstream]))
					else:
						invalid_upstreams.append(upstream)


			update_required = 0

			if "endpoints" in data:
				for server in data['endpoints']:
					locations_to_remove = []
					if server == "":
						continue
					for location in data['endpoints'][server]:
							if data['endpoints'][server][location] in invalid_upstreams:
								locations_to_remove.append(location)

					for location in locations_to_remove:
							del data['endpoints'][server][location]

					if data['endpoints'][server]:
						servers[server] = data['endpoints'][server]
						#servers.append(data['endpoints'][server])
						#servers.append(server_template.render(name=server, locations=data['endpoints'][server]))

				if self.upstreams != upstreams:
					self.upstreams = upstreams
					update_required = 1
					print "Upstreams updated"

				if self.servers != servers:
					self.servers = servers
					update_required = 1
					print "Servers updated"

			if update_required == 1:
				print "Updating config on disk"
				self.update_config_on_disk(upstreams, servers)

			return True


	def update_config_on_disk(self, upstreams, servers):

		JINJA_ENVIRONMENT = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),extensions=['jinja2.ext.autoescape'],autoescape=True)

		upstream_template = JINJA_ENVIRONMENT.get_template('upstream.conf')
		server_template = JINJA_ENVIRONMENT.get_template('server.conf')

		with open('output-upstreams.conf', 'w') as upstream_file:
			for upstream in upstreams:
				upstream_file.write(upstream_template.render(name=upstream, containers = upstreams[upstream]))
				upstream_file.write("\n")
				#upstream_file.write("\n".join(upstreams))

		with open('output-servers.conf', 'w') as server_file:
			for server in servers:
				server_file.write(server_template.render(name=server, locations=servers[server]))
				server_file.write("\n")

		#Move the files to the correct place
		subprocess.call(["pwd"])
		shutil.copy("output-upstreams.conf", self.nginx_config_path)
		shutil.copy("output-servers.conf", self.nginx_config_path)
		print "Config copied to nginx location"

		subprocess.call(self.nginx_restart_command, shell=True)
		#subprocess.Popen(self.nginx_restart_command.split(), env=None, shell=False)

		return True
