from era_5g_netapp_client.data_sender_gstreamer import DataSenderGStreamer
from era_5g_netapp_client.client_gstreamer import NetAppClientGstreamer
from era_5g_netapp_client.client import FailedToConnect


def main():

    server_ip = "butcluster.ddns.net"  
    
    try:
        client = NetAppClientGstreamer(server_ip, 5896)
        client.register()
        #sender = DataSenderGStreamer(server_ip, server_port, "v4l2src device=/dev/video0")
        sender = DataSenderGStreamer(server_ip, client.gstreamer_port, "videotestsrc")
        client.wait()
    except FailedToConnect as ex:
        print(f"Failed to connect to server ({ex})")
    except KeyboardInterrupt:
        client.disconnect()   



if __name__ == '__main__':
    main()
