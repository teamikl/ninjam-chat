
port = 6790
proxy = require \http-proxy

server = proxy.create-server do
  target: \ws://localhost:6789
  ws: true
.listen port
