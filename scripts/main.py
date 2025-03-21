from prometheus_client import start_http_server
import time

def main():
    # Start metrics server
    start_http_server(9090)
    
    # Rest of your application... 