import time
from dataclasses import dataclass


def _convert_timestamp(timestamp: str or int) -> str or None:
    """ Converts epoch timestamp into human readable time

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


@dataclass
class Post(object):
    """ Parent that defines Post objects. A Slack
    post can be a:
        - Message
        - Draft
        - File
    """

    id: str
    team: str
    created: int or float or str
    client_msg_id: str
    user: str


@dataclass
class File(Post):
    name: str
    title: str
    mimetype: str
    filetype: str
    pretty_type: str
    editable: bool
    size: int or float
    mode: str
    is_public: bool
    public_url_shared: bool
    url_private: str
    url_private_download: str
    shares: list


@dataclass
class Message(Post):
    text: str
    type: str
    blocks: list
    timestamp: float
    conversation: dataclass


@dataclass
class Draft(Post):
    last_updated_ts: str
    last_updated_client: str
    blocks: list
    file_ids: list
    is_from_composer: bool
    is_deleted: bool
    is_sent: bool
    destinations: list
    attachments: list
    date_scheduled: int or float


def create_draft_from_dict(draft_dict: dict) -> Draft:
    """ Create a Draft post object from a dict containing JSON data from
    the Slack API

    Args:
        draft_dict: dict containing post information from the Slack API
    Returns:
        Draft object for the post
    """

    return Draft(
        id=draft_dict.get('id'),
        team=draft_dict.get('team_id'),
        created=draft_dict.get('date_created'),
        client_msg_id=draft_dict.get('client_msg_id'),
        user=draft_dict.get('user_id'),
        last_updated_ts=_convert_timestamp(draft_dict.get('last_updated_ts')),
        last_updated_client=draft_dict.get('last_updated_client'),
        blocks=draft_dict.get('blocks'),
        file_ids=draft_dict.get('file_ids'),
        is_from_composer=draft_dict.get('is_from_composer'),
        is_deleted=draft_dict.get('is_deleted'),
        is_sent=draft_dict.get('is_sent'),
        destinations=[i.get('channel_id') for i in draft_dict.get('destinations')],
        attachments=draft_dict.get('attachments'),
        date_scheduled=_convert_timestamp(draft_dict.get('date_scheduled'))
    )


def create_message_from_dict(message_dict: dict) -> Message:
    """ Create a Message post object from a dict containing JSON data from
    the Slack API

    Args:
        message_dict: dict containing post information from the Slack API
    Returns:
        Message object for the post
    """

    return Message(
        id=message_dict.get('client_msg_id'),
        team=message_dict.get('team'),
        created=_convert_timestamp(message_dict.get('ts')),
        timestamp=message_dict.get('ts'),
        conversation=message_dict.get('conversation'),
        client_msg_id=message_dict.get('client_msg_id'),
        user=message_dict.get('user'),
        text=message_dict.get('text'),
        type=message_dict.get('type'),
        blocks=message_dict.get('blocks'),
    )


def create_file_from_dict(file_dict: dict) -> File:
    """ Create a File post object from a dict containing JSON data from
    the Slack API

    Args:
        file_dict: dict containing post information from the Slack API
    Returns:
        File object for the post
    """

    return File(
        id=file_dict.get('id'),
        team=file_dict.get('team'),
        created=_convert_timestamp(file_dict.get('created')),
        client_msg_id=file_dict.get('id'),
        user=file_dict.get('user'),
        name=file_dict.get('name'),
        title=file_dict.get('title'),
        mimetype=file_dict.get('mimetype'),
        filetype=file_dict.get('filetype'),
        pretty_type=file_dict.get('pretty_type'),
        editable=file_dict.get('editable'),
        size=file_dict.get('size'),
        mode=file_dict.get('mode'),
        is_public=file_dict.get('is_public'),
        public_url_shared=file_dict.get('public_url_shared'),
        url_private=file_dict.get('url_private'),
        url_private_download=file_dict.get('url_private_download'),
        shares=file_dict.get('shares')
    )
