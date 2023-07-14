from django.db import models, connection
from django.db.backends.base.schema import BaseDatabaseSchemaEditor
from rest_framework.exceptions import ValidationError

from djangodynamictables.models import DynamicModelMetadata

APP_LABEL = 'djangodynamictables'


def get_model_field(field_type: str):
    return {
        'string': models.CharField(max_length=100),
        'number': models.IntegerField(),
        'boolean': models.BooleanField()
    }.get(field_type)


def create_dynamic_model(fields, name):
    model_fields = {}
    for field in fields:
        field_type = field.get('type')
        field_title = field.get('title')
        model_fields[field_title] = get_model_field(field_type)
    DynamicModel = type(name,
                        (models.Model,),
                        {
                            **model_fields,
                            "Meta": type(
                                "Meta",
                                (),
                                {"app_label": APP_LABEL}
                            ),
                            "__module__": "database.models"
                        })
    return DynamicModel


def get_schema_editor() -> BaseDatabaseSchemaEditor:
    return connection.schema_editor()


def create_model_schema(DynamicModel):
    with get_schema_editor() as schema_editor:
        schema_editor.create_model(DynamicModel)


def update_model_schema(CurrentDynamicModel, UpdatedDynamicModel, updated_model_data: dict,
                        current_model_metadata: DynamicModelMetadata):
    print(CurrentDynamicModel.__dict__)
    print(UpdatedDynamicModel.__dict__)
    with get_schema_editor() as schema_editor:
        updated_model_fields = updated_model_data['fields']
        for current_field in current_model_metadata.fields:
            field_name = current_field['title']
            updated_field = next(
                filter(lambda field: field['title'] == field_name, updated_model_fields), None)
            is_field_removed = updated_field is None

            print(f'Is field {field_name} removed = {is_field_removed}')
            if is_field_removed:
                field_name = current_field['title']
                dynamic_model_field = CurrentDynamicModel._meta.get_field(field_name)
                print(f'Removing field {dynamic_model_field}')
                schema_editor.remove_field(CurrentDynamicModel, dynamic_model_field)
            else:
                if current_field['type'] != updated_field['type']:
                    raise ValidationError('Changing field type not allowed.')
        for updated_model_field in updated_model_fields:
            print('Update model field:')
            print(updated_model_field)
            print(current_model_metadata.fields)
            updated_field = next(
                filter(lambda field: field['title'] == updated_model_field['title'], current_model_metadata.fields),
                None)

            if updated_field is None:
                field_name = updated_model_field['title']
                dynamic_model_field = UpdatedDynamicModel._meta.get_field(field_name)
                print(f'Adding field {dynamic_model_field}')
                definition, params = schema_editor.column_sql(UpdatedDynamicModel, dynamic_model_field,
                                                              include_default=True)
                print(definition, params)
                schema_editor.add_field(UpdatedDynamicModel, dynamic_model_field)
