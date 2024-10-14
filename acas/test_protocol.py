from django.conf import settings
from django.db import transaction
from django.test import TransactionTestCase

from .models import Protocol, ProtocolKind

# acas/acas/test_models.py


class ProtocolModelTest(TransactionTestCase):
    def setUp(self):
        # Just get the first protocol kind
        self.protocol = Protocol.objects.create(short_description="Test Protocol")

    def test_protocol_creation(self):
        self.assertIsInstance(self.protocol, Protocol)
        self.assertEqual(self.protocol.short_description, "Test Protocol")
        self.assertEqual(self.protocol.version, 1)

    def test_protocol_fields(self):
        self.assertEqual(self.protocol.thing_type_and_kind, "document_protocol")
        self.assertEqual(self.protocol.short_description, "Test Protocol")

    def test_protocol_deletion(self):
        # Commit the transaction to persist the protocol to the database
        transaction.commit()
        protocol_id = self.protocol.id
        self.protocol.delete()
        transaction.commit()

        # Base manager should filter out the soft deleted protocols
        with self.assertRaises(Protocol.DoesNotExist):
            Protocol.objects.get(id=protocol_id)

        # All objects should return the soft deleted protocol
        self.assertTrue(Protocol.all_objects.filter(id=protocol_id).exists())

    def test_modified_date_auto_update(self):
        original_modified_date = self.protocol.modified_date
        original_recorded_date = self.protocol.recorded_date
        self.protocol.short_description = "New Description"
        self.protocol.save()
        # assert that the original modified date is less than the new modified date
        self.assertLess(original_modified_date, self.protocol.modified_date)
        # asser that the recorded_date is not updated
        self.assertEqual(original_recorded_date, self.protocol.recorded_date)
