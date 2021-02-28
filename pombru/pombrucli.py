import argparse
import requests

API_BASE = "http://localhost:5000/pombru/api/v1"
CT_FORM = {"Content-Type": "application/x-www-form-urlencoded"}

def jammaker_command(jammaker, command, parameter=None):
    url = API_BASE + "/" + jammaker
    res = None
    data = ''
    if command == 'on':
        res = requests.put(url, headers=CT_FORM, data="mode=on")
    elif command == 'off':
        res = requests.put(url, headers=CT_FORM, data="mode=off")
    elif command == 'status':
        res = requests.get(url)
    elif command == 'target':
        res = requests.put(url, headers=CT_FORM, data="mode=controlled&target=" + str(parameter))
        data="mode=controlled&target=" + str(parameter)
    print(data)
    print(res.json() if res is not None else "ERR: unknown command '" + command + "'")

def process_command(command, stage=None):
    url = API_BASE + "/process"
    res = None
    def processput(par1, par2=None):
        data = par1
        if par2 is not None:
            data = data + '&' + par2
        return requests.put(url, headers=CT_FORM, data=data)
    if command == 'status':
        res = requests.get(url)
    elif command in ['start', 'stop', 'pause', 'continue', 'next']:
        res = processput('command=' + command)
    elif command == 'continue_with':
        res = processput('command=continue_with', 'stage=' + stage)

    print(res.json() if res is not None else "ERR: unknown command '" + command + "'")

def all_command(command):
    if command == 'status':
        print("PROCESS:")
        process_command('status')
        print("MASH TUN:")
        jammaker_command('mashtun', 'status')
        twvalve_command('mashtunvalve', 'status')
        pump_command('mashtunpump', 'status')
        print("BOILER:")
        jammaker_command('boiler', 'status')
        twvalve_command('boilervalve', 'status')
        pump_command('boilerpump', 'status')
        print("TEMPORARY:")
        pump_command('temppump', 'status')

def twvalve_command(valve, command, target=None):
    url = API_BASE + "/" + valve
    res = None
    if command == 'status':
        res = requests.get(url)
    elif command == 'target':
        res = requests.put(url, headers=CT_FORM, data="target=" + target)
    print(res.json() if res is not None else "ERR: unknown command '" + command + "'")

def pump_command(pump, command):
    url = API_BASE + '/' + pump
    res = None
    if command == 'status':
        res = requests.get(url)
    elif command == 'on':
        res = requests.put(url, headers=CT_FORM, data="status=on")
    elif command == 'off':
        res = requests.put(url, headers=CT_FORM, data="status=off")
    print(res.json() if res is not None else "ERR: unknown command '" + command + "'")

def config_command(command):
    url = API_BASE + '/config'
    res = None
    if command == 'get':
        res = requests.get(url)
    elif command == 'reload':
        res = requests.put(url)
    print(res.json() if res is not None else "ERR: unknown command '" + command + "'")

def notify_command(command):
    url = API_BASE + '/notify'
    res = None
    if command == 'status':
        res = requests.get(url)
    elif command == 'start':
        res = requests.put(url, headers=CT_FORM, data='command=start')
    elif command == 'stop':
        res = requests.put(url, headers=CT_FORM, data='command=stop')
    else:
        print("Unknown command: " + str(command))
        return
    print(res.json() if res is not None else "ERR: unknown command '" + command + "'")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("object", help="The object on which the command is executed")
    parser.add_argument("command", help="The command to execute on object")
    parser.add_argument("--temperature", required=False, type=int, help="Temperature when setting a jam maker's temperature.")
    parser.add_argument("--stage", required=False, type=str, help="Target stage when continuing the process.")
    parser.add_argument("--target", required=False, help="Target for a two-way valve (mashtun or temporary)")
    args = parser.parse_args()

    o = args.object
    c = args.command
    if o in ['mashtun', 'boiler']:
        jammaker_command(o, c, args.temperature)
    elif o == 'process':
        process_command(c, args.stage)
    elif o == 'all':
        all_command(c)
    elif o in ['mashtunvalve', 'boilervalve']:
        twvalve_command(o, c, args.target)
    elif o in ['mashtunpump', 'boilerpump', 'temppump']:
        pump_command(o, c)
    elif o == 'config':
        config_command(c)
    elif o == 'notify':
        notify_command(c)

if __name__ == "__main__":
    main()
