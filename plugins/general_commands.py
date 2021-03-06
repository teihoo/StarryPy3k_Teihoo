from base_plugin import SimpleCommandPlugin
import data_parser
import packets
from plugins.player_manager import Admin
import pparser
from utilities import send_message, Command, broadcast


class Whois(Admin):
    pass


class GiveItem(Admin):
    pass


class GeneralCommands(SimpleCommandPlugin):
    name = "general_commands"
    depends = ["command_dispatcher", "player_manager"]

    @Command("who")
    def who(self, data, protocol):
        ret_list = []
        for player in self.plugins['player_manager'].players.values():
            if player.logged_in:
                ret_list.append(player.name)
        send_message(protocol,
                     "%d players online: %s" % (len(ret_list),
                                                ", ".join(ret_list)))

    def generate_whois(self, info):
        l = ""
        if not info.logged_in:
            l = "(Offline)"
        return ("Name: %s\n"
                "Roles: ^yellow;%s^green;%s\n"
                "UUID: ^yellow;%s^green;\n"
                "IP address: ^cyan;%s^green;\n"
                "Current location: ^yellow;%s^green;""" % (
                    info.name, l, ", ".join(info.roles),
                    info.uuid, info.ip, info.location))

    @Command("whois", doc="Returns client data about the specified user.",
             syntax="(username)", role=Whois)
    def whois(self, data, protocol):
        if len(data) == 0:
            raise SyntaxWarning
        name = " ".join(data)
        info = self.plugins['player_manager'].get_player_by_name(name)
        if info is not None:
            send_message(protocol, self.generate_whois(info))
        else:
            send_message(protocol, "Player not found!")

    @Command("give", "item", "give_item",
             role=GiveItem,
             doc="Gives an item to a player. "
                 "If player name is omitted, give item(s) to self.",
             syntax=("[player=self]", "(item name)", "[count=1]"))
    def give_item(self, data, protocol):
        arg_count = len(data)
        target = self.plugins.player_manager.get_player_by_name(data[0])
        if arg_count == 1:
            target = protocol.player
            item = data[0]
            count = 1
        elif arg_count == 2:
            if data[1].isdigit():
                target = protocol.player
                item = data[0]
                count = int(data[1])
            else:
                item = data[1]
                count = 1
        elif arg_count == 3:
            item = data[1]
            if not data[2].isdigit():
                raise SyntaxWarning("Couldn't convert %s to an item count." %
                                    data[2])
            count = int(data[2])
        else:
            raise SyntaxWarning("Too many arguments")
        if target is None:
            raise NameError(target)
        target = target.protocol
        if count > 1000 and item != "money":
            count = 1000
        count += 1
        item_base = data_parser.GiveItem.build(dict(name=item,
                                                    count=count,
                                                    variant_type=7,
                                                    extra=0))
        item_packet = pparser.build_packet(packets.packets['give_item'],
                                           item_base)
        yield from target.raw_write(item_packet)
        send_message(protocol, "Gave %s (count: %d) to %s" %
                               (item, count - 1, target.player.name))
        send_message(target, "%s gave you %s (count: %d)" %
                             (protocol.player.name, item, count - 1))

    @Command("nick", doc="Changes your nickname to another one.",
             syntax="(username)")
    def nick(self, data, protocol):
        name = " ".join(data)
        if self.plugins.player_manager.get_player_by_name(name):
            raise ValueError("There's already a user by that name.")
        else:
            old_name = protocol.player.name
            protocol.player.name = name
            broadcast(self.factory,
                      "%s's name has been changed to %s" % (old_name, name))
            # Removed for now as it's worthless.
            # I've filed a report with the devs about /nick on the server side
            # doing nothing but changing the chat name.
            #csp = data_parser.ChatSent.build(dict(message="/nick %s" % name,
            #                                      channel=0))
            #asyncio.Task(protocol.client_raw_write(pparser.build_packet
            #                                            'chat_sent'], csp)))

    @Command("whoami", doc="Displays your current nickname for chat.")
    def whoami(self, data, protocol):
        send_message(protocol,
                     self.generate_whois(protocol.player))
