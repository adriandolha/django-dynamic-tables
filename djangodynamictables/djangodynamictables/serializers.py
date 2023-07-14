from rest_framework import serializers
from rest_framework.exceptions import ValidationError


class FieldSerializer(serializers.Serializer):
    type = serializers.ChoiceField(choices=['string', 'number', 'boolean'])
    title = serializers.CharField(min_length=3, max_length=100)


class TableSerializer(serializers.Serializer):
    name = serializers.CharField(min_length=3, max_length=100)
    fields = serializers.ListField(child=FieldSerializer())

    def validate_fields(self, fields):
        if len(fields) > 10:
            raise ValidationError("Maximum of 10 fields allowed.")
        return fields
