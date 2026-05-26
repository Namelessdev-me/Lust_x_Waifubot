
import logging
import re
from typing import Union

import pyrogram
from pyrogram import raw
from pyrogram import utils
from pyrogram.errors import PeerIdInvalid

log = logging.getLogger(__name__)

MIN_CHANNEL_ID = -1002147483647
MAX_CHANNEL_ID = -1000000000000
MIN_CHAT_ID = -2147483647
MAX_USER_ID_OLD = 2147483647
MAX_USER_ID = 999999999999

def get_peer_type(peer_id: int) -> str:
    if peer_id < 0:
        if MIN_CHAT_ID <= peer_id:
            return "chat"

        if peer_id < MAX_CHANNEL_ID:
            return "channel"
    elif 0 < peer_id <= MAX_USER_ID:
        return "user"

    raise ValueError(f"Peer id invalid: {peer_id}")

class ResolvePeer:
    def __init__(self, cl) -> None:
        self.cl = cl

    async def resolve_peer(
        self: "pyrogram.Client",
        peer_id: Union[int, str]
    ) -> Union[raw.base.InputPeer, raw.base.InputUser, raw.base.InputChannel]:
        """Get the InputPeer of a known peer id.
        Useful whenever an InputPeer type is required.

        .. note::

            This is a utility method intended to be used **only** when working with raw
            :obj:`functions <pyrogram.api.functions>` (i.e: a Telegram API method you wish to use which is not
            available yet in the Client class as an easy-to-use method).

        .. include:: /_includes/usable-by/users-bots.rst

        Parameters:
            peer_id (``int`` | ``str``):
                The peer id you want to extract the InputPeer from.
                Can be a direct id (int), a username (str) or a phone number (str).

        Returns:
            ``InputPeer``: On success, the resolved peer id is returned in form of an InputPeer object.

        Raises:
            KeyError: In case the peer doesn't exist in the internal database.
        """
        if not self.cl.is_connected:
            raise ConnectionError("Client has not been started yet")

        try:
            return await self.cl.storage.get_peer_by_id(peer_id)
        except KeyError:
            if isinstance(peer_id, str):
                if peer_id in ("self", "me"):
                    return raw.types.InputPeerSelf()

                peer_id = re.sub(r"[@+\s]", "", peer_id.lower())

                try:
                    int(peer_id)
                except ValueError:
                    try:
                        return await self.cl.storage.get_peer_by_username(peer_id)
                    except KeyError:
                        await self.cl.invoke(
                            raw.functions.contacts.ResolveUsername(
                                username=peer_id
                            )
                        )

                        return await self.cl.storage.get_peer_by_username(peer_id)
                else:
                    try:
                        return await self.cl.storage.get_peer_by_phone_number(peer_id)
                    except KeyError:
                        raise PeerIdInvalid

            peer_type = get_peer_type(peer_id)

            if peer_type == "user":
                await self.cl.fetch_peers(
                    await self.cl.invoke(
                        raw.functions.users.GetUsers(
                            id=[
                                raw.types.InputUser(
                                    user_id=peer_id,
                                    access_hash=0
                                )
                            ]
                        )
                    )
                )
            elif peer_type == "chat":
                await self.cl.invoke(
                    raw.functions.messages.GetChats(
                        id=[-peer_id]
                    )
                )
            else:
                await self.cl.invoke(
                    raw.functions.channels.GetChannels(
                        id=[
                            raw.types.InputChannel(
                                channel_id=utils.get_channel_id(peer_id),
                                access_hash=0
                            )
                        ]
                    )
                )

            try:
                return await self.cl.storage.get_peer_by_id(peer_id)
            except KeyError:
                raise PeerIdInvalid
