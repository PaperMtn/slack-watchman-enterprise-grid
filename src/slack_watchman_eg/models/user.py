import time
from dataclasses import dataclass
from typing import Dict, List

from . import workspace


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
class User(object):
    """ Class that defines User objects for Slack users"""

    id: str
    name: str
    email: str
    title: str
    deleted: bool
    color: str
    real_name: str
    first_name: str
    last_name: str
    phone: str
    skype: str
    display_name: str
    fields: Dict
    api_app_id: str
    always_active: bool
    bot_id: str
    enterprise: str
    tz: str
    tz_label: str
    tz_offset: str
    is_admin: bool
    is_owner: bool
    is_primary_owner: bool
    is_restricted: bool
    is_ultra_restricted: bool
    is_bot: bool
    is_app_user: bool
    updated: int or float or str
    is_email_confirmed: bool
    who_can_share_contact_card: str
    is_workflow_bot: bool
    workspaces: List[workspace.Workspace]


@dataclass(slots=True)
class UserSuccinct(object):
    """ Class that defines User objects for Slack users"""

    id: str
    name: str
    email: str
    title: str
    deleted: bool
    real_name: str
    first_name: str
    last_name: str
    is_admin: bool
    is_owner: bool
    is_bot: bool
    is_app_user: bool
    is_workflow_bot: bool


def create_from_dict(user_dict: Dict,
                     workspaces: List[workspace.Workspace],
                     verbose: bool) -> User or UserSuccinct:
    """ Create a User object from a dict response from the Slack API

    Args:
        verbose: Whether to output a full User object, or use
            less verbose succinct class
        user_dict: dict/JSON format data from Slack API
        workspaces: list of Workspace objects
    Returns:
        A new User object
    """

    if verbose:
        return User(
            id=user_dict.get('id'),
            name=user_dict.get('name'),
            deleted=user_dict.get('deleted'),
            color=user_dict.get('colour'),
            real_name=user_dict.get('real_name'),
            tz=user_dict.get('tz'),
            tz_label=user_dict.get('tz_label'),
            tz_offset=user_dict.get('tz_offset'),
            title=user_dict.get('profile').get('title'),
            phone=user_dict.get('profile').get('phone'),
            skype=user_dict.get('profile').get('skype'),
            display_name=user_dict.get('profile').get('display_name'),
            fields=user_dict.get('profile').get('fields'),
            email=user_dict.get('profile').get('email'),
            api_app_id=user_dict.get('profile').get('api_app_id'),
            always_active=user_dict.get('profile').get('always_active'),
            bot_id=user_dict.get('profile').get('bot_id'),
            first_name=user_dict.get('profile').get('first_name'),
            last_name=user_dict.get('profile').get('last_name'),
            enterprise=user_dict.get('profile').get('enterprise'),
            is_admin=user_dict.get('is_admin'),
            is_owner=user_dict.get('is_owner'),
            is_primary_owner=user_dict.get('is_primary_owner'),
            is_restricted=user_dict.get('is_restricted'),
            is_ultra_restricted=user_dict.get('is_ultra_restricted'),
            is_bot=user_dict.get('is_bot'),
            is_app_user=user_dict.get('is_app_user'),
            updated=_convert_timestamp(user_dict.get('updated')),
            is_email_confirmed=user_dict.get('is_email_confirmed'),
            who_can_share_contact_card=user_dict.get('who_can_share_contact_card'),
            is_workflow_bot=user_dict.get('is_workflow_bot'),
            workspaces=workspaces
        )
    else:
        return UserSuccinct(
            id=user_dict.get('id'),
            name=user_dict.get('name'),
            deleted=user_dict.get('deleted'),
            real_name=user_dict.get('real_name'),
            title=user_dict.get('profile').get('title'),
            email=user_dict.get('profile').get('email'),
            first_name=user_dict.get('profile').get('first_name'),
            last_name=user_dict.get('profile').get('last_name'),
            is_admin=user_dict.get('is_admin'),
            is_owner=user_dict.get('is_owner'),
            is_bot=user_dict.get('is_bot'),
            is_app_user=user_dict.get('is_app_user'),
            is_workflow_bot=user_dict.get('is_workflow_bot'),
        )
