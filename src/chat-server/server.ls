# WebSocket chat server

require! {
  ws: \websocket.io
  \dateformat
}

host = '0.0.0.0'
port = 6789

server = ws.listen port, !->
  console.log "\033[96m Server running #{host}:#{port} \033[39m"
,  do
  host: host

server.on \connection, (socket) !->
  socket
  .on \error, (e) !->
    console.dir e
  .on \message, (data) !->
    msg = JSON.parse data
    msg.time = dateformat new Date, 'yyyy/mm/dd HH/MM/ss'

    console.log "\033[96m message recv \033[39m"
    console.dir msg

    chunk = JSON.stringify msg

    server.clients.forEach (client) ->
      client?.send chunk