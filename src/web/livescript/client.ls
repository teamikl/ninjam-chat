# chat client

ws-config = new
  @host = \localhost
  @port = 6789

user-name-key = \ninjam-chat-app-user-name
storage = local-storage
user-name = if storage? then storage.get-item user-name-key, "" else ""


function not-empty(line)
  line

function escape-html(text)
  $('<div>').text(text).html!

function format-chat-message(msg)
  msg.split(/(?:\r|\n|\r\n)/).filter(not-empty).map(escape-html).join('<br>')


$ !->
  if user-name
    init!
  else
    bootbox.prompt "Name: ", (name) !->
      user-name := if name then name else 'Guest' + Math.floor Math.random! * 100
      storage?.set-item user-name-key, user-name
      init!

!function init
  close_button = ->
    $ '<button/>' .addClass \close .attr {type: \button, 'data-dismiss': \alert} .append \x

  ws = new WebSocket("ws://#{ws-config.host}:#{ws-config.port}/")
  ws.onerror = (e) !->
    $(\#chat-area).empty!
      .addClass 'alert alert-error'
      .append close_button!, $('<i/>').addClass(\fa.fa-warning), 'Could not connect to server'

  ws.onopen = !->
    # NOTE: ws still connection state, 'send' fail
    $(\#text-box).focus!
    ws.send JSON.stringify do
      type: \join
      user: user-name

  ws.onmessage = (evt) !->
    return if evt.data.length <= 0

    data = JSON.parse evt.data
    item = $('<li/>').append \
      $('<div/>').append \
        $('<i/>').addClass('fa fa-user'),
        $('<small/>').addClass('meta chat-time').append(data.time)

    switch data.type
    | \join =>
      item.addClass 'alert alert-info'
        .prepend close_button!
        .children \div .children \i .after " #{data.user} join a room"
    | \chat =>
      item.addClass 'well well-small'
        .append $('<div/>').html format-chat-message(data.text)
        .children \div .children \i .after " #{data.user}"
    | \part =>
      item.addClass 'alert alert-warning'
        .prepend close_button!
        .children \div .children \i .after " #{data.user} left a room"
    | otherwise =>
      item.addClass 'alert alert-error'
        .children \div .children \i .removeClass 'fa fa-user' .addClass '\fa fa-warning'
        .after 'Recv invalid message'

    $(\#chat-history).prepend (item .hide! .fadeIn 1000)

  text-box = $(\#text-box)

  send_message = !->
    return if text-box.val!.length <= 0
    ws.send JSON.stringify do
      type: \chat
      user: user-name
      text: text-box.val!
    text-box.val ''

  $(\#user-name)
   ..append user-name
   ..on \click (evt) !->
      console.log this
      $(this).attr contenteditable: true
   ..on \keypress (evt) ->
      if (evt.which is 13 or evt.keyCode is 13)
        $(\#text-box).focus!
        false
   ..focusout (evt) !->
     name = $(this).text!.replace /(\s)/g, ''
     if name
       user-name := name
       storage?.set-item user-name-key, user-name
     else
       $(this).text user-name
     $(\#user-name).attr contenteditable: false

  $(text-box).on \keypress, (evt) ->
    if (evt.which is 13 or evt.keyCode is 13)
      send_message!
      false

  $(\#send-button).click (evt) !-> send_message!

  window.onbeforeunload = !->
    ws.send JSON.stringify do
      type: \part
      user: user-name
