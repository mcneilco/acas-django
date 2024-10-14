from django.conf import settings
from django.test import TestCase

from .models import Protocol, ProtocolKind

# acas/acas/test_models.py


class ProtocolModelTest(TestCase):
    def setUp(self):
        # Just get the first protocol kind
        self.protocol_kind = ProtocolKind.objects.first()
        self.protocol = Protocol.objects.create(
            ls_type_and_kind=self.protocol_kind, short_description="Test Protocol"
        )

    def test_protocol_creation(self):
        self.assertIsInstance(self.protocol, Protocol)
        self.assertEqual(self.protocol.short_description, "Test Protocol")

    def test_protocol_fields(self):
        self.assertEqual(self.protocol.thing_type_and_kind, "document_protocol")
        self.assertEqual(self.protocol.ls_type_and_kind, self.protocol_kind)
        self.assertEqual(self.protocol.short_description, "Test Protocol")

    def test_protocol_deletion(self):
        protocol_id = self.protocol.id
        self.protocol.delete()
        with self.assertRaises(Protocol.DoesNotExist):
            Protocol.objects.get(id=protocol_id)
