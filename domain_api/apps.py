from django.apps import AppConfig
from django.db.models.signals import post_save

def add_to_default_group(sender, **kwargs):
    """
    Add newly created user to the default group.
    """
    from django.contrib.auth.models import Group
    user = kwargs["instance"]
    if kwargs["created"]:
        group = Group.objects.get(name="customer")
        user.groups.add(group)

class DomainApiConfig(AppConfig):
    name = 'domain_api'

    def ready(self):
        """
        Override superclass function to add post_save action to user create.
        :returns: TODO

        """
        from django.contrib.auth.models import User
        post_save.connect(add_to_default_group, sender=User)
        super().ready()
