#!/usr/bin/env python3

import logging
import secrets
from queue import Queue
from worker import FaceDetector

import flask_socketio
from era_5g_netapp_interface import \
    TaskHandlerGstreamerInternalQ as TaskHandler
from era_5g_netapp_interface.common import get_logger
from flask import Flask, Response, request, session

from flask_session import Session

app = Flask(__name__)

app.secret_key = secrets.token_hex()
app.config['SESSION_TYPE'] = 'filesystem'

Session(app)
socketio = flask_socketio.SocketIO(app, manage_session=False, async_mode='threading') 

free_ports = [5001, 5002, 5003]
tasks = dict()

image_queue = Queue(1024)

logger = get_logger(log_level=logging.INFO)

@app.route('/register', methods=['GET'])
def register():
    """
    Needs to be called before an attempt to open WS is made.
    :return:
    """
    global logger
    if not free_ports:
        return {"error": "Not enough resources"}, 503
    port = free_ports.pop(0)

    session['registered'] = True
    task = TaskHandler(logger, session.sid, None, port, image_queue)
     
    tasks[session.sid] = task
    print(f"Client registered: {session.sid}")
    return {"port": port}, 200


@app.route('/unregister', methods=['GET'])
def unregister():
    session_id = session.sid

    if session.pop('registered', None):
        task = tasks.pop(session.sid)
        flask_socketio.disconnect(task.websocket_id, namespace="/results")
        free_ports.append(task.port)
        task.stop()
        print(f"Client unregistered: {session_id}")

        
    return Response(status=204)


@socketio.on('connect', namespace='/results')
def connect(auth):

    if 'registered' not in session:
        raise ConnectionRefusedError('Need to call /register first.')

    sid = request.sid

    print('connect ', sid)
    print(f"Connected. Session id: {session.sid}, ws_sid: {sid}")
    tasks[session.sid].websocket_id = sid
    tasks[session.sid].start(daemon=True)
    flask_socketio.send("you are connected", namespace='/results', to=sid)


@socketio.event
def disconnect(sid):
    print('disconnect ', sid)


def main(args=None):
    global image_queue

    
    # Create detector
    detector_thread = FaceDetector(logger, "Detector", image_queue, app)
    detector_thread.start(daemon=True)
    
    # Estimate new queue size based on maximum latency
    """avg_latency = latency_measurements.get_avg_latency() # obtained from detector init warmup
    if avg_latency != 0:  # warmup can be skipped
        new_queue_size = int(max_latency / avg_latency)
        image_queue = Queue(new_queue_size)
        detector_thread.input_queue = image_queue"""
    
   

    socketio.run(app, port=5896, host='0.0.0.0')
    


if __name__ == '__main__':
    main()
