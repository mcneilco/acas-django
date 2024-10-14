# myapp/management/commands/seed_protocols.py
from django.core.management.base import BaseCommand

from acas.models import Protocol, ProtocolKind


class Command(BaseCommand):
    help = "Seed the database with protocols"

    def handle(self, *args, **kwargs):
        self.seed_protocols(1000)
        self.stdout.write(self.style.SUCCESS("Successfully seeded 1000 protocols"))

    def seed_protocols(self, n):
        for _ in range(n):
            protocol = Protocol(short_description="Test Protocol")
            protocol.save()
            # save it again to get another version number to make sure versions are working
            protocol.save()
