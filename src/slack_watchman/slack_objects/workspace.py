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
class Workspace(object):
    """ Class that defines Workspaces objects. Workspaces are collections
    of conversations in a Slack Enterprise Organisation"""

    __slots__ = [
        'id',
        'name',
        'domain',
        'email_domain',
        'is_verified',
        'archived',
        'deleted',
        'discoverable',
        'enterprise_id',
        'enterprise_domain',
        'enterprise_name',
        'is_enterprise',
        'created',
        'description',
        'url'
    ]

    id: str
    name: str
    domain: str
    email_domain: str
    is_verified: bool
    archived: bool
    deleted: bool
    discoverable: bool
    enterprise_id: str
    enterprise_domain: str
    enterprise_name: str
    is_enterprise: int
    created: int or float or str
    description: str
    url: str


def create_from_dict(workspace_dict: dict) -> Workspace:
    """ Return a Workspace object based off an input dictionary

    Args:
        workspace_dict: dictionary/JSON formatted representation of the
            workspace.
    Returns:
        Workspace object representing the workspace
    """

    return Workspace(
        id=workspace_dict.get('id'),
        name=workspace_dict.get('name'),
        domain=workspace_dict.get('domain'),
        email_domain=workspace_dict.get('email_domain'),
        is_verified=workspace_dict.get('is_verified'),
        archived=workspace_dict.get('archived'),
        deleted=workspace_dict.get('deleted'),
        discoverable=workspace_dict.get('discoverable'),
        enterprise_id=workspace_dict.get('enterprise_id'),
        enterprise_domain=workspace_dict.get('enterprise_domain'),
        enterprise_name=workspace_dict.get('enterprise_name'),
        is_enterprise=workspace_dict.get('is_enterprise'),
        created=_convert_timestamp(workspace_dict.get('created')),
        description=workspace_dict.get('description'),
        url=f'https://{workspace_dict.get("enterprise_domain")}'
            f'.enterprise.slack.com/workspace/{workspace_dict.get("id")} '
    )
