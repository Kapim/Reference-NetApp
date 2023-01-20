import time
import cv2
import requests
from requests import HTTPError
import socketio
from collections.abc import Callable
import numpy as np
from era_5g_netapp_client.middleware_resource_checker import MiddlewareResourceChecker
from era_5g_netapp_interface.common import get_logger
import logging

logger = get_logger(logging.INFO)

class FailedToConnect(Exception):
    """
    Exception which is raised when the client could not connect to the NetApp or Middleware.
    """
    pass

class FailedToObtainPlan(Exception):
    """
    Exception which is raised when the client could not get the plan from the Middleware.
    """
    pass


class NetAppNotReady(Exception):
    """
    Raised when an operation was requested on NetApp which is not ready.
    """

class NetAppClient():
    """
    Basic implementation of the NetApp client. It creates the Requests 
    object with session and bind callbacks for connection info 
    and results from the NetApp.
    """

    def __init__(self, host: str, user_id: str, password: str, task_id: str, resource_lock: str, results_event: Callable, use_middleware=True, wait_for_netapp=True, netapp_uri: str = None, netapp_port: int = None) -> None:
        """Constructor

        Args:
            host (str): The IP or hostname of the middleware
            user_id (str): The middleware user's id
            password (str): The middleware user's password
            task_id (str): The ID of the NetApp to be deployed
            resource_lock (str): TBA
            results_event (Callable): callback where results will arrive
            use_middleware (bool, optional): Defines if the NetApp should be deployed by middleware. 
                If False, the netapp_uri and netapp_port need to be defined, otherwise, 
                they need to be left None. Defaults to True.
            netapp_uri (str, optional): The URI of the NetApp interface. Defaults to None.
            netapp_port (int, optional): The port of the NetApp interface. Defaults to None.
        
        Raises:
            FailedToConnect: When connection to the middleware could not be setupped or 
                login failed
            FailedToObtainPlan: When the plan was not sucessfully returned from
                the middleware
        """

        # temporary removed asserts until the middleware will provide neccessary info

        # if middleware is used, the netapp_uri and port should be obtained from it
        #assert use_middleware and not netapp_uri and not netapp_port
        # if middleware is not used, the netapp_uri and port needs to be provided
        #assert not use_middleware and netapp_uri and netapp_port

        self.num_steps = 0
        self.action_seq_ids = []


        self.sio = socketio.Client()
        self.s = requests.session()
        self.host = host.rstrip('/')
        self.resource_lock = resource_lock
        self.netapp_host = netapp_uri
        self.netapp_port = netapp_port
        self.use_middleware = use_middleware
        self.sio.on("message", results_event, namespace='/results')
        self.sio.on("connect", self.on_connect_event, namespace='/results')
        self.sesion_cookie = None
        self.plan = None
        self.action_plan_id = None
        self.resource_checker = None
        self.user_id = user_id
        self.password = password
        self.task_id = task_id
        self.token = None
        self.wait_for_netapp = wait_for_netapp
        if self.use_middleware:
            self.connect_to_middleware()

        
    def connect_to_middleware(self):
        try:            
            # connect to the middleware
            self.token = self.gateway_login(self.user_id, self.password)

            self.plan = self.gateway_get_plan(self.task_id, self.resource_lock)  # Get the plan by sending the token and TaskId

            self.resource_checker = MiddlewareResourceChecker(logger, "resource_checker", self.token, self.action_plan_id, self.build_middleware_api_endpoint("orchestrate/orchestrate/plan"))
            self.resource_checker.start(daemon=True)
            if self.use_middleware and self.wait_for_netapp:
                self.wait_until_netapp_ready()
                print(self.resource_checker.is_ready())
                self.load_netapp_uri()
            print('Feedback: Got new plan successfully.')
        except Exception as ex:
            self.deleteAllResources()
            raise ex

    
        
    def register(self, args=dict()) -> str:
        """
        Calls the /register endpoint of the NetApp interface and if the 
        registration is successful, it setups the WebSocket connection
        for results retrieval.

        Args:
            args (_type_, optional): optional parameters to be passed to 
            the NetApp. Defaults to dict().

        Returns:
            str: response from the NetApp
        """
        if self.use_middleware and not self.resource_checker.is_ready:
            raise NetAppNotReady

        resp = self.s.get(self.build_netapp_api_endpoint("register"), params=args)
        self.session_cookie = resp.cookies["session"]

        # creates the WebSocket connection
        self.sio.connect(self.build_netapp_api_endpoint(""), namespaces=['/results'], headers={'Cookie': f'session={self.session_cookie}'})
        return resp        

    def disconnect(self):
        """
        Calls the /unregister endpoint of the server and disconnects the 
        WebSocket connection.
        """
        if self.netapp_host is not None and self.netapp_port is not None:
            self.s.get(self.build_netapp_api_endpoint("unregister"))
        self.sio.disconnect()
        if self.use_middleware:
            self.deleteAllResources()
 

    def build_middleware_api_endpoint(self, path: str):
        """
        Builds an API endpoint on the NetApp interface.

        Args:
            path (str): endpoint path

        Returns:
            _type_: complete URI to requested endpoint
        """
        return f"http://{self.host}/{path}"

    def build_netapp_api_endpoint(self, path: str):
        """
        Builds an API endpoint on the NetApp interface.

        Args:
            path (str): endpoint path

        Returns:
            _type_: complete URI to requested endpoint
        """
        return f"http://{self.netapp_host}:{self.netapp_port}/{path}"
    

    def wait(self):
        """
        Blocking infinite waiting.
        """
        self.sio.wait()

    def on_connect_event(self):
        """
        The callback called once the connection to the NetApp is made.
        """
        print("Connected to server")

    def send_image(self, frame: np.ndarray, timestamp:str = None):
        """
        Encodes the received image frame to the jpg format and sends
        it over the HTTP, to the /image endpoint.

        Args:
            frame (np.ndarray): image frame
            timestamp (str, optional): frame timestamp The timestamp format
            is defined by the NetApp. Defaults to None.
        """
        _, img_encoded = cv2.imencode('.jpg', frame)
        headers = {'content-type': 'image/jpeg'}
        self.s.post(self.build_netapp_api_endpoint("image"), data=img_encoded.tostring(), 
            headers=headers, params={"timestamp": timestamp})

    def wait_until_netapp_ready(self):
        self.resource_checker.wait_until_resource_ready()

    def load_netapp_uri(self):
        if not self.resource_checker.is_ready():
            raise NetAppNotReady
        self.netapp_host = self.resource_checker.url
        self.netapp_port = "5896"

    def gateway_login(self,ID,PASSWORD):
        print("Trying to log into the middleware")
        # Request Login
        try:
            r = requests.post(self.build_middleware_api_endpoint("Login"), json={"Id": ID, "Password": PASSWORD})
            response = r.json()
            if "errors" in response:
                raise FailedToConnect(str(response["errors"]))
            newToken = (response['token'])  # Token is stored here
            #time.sleep(10)
            return newToken

        except requests.HTTPError as e:
            raise FailedToConnect(f"Could not login to the middleware gateway, status code: {e.response.status_code}")
        except KeyError as e:
            raise FailedToConnect(f"Could not login to the middleware gateway, the response does not contain {e}")

        
    def gateway_get_plan(self, taskid, resource_lock):
        # Request plan
        try:
            print("Goal task is: "+str(taskid))
            hed = {'Authorization': f'Bearer {str(self.token)}'}
            data = {"TaskId": str(taskid), "LockResourceReUse": resource_lock}
            response = requests.post(self.build_middleware_api_endpoint("Task/Plan"), json=data, headers=hed).json()
            if "statusCode" in response and (response["statusCode"] == 500 or response["statusCode"] == 400):
                raise FailedToConnect(f"response {response['statusCode']}: {response['message']}")
            
            action_sequence = response['ActionSequence']
            #print(action_sequence)
            self.action_plan_id = response['ActionPlanId']
            print("ActionPlanId ** is: " + str(self.action_plan_id))


            self.num_steps = len(action_sequence)

            for x in range(0, self.num_steps):  # Iterate over all the actions within the action sequence and get their ids.
                Action_SequenceFullData = action_sequence[x]
                print('Subaction task id: '+Action_SequenceFullData['Id'])
                self.action_seq_ids.append(Action_SequenceFullData['Id'])

            return response
        except KeyError as e:
            raise FailedToConnect(f"Could not get the plan, the response does not contain {e}")


    def deleteAllResources(self):
        if self.token is None or self.action_plan_id is None:
            return

        try:
            hed = {'Authorization': 'Bearer ' + str(self.token)}
            url = self.build_middleware_api_endpoint(f"orchestrate/orchestrate/plan/{str(self.action_plan_id)}")
            response = requests.delete(url, headers=hed)

            if '200' in str(response):
                print('Resource deleted')

        except HTTPError as e:
            print(e.response.status_code)
            return 'Error, could not get delete the resource, revisit the log files for more details.'

    def deleteSingleResource(self):
        raise NotImplemented #TODO

    
    def gatewayLogOff(self):
        print('Middleware log out succesful ')
        #TODO
        pass

