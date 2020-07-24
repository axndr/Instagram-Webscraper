import json
from types import SimpleNamespace


class Person:
    def __init__(self):
        """
        edge_followed_by = follower count
        followed_by_viewer
        edge_follow: Count of followed users who also follow this account
        follows_viewer: (bool) does this account follow you
        id
        is_business_account
        is_joined_recently
        :param name:
        :param viewable:
        """
        self.viewable = self.get_view_status()

    def get_info(self):
        pass

    def get_view_status(self) -> bool:
        """
        blocked_by_viewer
        restricted_by_viewer
        country_block
        :param self:
        :return:
        """
        pass

    def relationship(self):
        """
        has_blocked_viewer
        has_requested_viewer
        :return:
        """
        pass
