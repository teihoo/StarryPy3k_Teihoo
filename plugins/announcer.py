import asyncio

from base_plugin import BasePlugin
from utilities import broadcast


class Announcer(BasePlugin):
    name = "announcer"

    @asyncio.coroutine
    def send_announce(self, protocol, message):
        broadcast(self.factory, "%s %s" % (protocol.player.name, message))

    def on_connect_response(self, data, protocol):
        if data['parsed']['success']:
            asyncio.Task(self.send_announce(protocol, "joined."))
        return True

    def on_client_disconnect(self, data, protocol):
        asyncio.Task(self.send_announce(protocol, "left."))
        return True
