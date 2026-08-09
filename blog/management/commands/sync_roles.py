"""Apply blog/roles.py to the database.

    python manage.py sync_roles
    python manage.py sync_roles --prune   # also strip permissions not listed

Safe to run as often as you like — it is idempotent. Run it after every
migration that adds a model or a custom permission, and in your deploy script.
"""

from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand

from blog.roles import ROLES


class Command(BaseCommand):
    help = 'Create the Readers / Authors / Editors groups and fill them in.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--prune',
            action='store_true',
            help='Remove permissions a group holds that roles.py no longer lists.',
        )

    def handle(self, *args, **options):
        # `verbosity` is handed to every command by Django. Honouring it is
        # what lets tests call this with verbosity=0 and stay readable.
        quiet = options['verbosity'] == 0

        for role, labels in ROLES.items():
            group, created = Group.objects.get_or_create(name=role)

            wanted = []
            for label in labels:
                app_label, codename = label.split('.', 1)
                permission = Permission.objects.filter(
                    content_type__app_label=app_label, codename=codename
                ).first()
                if permission is None:
                    # Almost always a missing migration, or a typo in roles.py.
                    self.stderr.write(self.style.ERROR(f'  unknown permission: {label}'))
                    continue
                wanted.append(permission)

            group.permissions.add(*wanted)
            removed = 0
            if options['prune']:
                extra = group.permissions.exclude(pk__in=[p.pk for p in wanted])
                removed = extra.count()
                group.permissions.remove(*extra)

            if not quiet:
                verb = 'created' if created else 'updated'
                tail = f', {removed} pruned' if removed else ''
                self.stdout.write(
                    self.style.SUCCESS(f'  {verb:8} {role:9} {len(wanted)} permission(s){tail}')
                )

        if not quiet:
            self.stdout.write(self.style.SUCCESS('\nRoles are in sync.'))
