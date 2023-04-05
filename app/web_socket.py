import asyncio
import json
import logging
import threading
from json import JSONDecodeError

import websockets
from websockets.exceptions import ConnectionClosed


class WebSocketCallback:
    def on_connected(self):
        raise NotImplementedError()

    def on_disconnected(self):
        raise NotImplementedError()

    def on_update(self, event):
        raise NotImplementedError()


class WebSocketClient:
    def __init__(self):
        self._stop_future = None
        self.socket = None
        self.socket_callback = None
        self._running_thread = None

    def start(self, callback: WebSocketCallback):
        """
        Start the web socket and listen to the update from the clients.
        :param callback: the handler function for the  messages from the client. It will pass object or string based on
         the type of the original message. The second parameter indicates if the message is a JSON.
        """
        self._running_thread = threading.Thread(name="ws", target=self._start)
        self.socket_callback = callback
        self._running_thread.start()

    def stop(self):
        if self._running_thread:
            self._stop_future.set_result(True)
            self._running_thread.join()
            self._running_thread = None
            self._stop_future = None
            self.socket_callback = None

        else:
            logging.warning("The server did not start yet...")

    def send(self, message, event_type="text_update"):
        logging.debug("Send: %s" % message)
        if self.socket:
            json_string = json.dumps({
                "message": message,
                "event": event_type,
            })
            asyncio.run(self.socket.send(json_string))

    def _start(self):
        asyncio.run(self._start_server())

    async def _handle_websocket(self, websocket):

        while True:
            self.socket = websocket
            message = await websocket.recv()
            try:
                payload = json.loads(message)
                if 'event' not in payload:
                    logging.error("Invalid event received from web socket: %s" % payload)
                elif payload['event'] == 'connected':
                    self.socket_callback.on_connected()
                else:
                    self.socket_callback.on_update(payload)
            except JSONDecodeError:
                logging.error("Failed to parse websocket event")
            except ConnectionClosed:
                self.socket = None
                self.socket_callback.on_disconnected()

    async def _start_server(self):
        self._stop_future = asyncio.Future()

        async with websockets.serve(self._handle_websocket, "localhost", 8000):
            logging.debug("WebSocket server listening on ws://localhost:8000")
            await self._stop_future
