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

process.on \uncaughtException, (e) !->
  console.error "uncaughtException: #{e}"

server.on \connection, (socket) !->
  socket
  .on \error, (e) !->
    console.error e.message
  .on \message, (data) !->

    msg = try
      JSON.parse data
    catch
      console.error e.message
    return unless msg

    msg.time = dateformat new Date, 'yyyy/mm/dd HH:MM:ss'

    console.log msg

    chunk = try
      JSON.stringify msg
    catch
      console.error e.message
    return unless chunk

    server.clients.forEach (client) ->
      client?.send chunk
