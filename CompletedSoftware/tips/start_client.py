from textual_serve.server import Server

server = Server("python client.py", port=8001, host="192.168.0.5") 
server.serve()