from django.apps import apps
from django.db.models.signals import post_migrate

from .models import AbstractThing, LabelSequence, ProtocolKind, ProtocolType


def create_label_sequences(sender, **kwargs):
    # Get all models that inherit from AbstractThing
    for model in apps.get_models():
        if issubclass(model, AbstractThing) and model is not AbstractThing:
            # Each model has a thing_type_and_kind, label_type_and_kind and a label_prefix which can yield a label sequence
            # Skip the model if it has no label_prefix
            if not model.label_prefix:
                continue
            # Create a label sequence for the model
            label_sequence, created = LabelSequence.objects.get_or_create(
                thing_type_and_kind=model.thing_type_and_kind,
                label_type_and_kind=model.label_type_and_kind,
                label_prefix=model.label_prefix,
                digits=model.label_digits,
                label_separator=model.label_separator,
                starting_number=model.label_starting_number,
                group_digits=model.label_group_digits,
                ignored=False,
            )


def create_protocol_types_kinds(sender, **kwargs):
    # Types
    types_kinds = [
        {"type_name": "default", "kind_name": "default"},
        {"type_name": "default", "kind_name": "flipr screening assay"},
        {"type_name": "Biology", "kind_name": "Bio Activity"},
    ]
    for type_kind in types_kinds:
        type_obj, created = ProtocolType.objects.get_or_create(
            type_name=type_kind["type_name"]
        )
        kind_obj, created = ProtocolKind.objects.get_or_create(
            kind_name=type_kind["kind_name"], ls_type=type_obj
        )


# Connect the signal handler to the post_migrate signal
post_migrate.connect(create_label_sequences)
post_migrate.connect(create_protocol_types_kinds)
