import json

server_config={"ipv4_addr":"0.0.0.0",
        "port":14514
        }

_config_name="server_config.json"

try:
    f=open(_config_name,"r")
    server_config.update(json.loads(f.read()))
except (FileNotFoundError,json.decoder.JSONDecodeError):
    f=open(_config_name,"w")
    f.write(json.dumps(server_config,indent=4))
    f.close()
    