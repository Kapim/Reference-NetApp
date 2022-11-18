from .client import NetAppClient
from .client import FailedToConnect

class NetAppClientGstreamer(NetAppClient):

    def __init__(self, host: str, port) -> None:
        super().__init__(host, port)
        self.gstreamer_port = None

    def register(self) -> str:
        resp = super().register()

        if len(resp.content) > 0:
            data = resp.json()
            if "error" in data:
                err = data["error"]
                self.disconnect()
                raise FailedToConnect(f"{resp.status_code}: {err}")
            if "port" in data:
                self.gstreamer_port = data["port"]
            else:
                raise FailedToConnect(f"{resp.status_code}: could not obtain the gstreamer port number")
        
        else:
            self.disconnect()
            raise FailedToConnect(f"{resp.status_code}: unknown error")

        return resp