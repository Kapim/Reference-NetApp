import requests
import socketio


class FailedToConnect(Exception):
    pass


class NetAppClient():


    def __init__(self, host: str, port) -> None:
        self.sio = socketio.Client()
        self.s = requests.session()
        self.host = host.rstrip('/')
        self.port = port
        self.sio.on("message", self.results_event, namespace='/results')
        self.sio.on("connect", self.on_connect, namespace='/results')
        
    def register(self) -> str:
        resp = self.s.get(self.build_api_endpoint("register"))
        session_cookie = resp.cookies["session"]
    
        self.sio.connect(self.build_api_endpoint(""), namespaces=['/results'], headers={'Cookie': f'session={session_cookie}'})
        return resp
        

    def disconnect(self):
        self.s.get(self.build_api_endpoint("unregister"))
        self.sio.disconnect()
 
    def results_event(self, data):
        print(data)
 
    def on_connect(self):
        print("I'm connected to the /results namespace!")

    def build_api_endpoint(self, path: str): 
        return f"http://{self.host}:{self.port}/{path}"

    def wait(self):
        self.sio.wait()


