""" TCP client connection.
"""
import asyncio
import json
import unittest

from server.defs import SERVER_PORT, Result

SERVER_ADDR = '127.0.0.1'
# SERVER_ADDR = 'wgforge-srv.wargaming.net'
# SERVER_ADDR = '10.128.106.149'
# SERVER_PORT = 443


def run_in_foreground(task):
    """Runs event loop in current thread until the given task completes

    Returns the result of the task.
    For more complex conditions, combine with asyncio.wait()
    To include a timeout, combine with asyncio.wait_for()
    """
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(asyncio.ensure_future(task, loop=loop))


class ServerConnection(unittest.TestCase):
    """ Connection object.
    """
    def __init__(self):
        super(ServerConnection, self).__init__()
        self._loop = None
        self._reader = None
        self._writer = None
        run_in_foreground(self.connect_to_server())

    def __del__(self):
        self._writer.close()
        # self._loop.close()

    def verify(self):
        self.assertIsNotNone(self._loop)
        self.assertIsNotNone(self._reader)
        self.assertIsNotNone(self._writer)

    async def send_action(self, action: int, data, is_raw=False):
        """ Sends action command and returns result and message in string.
        """
        self._writer.write(action.to_bytes(4, byteorder='little'))
        if data is not None:
            if is_raw:
                message = data
            else:
                message = json.dumps(data, sort_keys=True, indent=4)
            self._writer.write(len(message).to_bytes(4, byteorder='little'))
            self._writer.write(message.encode('utf-8'))

        data = await self._reader.read(4)
        result = Result(int.from_bytes(data[0:4], byteorder='little'))
        data = await self._reader.read(4)
        msg_len = int.from_bytes(data[0:4], byteorder='little')
        message = ''
        if msg_len != 0:
            data = await self._reader.read(msg_len)
            while len(data) < msg_len:
                data += await self._reader.read(msg_len - len(data))
            message = data.decode('utf-8')
        return result, message

    async def connect_to_server(self):
        """ Get reader and writer.
        """
        self._loop = asyncio.get_event_loop()
        self._reader, self._writer = await asyncio.open_connection(
            SERVER_ADDR, SERVER_PORT, loop=self._loop)

    def do_action(self, action, data):
        return run_in_foreground(
            self.send_action(action, data)
        )

    def do_action_raw(self, action: int, json_str: str):
        return run_in_foreground(
            self.send_action(action, json_str, is_raw=True)
        )
