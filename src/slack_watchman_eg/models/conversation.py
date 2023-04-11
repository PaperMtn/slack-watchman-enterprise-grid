import time
from dataclasses import dataclass
from typing import List, Dict


def _convert_timestamp(timestamp: str or int) -> str or None:
    """ Converts epoch timestamp into human-readable time

    Args:
        timestamp: epoch timestamp in seconds
    Returns:
        String time in the format YYYY-mm-dd hh:mm:ss
    """

    if timestamp:
        if isinstance(timestamp, str):
            timestamp = timestamp.split('.', 1)[0]

        return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(timestamp)))
    else:
        return None


@dataclass(slots=True)
class Purpose(object):
    text: str
    set_by: str
    date_set: str


@dataclass(slots=True)
class Topic(object):
    text: str
    set_by: str
    date_set: str


@dataclass(slots=True)
class Retention(object):
    type: str
    duration: int


@dataclass(slots=True)
class Shared(object):
    shared_team_ids: List[str]
    connected_team_ids: List[str]
    internal_team_ids: List[str]
    connected_limited_team_ids: List[str]


@dataclass(slots=True)
class Conversation(object):
    """ Class that defines Conversation objects. Conversations
    could be:
        - Direct messages
        - Multi-person direct messages
        - Private channels
        - Public channels
        - Slack connect channels"""

    id: str
    name: str
    created: int or float or str
    is_private: bool
    is_im: bool
    is_mpim: bool
    is_deleted: bool
    is_archived: bool
    is_global_shared: bool
    is_org_shared: bool
    member_count: int
    is_general: bool
    creator: str
    is_moved: bool
    name_normalized: str
    is_org_mandatory: bool
    is_org_default: bool
    previous_names: List[str]
    has_guests: bool
    purpose: Purpose
    topic: Topic
    retention: Retention
    shared_workspaces: List[str]


@dataclass(slots=True)
class ConversationSuccinct(object):
    """ Class that defines Conversation objects. Conversations
    could be:
        - Direct messages
        - Multi-person direct messages
        - Private channels
        - Public channels
        - Slack connect channels"""

    id: str
    name: str
    created: int or float or str
    is_private: bool
    is_im: bool
    is_mpim: bool
    is_deleted: bool
    is_archived: bool
    member_count: int
    creator: str
    has_guests: bool
    purpose: Purpose


def create_from_dict(conv_dict: Dict, verbose: bool) -> Conversation or ConversationSuccinct:
    """ Create a User object from a dict response from the Slack API

    Args:
        conv_dict: dict/JSON format data from Slack API
        verbose: Whether to use verbose logging or not
    Returns:
        A new Conversation object
    """

    if verbose:
        return Conversation(
            id=conv_dict.get('id'),
            name=conv_dict.get('name'),
            created=_convert_timestamp(conv_dict.get('created')),
            member_count=conv_dict.get('member_count'),
            is_general=conv_dict.get('is_general'),
            is_private=conv_dict.get('is_private'),
            is_im=conv_dict.get('is_im'),
            is_mpim=conv_dict.get('is_mpim'),
            is_deleted=conv_dict.get('is_deleted'),
            is_archived=conv_dict.get('is_archived'),
            creator=conv_dict.get('creator'),
            is_moved=conv_dict.get('is_moved'),
            name_normalized=conv_dict.get('name_normalized'),
            is_global_shared=conv_dict.get('is_global_shared'),
            is_org_shared=conv_dict.get('is_org_shared'),
            is_org_mandatory=conv_dict.get('is_org_mandatory'),
            is_org_default=conv_dict.get('is_org_default'),
            previous_names=conv_dict.get('previous_names'),
            has_guests=conv_dict.get('has_guests'),
            purpose=Purpose(text=conv_dict.get('purpose').get('text'),
                            set_by=conv_dict.get('purpose').get('set_by'),
                            date_set=conv_dict.get('purpose').get('date_set')
                            ),
            topic=Topic(text=conv_dict.get('topic').get('text'),
                        set_by=conv_dict.get('topic').get('set_by'),
                        date_set=conv_dict.get('topic').get('date_set')
                        ),
            retention=Retention(type=conv_dict.get('retention').get('type'),
                                duration=conv_dict.get('retention').get('duration')
                                ),
            shared_workspaces=conv_dict.get('shared')
        )
    else:
        return ConversationSuccinct(
            id=conv_dict.get('id'),
            name=conv_dict.get('name'),
            created=_convert_timestamp(conv_dict.get('created')),
            member_count=conv_dict.get('member_count'),
            is_private=conv_dict.get('is_private'),
            is_im=conv_dict.get('is_im'),
            is_mpim=conv_dict.get('is_mpim'),
            is_deleted=conv_dict.get('is_deleted'),
            is_archived=conv_dict.get('is_archived'),
            creator=conv_dict.get('creator'),
            has_guests=conv_dict.get('has_guests'),
            purpose=Purpose(text=conv_dict.get('purpose').get('text'),
                            set_by=conv_dict.get('purpose').get('set_by'),
                            date_set=conv_dict.get('purpose').get('date_set')
                            )
        )
