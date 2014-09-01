# WebSocket chat server

require! {
  ws: \websocket.io
  \dateformat
}

server = ws.listen 6789 !->
  console.log '\033[96m Server running localhost:6789 \033[39m'

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