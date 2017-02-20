"REST API for Pombru brewer"
from flask import Flask
from flask_restful import Api, Resource, reqparse, abort
import logging
import brewery
import devices
import recipes

BASE = '/pombru/api/v1'

class JamMakerApi(Resource):
    "Represents a REST API endpoint for a modified jam maker."

    parser = reqparse.RequestParser()
    parser.add_argument('mode')
    parser.add_argument('target', required=False)

    def __init__(self, jammaker):
        self.jammaker = jammaker

    def get(self):
        ret = {
            'mode': self.jammaker.get_mode(),
            'current': self.jammaker.get_temperature()
        }
        if self.jammaker.get_mode() == 'controlled':
            ret['target'] = self.jammaker.get_target_temperature()
        return ret

    def put(self):
        args = JamMakerApi.parser.parse_args()
        new_mode = args['mode']
        if new_mode == 'controlled':
            new_target = float(args['target'])
            self.jammaker.set_temperature(new_target)
        elif new_mode == 'on':
            self.jammaker.on()
        elif new_mode == 'off':
            self.jammaker.off()
        else:
            abort(400)
        return self.get()

class RelayApi(Resource):
    "Represents a REST api for a relay."

    parser = reqparse.RequestParser()
    parser.add_argument('status')

    def __init__(self, relay):
        self.relay = relay

    def get(self):
        onoff = 'on' if self.relay.get_value() else 'off'
        return {'status': onoff}

    def put(self):
        args = RelayApi.parser.parse_args()
        new_status = args['status']
        if new_status == 'on':
            self.relay.on()
        elif new_status == 'off':
            self.relay.off()
        else:
            abort(400)
        return self.get(), 202

class ProcessApi(Resource):
    "Represents a REST API for a Pombru Brewery Process."

    parser = reqparse.RequestParser()
    parser.add_argument('command')
    parser.add_argument('continue_with_stage', required=False)

    def __init__(self, process):
        self.process = process

    def get(self):
        status, stage, stagetime, processtime = self.process.get_status()
        return {'status': status, 'current_stage': stage['name'], 'stage_remaining': stagetime, 'process_remaining': processtime}

    def put(self):
        args = ProcessApi.parser.parse_args()
        command = args["command"]
        if command == "start":
            self.process.start()
        elif command == "stop":
            self.process.stop()
        elif command == "pause":
            self.process.pause()
        elif command == "continue":
            self.process.cont()
        elif command == "continue_with":
            target = args["stage"]
            self.process.cont_with(target)

class TWValveApi(Resource):
    "REST api for two-way valves."

    parser = reqparse.RequestParser()
    parser.add_argument('target')

    def __init__(self, twvalve):
        self.twvalve = twvalve

    def get(self):
        return {"target": self.twvalve.get_direction_name()}

    def put(self):
        args = TWValveApi.parser.parse_args()
        new_target = args["target"]
        self.twvalve.set_direction_name(new_target)

class PombruRestApi(object):
    """Representation of Pombru REST API.
    Following devices should be passed:
    - mashtun
    - boiler
    - mashvalve
    - boilervalve
    - mashpump
    - temppump
    - boilerpump
    """

    def __init__(self, brewery):
        self._app = Flask("pombru")
        self._api = Api(self._app)
        self._brewery = brewery
        self._api.add_resource(JamMakerApi, BASE + '/mashtun', endpoint='mashtun', resource_class_kwargs={'jammaker': brewery.mashtun})
        self._api.add_resource(JamMakerApi, BASE + '/boiler', endpoint='boiler', resource_class_kwargs={'jammaker': brewery.boiler})
        self._api.add_resource(RelayApi, BASE + '/mashtunpump', endpoint='mashtunpump', resource_class_kwargs={'relay': brewery.mashtunpump})
        self._api.add_resource(RelayApi, BASE + '/temppump', endpoint='temppump', resource_class_kwargs={'relay': brewery.temppump})
        self._api.add_resource(RelayApi, BASE + '/boilerpump', endpoint='boilerpump', resource_class_kwargs={'relay': brewery.boilerpump})
        self._api.add_resource(ProcessApi, BASE + '/process', resource_class_kwargs={'process': brewery.process})
        self._api.add_resource(TWValveApi, BASE + '/mashtunvalve', endpoint="mashtunvalve", resource_class_kwargs={'twvalve': brewery.mashtunvalve})
        self._api.add_resource(TWValveApi, BASE + '/boilervalve', endpoint="boilervalve", resource_class_kwargs={'twvalve': brewery.boilervalve})

    def start(self):
        self._app.run()

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(message)s')
    r = recipes.Recipe(mash_stages=[(50, 1), (64, 1), (68, 1), (74, 1)], boiling_time=1, mash_water=1, sparge_water=1)
    b = brewery.Brewery(r)
    PombruRestApi(b).start()
