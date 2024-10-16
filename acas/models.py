# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
import re

from concurrency.fields import AutoIncVersionField
from django.db import connection, models
from django.utils import timezone


class BaseModelManger(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(deleted=False)


class BaseModel(models.Model):
    version = AutoIncVersionField()
    recorded_by = models.CharField(max_length=255)
    recorded_date = models.DateTimeField(default=timezone.now)
    modified_by = models.CharField(max_length=255, blank=True, null=True)
    modified_date = models.DateTimeField(blank=True, null=True)
    ls_type = models.CharField(max_length=64)
    ls_kind = models.CharField(max_length=255)
    ls_type_and_kind = models.CharField(max_length=255, blank=True, null=True)
    ignored = models.BooleanField(default=False)
    deleted = models.BooleanField(default=False)
    ls_transaction = models.BigIntegerField(blank=True, null=True)

    objects = BaseModelManger()
    all_objects = (
        models.Manager()
    )  # Manager to access all objects including deleted ones

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        # Update modified_date and modified_by fields
        # Check if the object is being created for the first time
        if not self.pk:
            # Recorded_date should already be set by the default but if not set it to now
            if not self.recorded_date:
                self.recorded_date = timezone.now()
            self.modified_date = self.recorded_date
        else:
            self.modified_date = timezone.now()

        super(BaseModel, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self.deleted = True
        self.ignored = True
        self.save()

    def active_objects(self):
        return self.objects.filter(deleted=False, ignored=False)

    def hard_delete(self, *args, **kwargs):
        super(BaseModel, self).delete(*args, **kwargs)


class AbstractState(BaseModel):
    comments = models.CharField(max_length=512, blank=True, null=True)

    class Meta:
        abstract = True


class AbstractLabel(BaseModel):
    label_text = models.CharField(max_length=255)
    physically_labled = models.BooleanField(default=False)
    image_file = models.CharField(max_length=255, blank=True, null=True)
    preferred = models.BooleanField(default=False)

    class Meta:
        abstract = True


class AbstractKind(models.Model):
    kind_name = models.CharField(max_length=255)
    ls_type_and_kind = models.CharField(
        unique=True, max_length=255, blank=True, null=True
    )
    version = AutoIncVersionField()

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        # Set ls_type_and_kind based on the related ProtocolType instance
        if self.ls_type:
            self.ls_type_and_kind = f"{self.ls_type.type_name}_{self.kind_name}"
        super().save(*args, **kwargs)


class AbstractValue(BaseModel):
    code_origin = models.CharField(max_length=255, blank=True, null=True)
    code_type = models.CharField(max_length=255, blank=True, null=True)
    code_kind = models.CharField(max_length=255, blank=True, null=True)
    code_type_and_kind = models.CharField(max_length=350, blank=True, null=True)
    string_value = models.CharField(max_length=255, blank=True, null=True)
    code_value = models.CharField(max_length=255, blank=True, null=True)
    file_value = models.CharField(max_length=512, blank=True, null=True)
    url_value = models.CharField(max_length=2000, blank=True, null=True)
    date_value = models.DateTimeField(blank=True, null=True)
    clob_value = models.TextField(blank=True, null=True)
    blob_value = models.BinaryField(blank=True, null=True)
    operator_type = models.CharField(max_length=25, blank=True, null=True)
    operator_kind = models.CharField(max_length=10, blank=True, null=True)
    operator_type_and_kind = models.CharField(max_length=50, blank=True, null=True)
    numeric_value = models.DecimalField(
        max_digits=38, decimal_places=18, blank=True, null=True
    )
    sig_figs = models.IntegerField(blank=True, null=True)
    uncertainty = models.DecimalField(
        max_digits=38, decimal_places=18, blank=True, null=True
    )
    number_of_replicates = models.IntegerField(blank=True, null=True)
    uncertainty_type = models.CharField(max_length=255, blank=True, null=True)
    unit_type = models.CharField(max_length=25, blank=True, null=True)
    unit_kind = models.CharField(max_length=25, blank=True, null=True)
    unit_type_and_kind = models.CharField(max_length=55, blank=True, null=True)
    concentration = models.FloatField(blank=True, null=True)
    conc_unit = models.CharField(max_length=25, blank=True, null=True)
    comments = models.CharField(max_length=512, blank=True, null=True)
    public_data = models.BooleanField(default=False)

    class Meta:
        abstract = True


class AbstractThing(BaseModel):
    label_type_and_kind = "id_codeName"
    label_separator = "-"
    label_digits = 8
    label_starting_number = 1
    label_prefix = None
    label_group_digits = False
    code_name = models.CharField(unique=True, max_length=255, blank=True, null=True)

    class Meta:
        abstract = True

    def generate_code_name(self):
        if not hasattr(self, "thing_type_and_kind") or not self.thing_type_and_kind:
            return  # Skip code name generation if thing_type_and_kind is not defined
        label_sequence = LabelSequence.objects.get(
            thing_type_and_kind=self.thing_type_and_kind,
            label_type_and_kind=self.label_type_and_kind,
        )
        self.code_name = label_sequence.generate_label()

    def save(self, *args, **kwargs):
        if not self.code_name:
            self.generate_code_name()
        super().save(*args, **kwargs)


class AbstractKindConstrained(models.Model):
    class Meta:
        abstract = True

    @property
    def kind_model(self):
        raise NotImplementedError("Subclasses must implement the kind_model property")

    def save(self, *args, **kwargs):
        if not self.ls_type or not self.ls_kind or not self.ls_type_and_kind:
            KindModel = self.kind_model
            default_kind = KindModel.objects.filter(
                ls_type_and_kind=self.default_type_and_kind
            ).first()
            if default_kind:
                self.ls_type = default_kind.ls_type.type_name
                self.ls_kind = default_kind.kind_name
                self.ls_type_and_kind = default_kind

        super().save(*args, **kwargs)


class AbstractbbchemStructure(models.Model):
    average_mol_weight = models.FloatField(blank=True, null=True)
    exact_mol_weight = models.FloatField(blank=True, null=True)
    mol = models.TextField()
    molecular_formula = models.CharField(max_length=255, blank=True, null=True)
    pre_reg = models.CharField(max_length=40, blank=True, null=True)
    recorded_date = models.DateTimeField()
    reg = models.CharField(max_length=40, blank=True, null=True)
    registration_comment = models.CharField(max_length=255, blank=True, null=True)
    registration_status = models.CharField(max_length=255, blank=True, null=True)
    similarity = models.UUIDField(blank=True, null=True)
    standardization_comment = models.CharField(max_length=255, blank=True, null=True)
    standardization_status = models.CharField(max_length=255, blank=True, null=True)
    substructure = models.UUIDField(blank=True, null=True)
    total_charge = models.IntegerField(blank=True, null=True)
    version = AutoIncVersionField()

    class Meta:
        abstract = True


class AnalysisGroup(AbstractThing):
    thing_type_and_kind = "document_analysis group"
    label_prefix = "AG"

    class Meta:
        db_table = "analysis_group"


class AnalysisGroupLabel(AbstractLabel, AbstractKindConstrained):
    ls_type_and_kind = models.ForeignKey(
        "LabelKind",
        models.DO_NOTHING,
        db_column="ls_type_and_kind",
        to_field="ls_type_and_kind",
        blank=True,
        null=True,
    )
    analysis_group = models.ForeignKey(AnalysisGroup, models.DO_NOTHING)

    class Meta:
        db_table = "analysis_group_label"

    @property
    def kind_model(self):
        return LabelKind


class AnalysisGroupState(AbstractState):
    analysis_group = models.ForeignKey(AnalysisGroup, models.DO_NOTHING)

    class Meta:
        db_table = "analysis_group_state"


class AnalysisGroupValue(AbstractValue):
    ls_type_and_kind = models.ForeignKey(
        "ValueKind",
        models.DO_NOTHING,
        db_column="ls_type_and_kind",
        to_field="ls_type_and_kind",
        blank=True,
        null=True,
    )
    analysis_state = models.ForeignKey(AnalysisGroupState, models.DO_NOTHING)

    class Meta:
        db_table = "analysis_group_value"


class AnalysisgroupTreatmentgroup(models.Model):
    treatment_group = models.OneToOneField(
        "TreatmentGroup", models.DO_NOTHING, primary_key=True
    )  # The composite primary key (treatment_group_id, analysis_group_id) found, that is not supported. The first column is selected.
    analysis_group = models.ForeignKey(AnalysisGroup, models.DO_NOTHING)

    class Meta:
        db_table = "analysisgroup_treatmentgroup"
        unique_together = (("treatment_group", "analysis_group"),)


class ApplicationSetting(models.Model):
    comments = models.CharField(max_length=512, blank=True, null=True)
    ignored = models.BooleanField()
    prop_name = models.CharField(max_length=255, blank=True, null=True)
    prop_value = models.CharField(max_length=255, blank=True, null=True)
    recorded_date = models.DateTimeField(blank=True, null=True)
    version = AutoIncVersionField()

    class Meta:
        db_table = "application_setting"


class Author(AbstractThing):
    thing_type_and_kind = "author_author"
    label_prefix = "AUTH"
    activation_date = models.DateTimeField(blank=True, null=True)
    activation_key = models.CharField(max_length=255, blank=True, null=True)
    email_address = models.CharField(unique=True, max_length=255)
    enabled = models.BooleanField(blank=True, null=True)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    locked = models.BooleanField(blank=True, null=True)
    password = models.CharField(max_length=255, blank=True, null=True)
    user_name = models.CharField(unique=True, max_length=255)

    class Meta:
        db_table = "author"


class AuthorLabel(AbstractLabel):
    author = models.ForeignKey(Author, models.DO_NOTHING)

    class Meta:
        db_table = "author_label"


class AuthorRole(models.Model):
    version = AutoIncVersionField()
    lsrole = models.ForeignKey("LsRole", models.DO_NOTHING)
    author = models.ForeignKey(Author, models.DO_NOTHING)

    class Meta:
        db_table = "author_role"
        unique_together = (
            ("author", "lsrole"),
            ("author", "lsrole"),
        )


class AuthorState(AbstractState):
    ls_type_and_kind = models.ForeignKey(
        "StateKind",
        models.DO_NOTHING,
        db_column="ls_type_and_kind",
        to_field="ls_type_and_kind",
        blank=True,
        null=True,
    )
    author = models.ForeignKey(Author, models.DO_NOTHING)

    class Meta:
        db_table = "author_state"


class AuthorValue(AbstractValue):
    ls_type_and_kind = models.ForeignKey(
        "ValueKind",
        models.DO_NOTHING,
        db_column="ls_type_and_kind",
        to_field="ls_type_and_kind",
        blank=True,
        null=True,
    )
    author_state = models.ForeignKey(AuthorState, models.DO_NOTHING)

    class Meta:
        db_table = "author_value"


class BingoConfig(models.Model):
    cname = models.CharField(max_length=255, blank=True, null=True)
    cvalue = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = "bingo_config"


class BingoTauConfig(models.Model):
    rule_idx = models.IntegerField(blank=True, null=True)
    tau_beg = models.TextField(blank=True, null=True)
    tau_end = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "bingo_tau_config"


class BulkLoadFile(models.Model):
    file_name = models.CharField(max_length=1000, blank=True, null=True)
    file_size = models.IntegerField()
    json_template = models.TextField(blank=True, null=True)
    number_of_mols = models.IntegerField()
    recorded_by = models.CharField(max_length=255)
    version = AutoIncVersionField()
    file_date = models.DateTimeField(blank=True, null=True)
    recorded_date = models.DateTimeField()
    original_file_name = models.CharField(max_length=1000, blank=True, null=True)

    class Meta:
        db_table = "bulk_load_file"


class BulkLoadTemplate(models.Model):
    json_template = models.TextField(blank=True, null=True)
    recorded_by = models.CharField(max_length=255)
    template_name = models.CharField(max_length=255, blank=True, null=True)
    version = AutoIncVersionField()
    ignored = models.BooleanField()

    class Meta:
        db_table = "bulk_load_template"
        unique_together = (("template_name", "recorded_by"),)


class ChemStructure(models.Model):
    code_name = models.CharField(unique=True, max_length=255)
    deleted = models.BooleanField()
    ignored = models.BooleanField()
    ls_kind = models.CharField(max_length=255, blank=True, null=True)
    ls_transaction = models.BigIntegerField(blank=True, null=True)
    ls_type = models.CharField(max_length=255, blank=True, null=True)
    ls_type_and_kind = models.CharField(max_length=255, blank=True, null=True)
    modified_by = models.CharField(max_length=255, blank=True, null=True)
    modified_date = models.DateTimeField(blank=True, null=True)
    mol_structure = models.TextField()
    recorded_by = models.CharField(max_length=255)
    recorded_date = models.DateTimeField()
    smiles = models.CharField(max_length=1000, blank=True, null=True)
    version = AutoIncVersionField()

    class Meta:
        db_table = "chem_structure"


class CmpdRegAppSetting(models.Model):
    comments = models.CharField(max_length=512, blank=True, null=True)
    ignored = models.BooleanField()
    prop_name = models.CharField(max_length=255, blank=True, null=True)
    prop_value = models.CharField(max_length=255, blank=True, null=True)
    recorded_date = models.DateTimeField(blank=True, null=True)
    version = AutoIncVersionField()

    class Meta:
        db_table = "cmpd_reg_app_setting"


class CodeKind(AbstractKind):
    ls_type = models.ForeignKey("CodeType", models.DO_NOTHING, db_column="ls_type")

    class Meta:
        db_table = "code_kind"


class CodeOrigin(models.Model):
    name = models.CharField(unique=True, max_length=256)
    version = AutoIncVersionField()

    class Meta:
        db_table = "code_origin"


class CodeType(models.Model):
    type_name = models.CharField(unique=True, max_length=128)
    version = AutoIncVersionField()

    class Meta:
        db_table = "code_type"


class Compound(models.Model):
    version = AutoIncVersionField()
    corp_name = models.CharField(max_length=255, blank=True, null=True)
    external_id = models.CharField(max_length=255, blank=True, null=True)
    cd_id = models.IntegerField()
    ignored = models.BooleanField(blank=True, null=True)
    deleted = models.BooleanField(blank=True, null=True)
    created_date = models.DateTimeField(blank=True, null=True)
    modified_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "compound"


class CompoundType(models.Model):
    code = models.CharField(unique=True, max_length=255)
    name = models.CharField(max_length=255)
    display_order = models.IntegerField(blank=True, null=True)
    comment = models.CharField(max_length=255, blank=True, null=True)
    version = AutoIncVersionField()

    class Meta:
        db_table = "compound_type"


class Container(AbstractThing):
    thing_type_and_kind = "material_container"
    label_prefix = "CONT"
    location_id = models.BigIntegerField(blank=True, null=True)
    column_index = models.IntegerField(blank=True, null=True)
    row_index = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = "container"


class ContainerKind(AbstractKind):
    ls_type = models.ForeignKey("ContainerType", models.DO_NOTHING, db_column="ls_type")

    class Meta:
        db_table = "container_kind"


class ContainerLabel(AbstractLabel):
    ls_type_and_kind = models.ForeignKey(
        "LabelKind",
        models.DO_NOTHING,
        db_column="ls_type_and_kind",
        to_field="ls_type_and_kind",
        blank=True,
        null=True,
    )
    container = models.ForeignKey(Container, models.DO_NOTHING)

    class Meta:
        db_table = "container_label"


class ContainerState(AbstractState):
    ls_type_and_kind = models.ForeignKey(
        "StateKind",
        models.DO_NOTHING,
        db_column="ls_type_and_kind",
        to_field="ls_type_and_kind",
        blank=True,
        null=True,
    )
    container = models.ForeignKey(Container, models.DO_NOTHING)

    class Meta:
        db_table = "container_state"


class ContainerType(models.Model):
    type_name = models.CharField(unique=True, max_length=128)
    version = AutoIncVersionField()

    class Meta:
        db_table = "container_type"


class ContainerValue(AbstractValue):
    container_state = models.ForeignKey(ContainerState, models.DO_NOTHING)

    class Meta:
        db_table = "container_value"


class CorpName(models.Model):
    comment = models.CharField(max_length=50, blank=True, null=True)
    ignore = models.BooleanField(blank=True, null=True)
    parent_corp_name = models.CharField(max_length=50, blank=True, null=True)
    version = AutoIncVersionField()

    class Meta:
        db_table = "corp_name"


class CronJob(models.Model):
    active = models.BooleanField()
    code_name = models.CharField(unique=True, max_length=255)
    function_name = models.CharField(max_length=255, blank=True, null=True)
    ignored = models.BooleanField()
    last_duration = models.BigIntegerField(blank=True, null=True)
    last_resultjson = models.TextField(blank=True, null=True)
    last_start_time = models.DateTimeField(blank=True, null=True)
    number_of_executions = models.IntegerField(blank=True, null=True)
    run_user = models.CharField(max_length=255)
    schedule = models.CharField(max_length=255)
    script_file = models.CharField(max_length=255)
    scriptjsondata = models.TextField(blank=True, null=True)
    script_type = models.CharField(max_length=255)
    version = AutoIncVersionField()

    class Meta:
        db_table = "cron_job"


class DdictKind(models.Model):
    comments = models.CharField(max_length=512, blank=True, null=True)
    description = models.CharField(max_length=512, blank=True, null=True)
    display_order = models.IntegerField(blank=True, null=True)
    ignored = models.BooleanField()
    ls_type = models.CharField(max_length=255, blank=True, null=True)
    ls_type_and_kind = models.CharField(
        unique=True, max_length=255, blank=True, null=True
    )
    name = models.CharField(max_length=255)
    version = AutoIncVersionField()

    class Meta:
        db_table = "ddict_kind"


class DdictType(models.Model):
    comments = models.CharField(max_length=512, blank=True, null=True)
    description = models.CharField(max_length=512, blank=True, null=True)
    display_order = models.IntegerField(blank=True, null=True)
    ignored = models.BooleanField()
    name = models.CharField(unique=True, max_length=255)
    version = AutoIncVersionField()

    class Meta:
        db_table = "ddict_type"


class DdictValue(models.Model):
    code_name = models.CharField(max_length=255)
    comments = models.CharField(max_length=512, blank=True, null=True)
    description = models.CharField(max_length=512, blank=True, null=True)
    display_order = models.IntegerField(blank=True, null=True)
    ignored = models.BooleanField()
    label_text = models.CharField(max_length=512)
    ls_kind = models.CharField(max_length=255)
    ls_type = models.CharField(max_length=255)
    ls_type_and_kind = models.ForeignKey(
        DdictKind,
        models.DO_NOTHING,
        db_column="ls_type_and_kind",
        to_field="ls_type_and_kind",
        blank=True,
        null=True,
    )
    short_name = models.CharField(max_length=256, blank=True, null=True)
    version = AutoIncVersionField()

    class Meta:
        db_table = "ddict_value"
        unique_together = (("ls_type", "ls_kind", "short_name"),)


class DryRunCompound(models.Model):
    corp_name = models.CharField(max_length=255, blank=True, null=True)
    stereo_category = models.CharField(max_length=255, blank=True, null=True)
    stereo_comment = models.CharField(max_length=255, blank=True, null=True)
    cd_id = models.IntegerField()
    record_number = models.IntegerField()
    mol_structure = models.TextField(blank=True, null=True)
    version = AutoIncVersionField()

    class Meta:
        db_table = "dry_run_compound"


class Experiment(AbstractThing, AbstractKindConstrained):
    thing_type_and_kind = "document_experiment"
    label_prefix = "EXPT"
    ls_type_and_kind = models.ForeignKey(
        "ExperimentKind",
        models.DO_NOTHING,
        db_column="ls_type_and_kind",
        to_field="ls_type_and_kind",
        blank=True,
        null=True,
    )
    short_description = models.CharField(max_length=1024, blank=True, null=True)
    protocol = models.ForeignKey("Protocol", models.DO_NOTHING)

    class Meta:
        db_table = "experiment"

    @property
    def kind_model(self):
        return ExperimentKind


class ExperimentAnalysisgroup(models.Model):
    analysis_group = models.OneToOneField(
        AnalysisGroup, models.DO_NOTHING, primary_key=True
    )  # The composite primary key (analysis_group_id, experiment_id) found, that is not supported. The first column is selected.
    experiment = models.ForeignKey(Experiment, models.DO_NOTHING)

    class Meta:
        db_table = "experiment_analysisgroup"
        unique_together = (("analysis_group", "experiment"),)


class ExperimentKind(AbstractKind):
    ls_type = models.ForeignKey(
        "ExperimentType", models.DO_NOTHING, db_column="ls_type"
    )

    class Meta:
        db_table = "experiment_kind"


class ExperimentLabel(AbstractLabel, AbstractKindConstrained):
    ls_type_and_kind = models.ForeignKey(
        "LabelKind",
        models.DO_NOTHING,
        db_column="ls_type_and_kind",
        to_field="ls_type_and_kind",
        blank=True,
        null=True,
    )
    experiment = models.ForeignKey(Experiment, models.DO_NOTHING)

    class Meta:
        db_table = "experiment_label"

    @property
    def kind_model(self):
        return LabelKind


class ExperimentState(AbstractState, AbstractKindConstrained):
    ls_type_and_kind = models.ForeignKey(
        "StateKind",
        models.DO_NOTHING,
        db_column="ls_type_and_kind",
        to_field="ls_type_and_kind",
        blank=True,
        null=True,
    )
    experiment = models.ForeignKey(Experiment, models.DO_NOTHING)

    class Meta:
        db_table = "experiment_state"

    @property
    def kind_model(self):
        return StateKind


class ExperimentTag(models.Model):
    experiment = models.OneToOneField(
        Experiment, models.DO_NOTHING, primary_key=True
    )  # The composite primary key (experiment_id, tag_id) found, that is not supported. The first column is selected.
    tag = models.ForeignKey("LsTag", models.DO_NOTHING)

    class Meta:
        db_table = "experiment_tag"
        unique_together = (("experiment", "tag"),)


class ExperimentType(models.Model):
    type_name = models.CharField(unique=True, max_length=128)
    version = AutoIncVersionField()

    class Meta:
        db_table = "experiment_type"


class ExperimentValue(AbstractValue, AbstractKindConstrained):
    ls_type_and_kind = models.ForeignKey(
        "ValueKind",
        models.DO_NOTHING,
        db_column="ls_type_and_kind",
        to_field="ls_type_and_kind",
        blank=True,
        null=True,
    )
    experiment_state = models.ForeignKey(ExperimentState, models.DO_NOTHING)

    class Meta:
        db_table = "experiment_value"

    @property
    def kind_model(self):
        return ValueKind


class FileList(models.Model):
    description = models.CharField(max_length=255, blank=True, null=True)
    file_name = models.CharField(max_length=255, blank=True, null=True)
    file_path = models.CharField(max_length=255, blank=True, null=True)
    ie = models.BooleanField(blank=True, null=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    size = models.BigIntegerField()
    subdir = models.CharField(max_length=255, blank=True, null=True)
    type = models.CharField(max_length=255, blank=True, null=True)
    uploaded = models.BooleanField(blank=True, null=True)
    url = models.CharField(max_length=255, blank=True, null=True)
    version = AutoIncVersionField()
    lot = models.ForeignKey(
        "Lot", models.DO_NOTHING, db_column="lot", blank=True, null=True
    )
    writeup = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "file_list"


class FileThing(AbstractThing):
    thing_type_and_kind = "document_file"
    application_type = models.CharField(max_length=512, blank=True, null=True)
    description = models.CharField(max_length=512, blank=True, null=True)
    file_extension = models.CharField(max_length=255, blank=True, null=True)
    file_size = models.BigIntegerField(blank=True, null=True)
    fileurl = models.CharField(max_length=1024, blank=True, null=True)
    mime_type = models.CharField(max_length=512, blank=True, null=True)
    name = models.CharField(max_length=512, blank=True, null=True)

    class Meta:
        db_table = "file_thing"


class FileType(models.Model):
    code = models.CharField(max_length=255, blank=True, null=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    version = AutoIncVersionField()

    class Meta:
        db_table = "file_type"


class InteractionKind(AbstractKind):
    ls_type = models.ForeignKey(
        "InteractionType", models.DO_NOTHING, db_column="ls_type"
    )

    class Meta:
        db_table = "interaction_kind"


class InteractionType(models.Model):
    type_name = models.CharField(unique=True, max_length=128)
    type_verb = models.CharField(max_length=128)
    version = AutoIncVersionField()

    class Meta:
        db_table = "interaction_type"


class IsoSalt(models.Model):
    equivalents = models.FloatField(blank=True, null=True)
    ignore = models.BooleanField(blank=True, null=True)
    type = models.CharField(max_length=25, blank=True, null=True)
    version = AutoIncVersionField()
    isotope = models.ForeignKey(
        "Isotope", models.DO_NOTHING, db_column="isotope", blank=True, null=True
    )
    salt = models.ForeignKey(
        "Salt", models.DO_NOTHING, db_column="salt", blank=True, null=True
    )
    salt_form = models.ForeignKey(
        "SaltForm", models.DO_NOTHING, db_column="salt_form", blank=True, null=True
    )

    class Meta:
        db_table = "iso_salt"


class Isotope(models.Model):
    abbrev = models.CharField(max_length=100, blank=True, null=True)
    ignore = models.BooleanField(blank=True, null=True)
    mass_change = models.FloatField(blank=True, null=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    version = AutoIncVersionField()

    class Meta:
        db_table = "isotope"


class ItxContainerContainer(AbstractThing):
    thing_type_and_kind = "interaction_containerContainer"
    label_prefix = "CITX"
    first_container = models.ForeignKey(Container, models.DO_NOTHING)
    second_container = models.ForeignKey(
        Container,
        models.DO_NOTHING,
        related_name="itxcontainercontainer_second_container_set",
    )

    class Meta:
        db_table = "itx_container_container"


class ItxContainerContainerState(AbstractState):
    itx_container_container = models.ForeignKey(
        ItxContainerContainer,
        models.DO_NOTHING,
        db_column="itx_container_container",
        blank=True,
        null=True,
    )

    class Meta:
        db_table = "itx_container_container_state"


class ItxContainerContainerValue(AbstractValue):
    ls_state = models.ForeignKey(
        ItxContainerContainerState,
        models.DO_NOTHING,
        db_column="ls_state",
        blank=True,
        null=True,
    )

    class Meta:
        db_table = "itx_container_container_value"


class ItxExptExpt(models.Model):
    code_name = models.CharField(unique=True, max_length=255, blank=True, null=True)
    deleted = models.BooleanField()
    ignored = models.BooleanField()
    ls_kind = models.CharField(max_length=255)
    ls_transaction = models.BigIntegerField(blank=True, null=True)
    ls_type = models.CharField(max_length=255)
    ls_type_and_kind = models.CharField(max_length=255, blank=True, null=True)
    modified_by = models.CharField(max_length=255, blank=True, null=True)
    modified_date = models.DateTimeField(blank=True, null=True)
    recorded_by = models.CharField(max_length=255)
    recorded_date = models.DateTimeField()
    version = AutoIncVersionField()
    first_experiment = models.ForeignKey(Experiment, models.DO_NOTHING)
    second_experiment = models.ForeignKey(
        Experiment, models.DO_NOTHING, related_name="itxexptexpt_second_experiment_set"
    )

    class Meta:
        db_table = "itx_expt_expt"


class ItxExptExptState(AbstractState):
    itx_experiment_experiment = models.ForeignKey(
        ItxExptExpt,
        models.DO_NOTHING,
        db_column="itx_experiment_experiment",
        blank=True,
        null=True,
    )

    class Meta:
        db_table = "itx_expt_expt_state"


class ItxExptExptValue(AbstractValue):
    ls_state = models.ForeignKey(
        ItxExptExptState, models.DO_NOTHING, db_column="ls_state", blank=True, null=True
    )

    class Meta:
        db_table = "itx_expt_expt_value"


class ItxLsThingLsThing(AbstractThing):
    first_ls_thing = models.ForeignKey("LsThing", models.DO_NOTHING)
    second_ls_thing = models.ForeignKey(
        "LsThing",
        models.DO_NOTHING,
        related_name="itxlsthinglsthing_second_ls_thing_set",
    )

    class Meta:
        db_table = "itx_ls_thing_ls_thing"


class ItxLsThingLsThingState(AbstractState):
    itx_ls_thing_ls_thing = models.ForeignKey(
        ItxLsThingLsThing,
        models.DO_NOTHING,
        db_column="itx_ls_thing_ls_thing",
        blank=True,
        null=True,
    )

    class Meta:
        db_table = "itx_ls_thing_ls_thing_state"


class ItxLsThingLsThingValue(AbstractValue):
    ls_state = models.ForeignKey(
        ItxLsThingLsThingState,
        models.DO_NOTHING,
        db_column="ls_state",
        blank=True,
        null=True,
    )

    class Meta:
        db_table = "itx_ls_thing_ls_thing_value"


class ItxProtocolProtocol(AbstractThing):
    first_protocol = models.ForeignKey("Protocol", models.DO_NOTHING)
    second_protocol = models.ForeignKey(
        "Protocol",
        models.DO_NOTHING,
        related_name="itxprotocolprotocol_second_protocol_set",
    )

    class Meta:
        db_table = "itx_protocol_protocol"


class ItxProtocolProtocolState(AbstractState):
    itx_protocol_protocol = models.ForeignKey(
        ItxProtocolProtocol,
        models.DO_NOTHING,
        db_column="itx_protocol_protocol",
        blank=True,
        null=True,
    )

    class Meta:
        db_table = "itx_protocol_protocol_state"


class ItxProtocolProtocolValue(AbstractValue):
    ls_state = models.ForeignKey(
        ItxProtocolProtocolState,
        models.DO_NOTHING,
        db_column="ls_state",
        blank=True,
        null=True,
    )

    class Meta:
        db_table = "itx_protocol_protocol_value"


class ItxSubjectContainer(AbstractThing):
    thing_type_and_kind = "interaction_subjectContainer"
    label_prefix = "SITX"
    container = models.ForeignKey(Container, models.DO_NOTHING)
    subject = models.ForeignKey("Subject", models.DO_NOTHING)

    class Meta:
        db_table = "itx_subject_container"


class ItxSubjectContainerState(AbstractState):
    itx_subject_container = models.ForeignKey(
        ItxSubjectContainer,
        models.DO_NOTHING,
        db_column="itx_subject_container",
        blank=True,
        null=True,
    )

    class Meta:
        db_table = "itx_subject_container_state"


class ItxSubjectContainerValue(AbstractValue):
    ls_state = models.ForeignKey(
        ItxSubjectContainerState,
        models.DO_NOTHING,
        db_column="ls_state",
        blank=True,
        null=True,
    )

    class Meta:
        db_table = "itx_subject_container_value"


class LabelKind(AbstractKind):
    ls_type = models.ForeignKey(
        "LabelType", models.DO_NOTHING, db_column="ls_type", blank=True, null=True
    )

    class Meta:
        db_table = "label_kind"


class LabelSequence(models.Model):
    digits = models.IntegerField(blank=True, null=True)
    group_digits = models.BooleanField()
    ignored = models.BooleanField()
    label_prefix = models.CharField(max_length=50)
    label_separator = models.CharField(max_length=10, blank=True, null=True)
    label_type_and_kind = models.CharField(max_length=255)
    starting_number = models.BigIntegerField()
    modified_date = models.DateTimeField(blank=True, null=True)
    thing_type_and_kind = models.CharField(max_length=255)
    version = AutoIncVersionField()
    db_sequence = models.CharField(max_length=255)

    class Meta:
        db_table = "label_sequence"
        unique_together = (
            ("thing_type_and_kind", "label_type_and_kind", "label_prefix"),
        )

    def sanitize_name(self, name):
        # Replace spaces with underscores
        name = name.replace(" ", "_")
        # Remove any non-alphanumeric characters except underscores
        name = re.sub(r"[^a-zA-Z0-9_]", "", name)
        return name

    def generate_db_sequence(self):
        sequence_name = f"labelseq_{self.label_prefix}_{self.label_type_and_kind}_{self.thing_type_and_kind}"
        return self.sanitize_name(sequence_name)

    def create_sequence(self):
        with connection.cursor() as cursor:
            cursor.execute(f"CREATE SEQUENCE IF NOT EXISTS {self.db_sequence};")

    def drop_sequence(self):
        with connection.cursor() as cursor:
            cursor.execute(f"DROP SEQUENCE IF EXISTS {self.db_sequence};")

    def save(self, *args, **kwargs):
        if not self.db_sequence:  # If db_sequence is not set, generate it
            self.db_sequence = self.generate_db_sequence()
            self.create_sequence()
        else:
            old_instance = LabelSequence.objects.filter(pk=self.pk).first()
            if old_instance and old_instance.db_sequence != self.db_sequence:
                self.drop_sequence()
                self.create_sequence()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self.drop_sequence()
        super().delete(*args, **kwargs)

    def get_next_value(self):
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT nextval('{self.db_sequence}')")
            next_value = cursor.fetchone()[0]
        return next_value

    def generate_label(self):
        next_value = self.get_next_value()
        if self.digits:
            next_value = str(next_value).zfill(self.digits)
        if self.group_digits:
            next_value = "{:,}".format(int(next_value)).replace(
                ",", self.label_separator or ""
            )
        return f"{self.label_prefix}{self.label_separator or ''}{next_value}"


class LabelSequenceLsRole(models.Model):
    version = AutoIncVersionField()
    label_sequence = models.ForeignKey(LabelSequence, models.DO_NOTHING)
    ls_role = models.ForeignKey("LsRole", models.DO_NOTHING)

    class Meta:
        db_table = "label_sequence_ls_role"
        unique_together = (
            ("label_sequence", "ls_role"),
            ("label_sequence", "ls_role"),
        )


class LabelType(models.Model):
    type_name = models.CharField(unique=True, max_length=255)
    version = AutoIncVersionField()

    class Meta:
        db_table = "label_type"


class Lot(models.Model):
    amount = models.FloatField(blank=True, null=True)
    as_drawn_struct = models.TextField(blank=True, null=True)
    barcode = models.CharField(max_length=255, blank=True, null=True)
    boiling_point = models.FloatField(blank=True, null=True)
    buid = models.BigIntegerField()
    color = models.CharField(max_length=255, blank=True, null=True)
    comments = models.TextField(blank=True, null=True)
    corp_name = models.CharField(unique=True, max_length=255)
    ignore = models.BooleanField(blank=True, null=True)
    is_virtual = models.BooleanField(blank=True, null=True)
    lot_as_drawn_cd_id = models.IntegerField()
    lot_mol_weight = models.FloatField(blank=True, null=True)
    lot_number = models.IntegerField()
    melting_point = models.FloatField(blank=True, null=True)
    notebook_page = models.CharField(max_length=255, blank=True, null=True)
    percentee = models.FloatField(blank=True, null=True)
    purity = models.FloatField(blank=True, null=True)
    registration_date = models.DateTimeField(blank=True, null=True)
    retain = models.FloatField(blank=True, null=True)
    solution_amount = models.FloatField(blank=True, null=True)
    supplier = models.CharField(max_length=255, blank=True, null=True)
    supplierid = models.CharField(max_length=255, blank=True, null=True)
    supplier_lot = models.CharField(max_length=255, blank=True, null=True)
    synthesis_date = models.DateTimeField(blank=True, null=True)
    version = AutoIncVersionField()
    amount_units = models.ForeignKey(
        "Unit", models.DO_NOTHING, db_column="amount_units", blank=True, null=True
    )
    chemist = models.CharField(blank=True, null=True)
    physical_state = models.ForeignKey(
        "PhysicalState",
        models.DO_NOTHING,
        db_column="physical_state",
        blank=True,
        null=True,
    )
    project = models.CharField(blank=True, null=True)
    purity_measured_by = models.ForeignKey(
        "PurityMeasuredBy",
        models.DO_NOTHING,
        db_column="purity_measured_by",
        blank=True,
        null=True,
    )
    purity_operator = models.ForeignKey(
        "Operator",
        models.DO_NOTHING,
        db_column="purity_operator",
        blank=True,
        null=True,
    )
    retain_units = models.ForeignKey(
        "Unit",
        models.DO_NOTHING,
        db_column="retain_units",
        related_name="lot_retain_units_set",
        blank=True,
        null=True,
    )
    salt_form = models.ForeignKey(
        "SaltForm", models.DO_NOTHING, db_column="salt_form", blank=True, null=True
    )
    solution_amount_units = models.ForeignKey(
        "SolutionUnit",
        models.DO_NOTHING,
        db_column="solution_amount_units",
        blank=True,
        null=True,
    )
    vendor = models.ForeignKey(
        "Vendor", models.DO_NOTHING, db_column="vendor", blank=True, null=True
    )
    modified_date = models.DateTimeField(blank=True, null=True)
    modified_by = models.CharField(blank=True, null=True)
    bulk_load_file = models.ForeignKey(
        BulkLoadFile,
        models.DO_NOTHING,
        db_column="bulk_load_file",
        blank=True,
        null=True,
    )
    lambda_field = models.FloatField(
        db_column="lambda", blank=True, null=True
    )  # Field renamed because it was a Python reserved word.
    absorbance = models.FloatField(blank=True, null=True)
    stock_solvent = models.CharField(max_length=255, blank=True, null=True)
    stock_location = models.CharField(max_length=255, blank=True, null=True)
    retain_location = models.CharField(max_length=255, blank=True, null=True)
    registered_by = models.CharField(blank=True, null=True)
    observed_mass_one = models.FloatField(blank=True, null=True)
    observed_mass_two = models.FloatField(blank=True, null=True)
    tare_weight = models.FloatField(blank=True, null=True)
    total_amount_stored = models.FloatField(blank=True, null=True)
    tare_weight_units = models.ForeignKey(
        "Unit",
        models.DO_NOTHING,
        db_column="tare_weight_units",
        related_name="lot_tare_weight_units_set",
        blank=True,
        null=True,
    )
    total_amount_stored_units = models.ForeignKey(
        "Unit",
        models.DO_NOTHING,
        db_column="total_amount_stored_units",
        related_name="lot_total_amount_stored_units_set",
        blank=True,
        null=True,
    )
    vendorid = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = "lot"


class LotAlias(models.Model):
    version = AutoIncVersionField()
    lot = models.ForeignKey(
        Lot, models.DO_NOTHING, db_column="lot", blank=True, null=True
    )
    alias_name = models.CharField(max_length=255, blank=True, null=True)
    ls_type = models.CharField(max_length=255, blank=True, null=True)
    ls_kind = models.CharField(max_length=255, blank=True, null=True)
    ignored = models.BooleanField(blank=True, null=True)
    deleted = models.BooleanField(blank=True, null=True)
    preferred = models.BooleanField(blank=True, null=True)

    class Meta:
        db_table = "lot_alias"


class LotAliasKind(models.Model):
    ls_type = models.ForeignKey(
        "LotAliasType", models.DO_NOTHING, db_column="ls_type", blank=True, null=True
    )
    kind_name = models.CharField(max_length=255, blank=True, null=True)
    version = AutoIncVersionField()

    class Meta:
        db_table = "lot_alias_kind"


class LotAliasType(models.Model):
    type_name = models.CharField(max_length=255, blank=True, null=True)
    version = AutoIncVersionField()

    class Meta:
        db_table = "lot_alias_type"


class LsInteraction(AbstractThing):
    first_thing_id = models.BigIntegerField()
    second_thing_id = models.BigIntegerField()

    class Meta:
        db_table = "ls_interaction"


class LsRole(AbstractKindConstrained):
    role_description = models.CharField(max_length=200, blank=True, null=True)
    role_name = models.CharField(max_length=255)
    version = AutoIncVersionField()
    ls_type = models.CharField(max_length=64, blank=True, null=True)
    ls_kind = models.CharField(max_length=255, blank=True, null=True)
    ls_type_and_kind = models.ForeignKey(
        "RoleKind",
        models.DO_NOTHING,
        db_column="ls_type_and_kind",
        to_field="ls_type_and_kind",
        blank=True,
        null=True,
    )

    class Meta:
        db_table = "ls_role"
        unique_together = (("ls_type", "ls_kind", "role_name"),)

    @property
    def kind_model(self):
        return RoleKind


class LsTag(models.Model):
    recorded_date = models.DateTimeField(blank=True, null=True)
    tag_text = models.CharField(max_length=255, blank=True, null=True)
    version = AutoIncVersionField()

    class Meta:
        db_table = "ls_tag"


class LsThing(AbstractThing):
    class Meta:
        db_table = "ls_thing"


class LsThingLabel(AbstractLabel):
    lsthing = models.ForeignKey(LsThing, models.DO_NOTHING)
    ls_thing_type_and_kind = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = "ls_thing_label"


class LsThingState(AbstractState):
    lsthing = models.ForeignKey(LsThing, models.DO_NOTHING)

    class Meta:
        db_table = "ls_thing_state"


class LsThingValue(AbstractValue):
    lsthing_state = models.ForeignKey(LsThingState, models.DO_NOTHING)

    class Meta:
        db_table = "ls_thing_value"


class LsTransaction(models.Model):
    comments = models.CharField(max_length=255, blank=True, null=True)
    recorded_date = models.DateTimeField()
    version = AutoIncVersionField()
    recorded_by = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=64, blank=True, null=True)
    type = models.CharField(max_length=64, blank=True, null=True)

    class Meta:
        db_table = "ls_transaction"


class LsthingTag(models.Model):
    lsthing = models.OneToOneField(
        LsThing, models.DO_NOTHING, primary_key=True
    )  # The composite primary key (lsthing_id, tag_id) found, that is not supported. The first column is selected.
    tag = models.ForeignKey(LsTag, models.DO_NOTHING)

    class Meta:
        db_table = "lsthing_tag"
        unique_together = (("lsthing", "tag"),)


class Operator(models.Model):
    code = models.CharField(max_length=255, blank=True, null=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    version = AutoIncVersionField()

    class Meta:
        db_table = "operator"


class OperatorKind(models.Model):
    kind_name = models.CharField(max_length=64)
    ls_type_and_kind = models.CharField(
        unique=True, max_length=255, blank=True, null=True
    )
    version = AutoIncVersionField()
    ls_type = models.ForeignKey("OperatorType", models.DO_NOTHING, db_column="ls_type")

    class Meta:
        db_table = "operator_kind"


class OperatorType(models.Model):
    type_name = models.CharField(unique=True, max_length=25)
    version = AutoIncVersionField()

    class Meta:
        db_table = "operator_type"


class Parent(models.Model):
    cd_id = models.IntegerField()
    common_name = models.CharField(max_length=1000, blank=True, null=True)
    corp_name = models.CharField(unique=True, max_length=255)
    ignore = models.BooleanField(blank=True, null=True)
    mol_formula = models.CharField(max_length=4000, blank=True, null=True)
    mol_structure = models.TextField(blank=True, null=True)
    mol_weight = models.FloatField(blank=True, null=True)
    parent_number = models.BigIntegerField()
    registration_date = models.DateTimeField(blank=True, null=True)
    stereo_comment = models.CharField(max_length=1000, blank=True, null=True)
    version = AutoIncVersionField()
    chemist = models.CharField(blank=True, null=True)
    stereo_category = models.ForeignKey(
        "StereoCategory",
        models.DO_NOTHING,
        db_column="stereo_category",
        blank=True,
        null=True,
    )
    modified_date = models.DateTimeField(blank=True, null=True)
    modified_by = models.CharField(blank=True, null=True)
    bulk_load_file = models.ForeignKey(
        BulkLoadFile,
        models.DO_NOTHING,
        db_column="bulk_load_file",
        blank=True,
        null=True,
    )
    parent_annotation = models.ForeignKey(
        "ParentAnnotation",
        models.DO_NOTHING,
        db_column="parent_annotation",
        blank=True,
        null=True,
    )
    compound_type = models.ForeignKey(
        CompoundType,
        models.DO_NOTHING,
        db_column="compound_type",
        blank=True,
        null=True,
    )
    comment = models.TextField(blank=True, null=True)
    exact_mass = models.FloatField(blank=True, null=True)
    registered_by = models.CharField(blank=True, null=True)
    is_mixture = models.BooleanField(blank=True, null=True)

    class Meta:
        db_table = "parent"


class ParentAlias(models.Model):
    version = AutoIncVersionField()
    parent = models.ForeignKey(
        Parent, models.DO_NOTHING, db_column="parent", blank=True, null=True
    )
    alias_name = models.CharField(max_length=255, blank=True, null=True)
    ls_type = models.CharField(max_length=255, blank=True, null=True)
    ls_kind = models.CharField(max_length=255, blank=True, null=True)
    ignored = models.BooleanField(blank=True, null=True)
    deleted = models.BooleanField(blank=True, null=True)
    preferred = models.BooleanField(blank=True, null=True)
    sort_id = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = "parent_alias"


class ParentAliasKind(models.Model):
    ls_type = models.ForeignKey(
        "ParentAliasType", models.DO_NOTHING, db_column="ls_type", blank=True, null=True
    )
    kind_name = models.CharField(max_length=255, blank=True, null=True)
    version = AutoIncVersionField()

    class Meta:
        db_table = "parent_alias_kind"


class ParentAliasType(models.Model):
    type_name = models.CharField(max_length=255, blank=True, null=True)
    version = AutoIncVersionField()

    class Meta:
        db_table = "parent_alias_type"


class ParentAnnotation(models.Model):
    code = models.CharField(unique=True, max_length=255)
    name = models.CharField(max_length=255)
    display_order = models.IntegerField(blank=True, null=True)
    comment = models.CharField(max_length=255, blank=True, null=True)
    version = AutoIncVersionField()

    class Meta:
        db_table = "parent_annotation"


class PhysicalState(models.Model):
    code = models.CharField(max_length=100, blank=True, null=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    version = AutoIncVersionField()

    class Meta:
        db_table = "physical_state"


class PreDefCorpName(models.Model):
    comment = models.CharField(max_length=255, blank=True, null=True)
    corp_name = models.CharField(max_length=64, blank=True, null=True)
    corp_number = models.BigIntegerField()
    skip = models.BooleanField(blank=True, null=True)
    used = models.BooleanField(blank=True, null=True)
    version = AutoIncVersionField()

    class Meta:
        db_table = "pre_def_corp_name"


class Protocol(AbstractThing, AbstractKindConstrained):
    thing_type_and_kind = "document_protocol"
    default_type_and_kind = "default_default"
    label_prefix = "PROT"
    ls_type_and_kind = models.ForeignKey(
        "ProtocolKind",
        models.DO_NOTHING,
        db_column="ls_type_and_kind",
        to_field="ls_type_and_kind",
        blank=True,
        null=True,
    )
    short_description = models.CharField(max_length=1000, blank=True, null=True)

    class Meta:
        db_table = "protocol"

    @property
    def kind_model(self):
        return ProtocolKind


class ProtocolKind(AbstractKind):
    ls_type = models.ForeignKey("ProtocolType", models.DO_NOTHING, db_column="ls_type")

    def __str__(self) -> str:
        return super().__str__()

    def save(self, *args, **kwargs):
        # Set ls_type_and_kind based on the related ProtocolType instance
        if self.ls_type:
            self.ls_type_and_kind = f"{self.ls_type.type_name}_{self.kind_name}"
        super(ProtocolKind, self).save(*args, **kwargs)

    class Meta:
        db_table = "protocol_kind"


class ProtocolLabel(AbstractLabel, AbstractKindConstrained):
    ls_type_and_kind = models.ForeignKey(
        LabelKind,
        models.DO_NOTHING,
        db_column="ls_type_and_kind",
        to_field="ls_type_and_kind",
        blank=True,
        null=True,
    )
    protocol = models.ForeignKey(Protocol, models.DO_NOTHING)

    class Meta:
        db_table = "protocol_label"

    @property
    def kind_model(self):
        return LabelKind


class ProtocolState(AbstractState):
    ls_type_and_kind = models.ForeignKey(
        "StateKind",
        models.DO_NOTHING,
        db_column="ls_type_and_kind",
        to_field="ls_type_and_kind",
        blank=True,
        null=True,
    )
    protocol = models.ForeignKey(Protocol, models.DO_NOTHING)

    class Meta:
        db_table = "protocol_state"


class ProtocolTag(models.Model):
    protocol = models.OneToOneField(
        Protocol, models.DO_NOTHING, primary_key=True
    )  # The composite primary key (protocol_id, tag_id) found, that is not supported. The first column is selected.
    tag = models.ForeignKey(LsTag, models.DO_NOTHING)

    class Meta:
        db_table = "protocol_tag"
        unique_together = (("protocol", "tag"),)


class ProtocolType(models.Model):
    type_name = models.CharField(unique=True, max_length=128)
    version = AutoIncVersionField()

    class Meta:
        db_table = "protocol_type"


class ProtocolValue(AbstractValue):
    ls_type_and_kind = models.ForeignKey(
        "ValueKind",
        models.DO_NOTHING,
        db_column="ls_type_and_kind",
        to_field="ls_type_and_kind",
        blank=True,
        null=True,
    )
    protocol_state = models.ForeignKey(ProtocolState, models.DO_NOTHING)

    class Meta:
        db_table = "protocol_value"


class PurityMeasuredBy(models.Model):
    code = models.CharField(max_length=255, blank=True, null=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    version = AutoIncVersionField()

    class Meta:
        db_table = "purity_measured_by"


class QcCompound(models.Model):
    version = AutoIncVersionField()
    run_number = models.IntegerField(blank=True, null=True)
    qc_date = models.DateTimeField(blank=True, null=True)
    parent_id = models.BigIntegerField(blank=True, null=True)
    display_change = models.BooleanField(blank=True, null=True)
    corp_name = models.CharField(max_length=255, blank=True, null=True)
    stereo_category = models.CharField(max_length=255, blank=True, null=True)
    stereo_comment = models.CharField(max_length=255, blank=True, null=True)
    dupe_count = models.IntegerField(blank=True, null=True)
    dupe_corp_name = models.CharField(max_length=255, blank=True, null=True)
    alias = models.CharField(max_length=1024, blank=True, null=True)
    cd_id = models.IntegerField()
    mol_structure = models.TextField(blank=True, null=True)
    comment = models.CharField(max_length=2000, blank=True, null=True)
    ignore = models.BooleanField(blank=True, null=True)

    class Meta:
        db_table = "qc_compound"


class RoleKind(AbstractKind):
    ls_type = models.ForeignKey("RoleType", models.DO_NOTHING, db_column="ls_type")

    class Meta:
        db_table = "role_kind"


class RoleType(models.Model):
    type_name = models.CharField(unique=True, max_length=128)
    version = AutoIncVersionField()

    class Meta:
        db_table = "role_type"


class Salt(models.Model):
    abbrev = models.CharField(max_length=100, blank=True, null=True)
    cd_id = models.IntegerField()
    formula = models.CharField(max_length=255, blank=True, null=True)
    ignore = models.BooleanField(blank=True, null=True)
    mol_structure = models.TextField(blank=True, null=True)
    mol_weight = models.FloatField(blank=True, null=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    original_structure = models.TextField(blank=True, null=True)
    version = AutoIncVersionField()
    charge = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = "salt"


class SaltForm(models.Model):
    cd_id = models.IntegerField()
    cas_number = models.CharField(max_length=255, blank=True, null=True)
    corp_name = models.CharField(max_length=255, blank=True, null=True)
    ignore = models.BooleanField(blank=True, null=True)
    mol_structure = models.TextField(blank=True, null=True)
    registration_date = models.DateTimeField(blank=True, null=True)
    salt_weight = models.FloatField(blank=True, null=True)
    version = AutoIncVersionField()
    chemist = models.CharField(blank=True, null=True)
    parent = models.ForeignKey(
        Parent, models.DO_NOTHING, db_column="parent", blank=True, null=True
    )
    bulk_load_file = models.ForeignKey(
        BulkLoadFile,
        models.DO_NOTHING,
        db_column="bulk_load_file",
        blank=True,
        null=True,
    )

    class Meta:
        db_table = "salt_form"


class SaltFormAlias(models.Model):
    version = AutoIncVersionField()
    salt_form = models.ForeignKey(
        SaltForm, models.DO_NOTHING, db_column="salt_form", blank=True, null=True
    )
    alias_name = models.CharField(max_length=255, blank=True, null=True)
    ls_type = models.CharField(max_length=255, blank=True, null=True)
    ls_kind = models.CharField(max_length=255, blank=True, null=True)
    ignored = models.BooleanField(blank=True, null=True)
    deleted = models.BooleanField(blank=True, null=True)
    preferred = models.BooleanField(blank=True, null=True)

    class Meta:
        db_table = "salt_form_alias"


class SaltFormAliasKind(AbstractKind):
    ls_type = models.ForeignKey(
        "SaltFormAliasType",
        models.DO_NOTHING,
        db_column="ls_type",
        blank=True,
        null=True,
    )
    kind_name = models.CharField(max_length=255, blank=True, null=True)
    version = AutoIncVersionField()

    class Meta:
        db_table = "salt_form_alias_kind"


class SaltFormAliasType(models.Model):
    type_name = models.CharField(max_length=255, blank=True, null=True)
    version = AutoIncVersionField()

    class Meta:
        db_table = "salt_form_alias_type"


class SaltLoader(models.Model):
    description = models.CharField(max_length=255, blank=True, null=True)
    file_name = models.CharField(max_length=255, blank=True, null=True)
    loaded_date = models.DateTimeField(blank=True, null=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    number_of_salts = models.BigIntegerField()
    size = models.BigIntegerField()
    uploaded = models.BooleanField(blank=True, null=True)
    version = AutoIncVersionField()

    class Meta:
        db_table = "salt_loader"


class SchemaVersion(models.Model):
    installed_rank = models.IntegerField(primary_key=True)
    version = models.CharField(max_length=50, blank=True, null=True)
    description = models.CharField(max_length=200)
    type = models.CharField(max_length=20)
    script = models.CharField(max_length=1000)
    checksum = models.IntegerField(blank=True, null=True)
    installed_by = models.CharField(max_length=100)
    installed_on = models.DateTimeField()
    execution_time = models.IntegerField()
    success = models.BooleanField()

    class Meta:
        db_table = "schema_version"


class SolutionUnit(models.Model):
    code = models.CharField(max_length=255, blank=True, null=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    version = AutoIncVersionField()

    class Meta:
        db_table = "solution_unit"


class StandardizationDryRunCompound(models.Model):
    version = AutoIncVersionField()
    run_number = models.IntegerField(blank=True, null=True)
    qc_date = models.DateTimeField(blank=True, null=True)
    parent = models.ForeignKey(Parent, models.DO_NOTHING, blank=True, null=True)
    changed_structure = models.BooleanField(blank=True, null=True)
    new_mol_weight = models.FloatField(blank=True, null=True)
    delta_mol_weight = models.FloatField(blank=True, null=True)
    existing_duplicate_count = models.IntegerField(blank=True, null=True)
    new_duplicate_count = models.IntegerField(blank=True, null=True)
    new_duplicates = models.TextField(blank=True, null=True)
    display_change = models.BooleanField(blank=True, null=True)
    existing_duplicates = models.TextField(blank=True, null=True)
    as_drawn_display_change = models.BooleanField(blank=True, null=True)
    corp_name = models.CharField(max_length=255, blank=True, null=True)
    alias = models.CharField(max_length=1024, blank=True, null=True)
    cd_id = models.IntegerField()
    mol_structure = models.TextField(blank=True, null=True)
    comment = models.CharField(max_length=2000, blank=True, null=True)
    registration_status = models.CharField(max_length=255, blank=True, null=True)
    registration_comment = models.TextField(blank=True, null=True)
    standardization_status = models.CharField(max_length=255, blank=True, null=True)
    standardization_comment = models.TextField(blank=True, null=True)
    ignore = models.BooleanField(blank=True, null=True)
    sync_status = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = "standardization_dry_run_compound"


class StandardizationHistory(models.Model):
    version = AutoIncVersionField()
    recorded_date = models.DateTimeField(blank=True, null=True)
    settings_hash = models.IntegerField(blank=True, null=True)
    settings = models.TextField(blank=True, null=True)
    dry_run_status = models.CharField(max_length=20, blank=True, null=True)
    dry_run_start = models.DateTimeField(blank=True, null=True)
    dry_run_complete = models.DateTimeField(blank=True, null=True)
    standardization_status = models.CharField(max_length=20, blank=True, null=True)
    standardization_user = models.TextField(blank=True, null=True)
    standardization_reason = models.TextField(blank=True, null=True)
    standardization_start = models.DateTimeField(blank=True, null=True)
    standardization_complete = models.DateTimeField(blank=True, null=True)
    structures_standardized_count = models.IntegerField(blank=True, null=True)
    structures_updated_count = models.IntegerField(blank=True, null=True)
    new_duplicate_count = models.IntegerField(blank=True, null=True)
    existing_duplicate_count = models.IntegerField(blank=True, null=True)
    display_change_count = models.IntegerField(blank=True, null=True)
    as_drawn_display_change_count = models.IntegerField(blank=True, null=True)
    changed_structure_count = models.IntegerField(blank=True, null=True)
    standardization_error_count = models.IntegerField(blank=True, null=True)
    registration_error_count = models.IntegerField(blank=True, null=True)
    dry_run_standardization_changes_count = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = "standardization_history"


class StateKind(AbstractKind):
    kind_name = models.CharField(max_length=64)
    ls_type_and_kind = models.CharField(
        unique=True, max_length=255, blank=True, null=True
    )
    version = AutoIncVersionField()
    ls_type = models.ForeignKey("StateType", models.DO_NOTHING, db_column="ls_type")

    class Meta:
        db_table = "state_kind"


class StateType(models.Model):
    type_name = models.CharField(unique=True, max_length=64)
    version = AutoIncVersionField()

    class Meta:
        db_table = "state_type"


class StereoCategory(models.Model):
    code = models.CharField(max_length=255, blank=True, null=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    version = AutoIncVersionField()

    class Meta:
        db_table = "stereo_category"


class StructureKind(AbstractKind):
    kind_name = models.CharField(max_length=64)
    ls_type_and_kind = models.CharField(
        unique=True, max_length=255, blank=True, null=True
    )
    version = AutoIncVersionField()
    ls_type = models.ForeignKey("StructureType", models.DO_NOTHING, db_column="ls_type")

    class Meta:
        db_table = "structure_kind"


class StructureType(models.Model):
    type_name = models.CharField(unique=True, max_length=64)
    version = AutoIncVersionField()

    class Meta:
        db_table = "structure_type"


class Subject(AbstractThing):
    thing_type_and_kind = "document_subject"
    label_prefix = "SUBJ"

    class Meta:
        db_table = "subject"


class SubjectLabel(AbstractLabel, AbstractKindConstrained):
    ls_type_and_kind = models.ForeignKey(
        LabelKind,
        models.DO_NOTHING,
        db_column="ls_type_and_kind",
        to_field="ls_type_and_kind",
        blank=True,
        null=True,
    )
    subject = models.ForeignKey(Subject, models.DO_NOTHING)

    class Meta:
        db_table = "subject_label"

    @property
    def kind_model(self):
        return LabelKind


class SubjectState(AbstractState):
    ls_type_and_kind = models.ForeignKey(
        StateKind,
        models.DO_NOTHING,
        db_column="ls_type_and_kind",
        to_field="ls_type_and_kind",
        blank=True,
        null=True,
    )
    subject = models.ForeignKey(Subject, models.DO_NOTHING)

    class Meta:
        db_table = "subject_state"


class SubjectValue(AbstractValue):
    ls_type_and_kind = models.ForeignKey(
        "ValueKind",
        models.DO_NOTHING,
        db_column="ls_type_and_kind",
        to_field="ls_type_and_kind",
        blank=True,
        null=True,
    )
    subject_state = models.ForeignKey(SubjectState, models.DO_NOTHING)

    class Meta:
        db_table = "subject_value"


class TempSelectTable(models.Model):
    ls_transaction = models.BigIntegerField(blank=True, null=True)
    number_var = models.BigIntegerField(blank=True, null=True)
    recorded_by = models.CharField(max_length=255, blank=True, null=True)
    recorded_date = models.DateTimeField()
    string_var = models.CharField(max_length=255, blank=True, null=True)
    version = AutoIncVersionField()

    class Meta:
        db_table = "temp_select_table"


class ThingKind(AbstractKind):
    ls_type = models.ForeignKey("ThingType", models.DO_NOTHING, db_column="ls_type")

    class Meta:
        db_table = "thing_kind"


class ThingPage(models.Model):
    archived = models.BooleanField()
    current_editor = models.CharField(max_length=255)
    ignored = models.BooleanField()
    modified_by = models.CharField(max_length=255)
    modified_date = models.DateTimeField()
    page_content = models.TextField(blank=True, null=True)
    page_name = models.CharField(max_length=255, blank=True, null=True)
    recorded_by = models.CharField(max_length=255)
    recorded_date = models.DateTimeField()
    version = AutoIncVersionField()
    ls_transaction = models.ForeignKey(
        LsTransaction,
        models.DO_NOTHING,
        db_column="ls_transaction",
        blank=True,
        null=True,
    )
    thing_id = models.BigIntegerField()

    class Meta:
        db_table = "thing_page"


class ThingPageArchive(models.Model):
    archived = models.BooleanField()
    current_editor = models.CharField(max_length=255, blank=True, null=True)
    ignored = models.BooleanField()
    ls_transaction = models.BigIntegerField(blank=True, null=True)
    modified_by = models.CharField(max_length=255)
    modified_date = models.DateTimeField()
    page_content = models.TextField(blank=True, null=True)
    page_name = models.CharField(max_length=255, blank=True, null=True)
    page_version = AutoIncVersionField()
    recorded_by = models.CharField(max_length=255)
    recorded_date = models.DateTimeField()
    thing_id = models.BigIntegerField(blank=True, null=True)
    version = AutoIncVersionField()

    class Meta:
        db_table = "thing_page_archive"


class ThingType(models.Model):
    type_name = models.CharField(unique=True, max_length=128)
    version = AutoIncVersionField()

    class Meta:
        db_table = "thing_type"


class TreatmentGroup(AbstractThing):
    thing_type_and_kind = "document_treatment group"
    label_prefix = "TG"

    class Meta:
        db_table = "treatment_group"


class TreatmentGroupLabel(AbstractLabel, AbstractKindConstrained):
    ls_type_and_kind = models.ForeignKey(
        LabelKind,
        models.DO_NOTHING,
        db_column="ls_type_and_kind",
        to_field="ls_type_and_kind",
        blank=True,
        null=True,
    )
    treatment_group = models.ForeignKey(TreatmentGroup, models.DO_NOTHING)

    class Meta:
        db_table = "treatment_group_label"

    @property
    def kind_model(self):
        return LabelKind


class TreatmentGroupState(AbstractState):
    ls_type_and_kind = models.ForeignKey(
        StateKind,
        models.DO_NOTHING,
        db_column="ls_type_and_kind",
        to_field="ls_type_and_kind",
        blank=True,
        null=True,
    )
    treatment_group = models.ForeignKey(TreatmentGroup, models.DO_NOTHING)

    class Meta:
        db_table = "treatment_group_state"


class TreatmentGroupValue(AbstractValue):
    ls_type_and_kind = models.ForeignKey(
        "ValueKind",
        models.DO_NOTHING,
        db_column="ls_type_and_kind",
        to_field="ls_type_and_kind",
        blank=True,
        null=True,
    )
    treatment_state = models.ForeignKey(TreatmentGroupState, models.DO_NOTHING)

    class Meta:
        db_table = "treatment_group_value"


class TreatmentgroupSubject(models.Model):
    subject = models.OneToOneField(
        Subject, models.DO_NOTHING, primary_key=True
    )  # The composite primary key (subject_id, treatment_group_id) found, that is not supported. The first column is selected.
    treatment_group = models.ForeignKey(TreatmentGroup, models.DO_NOTHING)

    class Meta:
        db_table = "treatmentgroup_subject"
        unique_together = (("subject", "treatment_group"),)


class UncertaintyKind(AbstractKind):
    class Meta:
        db_table = "uncertainty_kind"


class Unit(models.Model):
    code = models.CharField(max_length=255, blank=True, null=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    version = AutoIncVersionField()

    class Meta:
        db_table = "unit"


class UnitKind(AbstractKind):

    ls_type = models.ForeignKey("UnitType", models.DO_NOTHING, db_column="ls_type")

    class Meta:
        db_table = "unit_kind"


class UnitType(models.Model):
    type_name = models.CharField(unique=True, max_length=64)
    version = AutoIncVersionField()

    class Meta:
        db_table = "unit_type"


class UpdateLog(models.Model):
    comments = models.CharField(max_length=512, blank=True, null=True)
    ls_transaction = models.BigIntegerField(blank=True, null=True)
    recorded_by = models.CharField(max_length=255, blank=True, null=True)
    recorded_date = models.DateTimeField()
    thing = models.BigIntegerField(blank=True, null=True)
    update_action = models.CharField(max_length=255, blank=True, null=True)
    version = AutoIncVersionField()

    class Meta:
        db_table = "update_log"


class ValueKind(AbstractKind):

    ls_type = models.ForeignKey("ValueType", models.DO_NOTHING, db_column="ls_type")

    class Meta:
        db_table = "value_kind"


class ValueType(models.Model):
    type_name = models.CharField(unique=True, max_length=64)
    version = AutoIncVersionField()

    class Meta:
        db_table = "value_type"


class Vendor(models.Model):
    code = models.CharField(max_length=255, blank=True, null=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    version = AutoIncVersionField()

    class Meta:
        db_table = "vendor"
