from dataclasses import dataclass
from typing import Dict


@dataclass(slots=True)
class Enterprise(object):
    """ Class that defines Enterprise objects. A Slack Enterprise
    is the top level organisation that contains workspaces"""

    id: str
    name: str
    domain: str
    email_domain: str
    is_verified: bool
    discoverable: bool
    pay_prod_cur: str
    locale: str
    url: str


def create_from_dict(enterprise_dict: Dict) -> Enterprise:
    """ Create an Enterprise object from a dict response from the Slack API

    Args:
        enterprise_dict: dict/JSON format data from Slack API
    Returns:
        A new Enterprise object
    """

    return Enterprise(
        id=enterprise_dict.get('id'),
        name=enterprise_dict.get('name'),
        domain=enterprise_dict.get('domain'),
        email_domain=enterprise_dict.get('email_domain'),
        is_verified=enterprise_dict.get('is_verified'),
        discoverable=enterprise_dict.get('discoverable'),
        pay_prod_cur=enterprise_dict.get('pay_prod_cur'),
        locale=enterprise_dict.get('locale'),
        url=f'https://{enterprise_dict.get("domain")}.enterprise.slack.com'
    )
