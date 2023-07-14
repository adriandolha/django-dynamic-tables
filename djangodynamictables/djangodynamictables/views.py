from django.db.backends.base.schema import BaseDatabaseSchemaEditor
from django.db.models import Count
from django.shortcuts import get_object_or_404
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework import status, serializers
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from django.apps import apps
from django.db import models, migrations

from . import dynamic_models
from .models import DynamicModelMetadata
from .serializers import TableSerializer
from django.db import connection, models

APP_LABEL = 'djangodynamictables'


class CustomAuthToken(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({'token': token.key})


class TableAPIView(APIView):
    serializer_class = TableSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        fields = serializer.validated_data['fields']
        model_name = serializer.validated_data['name']
        user_tables_count = DynamicModelMetadata.objects.filter(owner=self.request.user).aggregate(count=Count('id'))[
            'count']
        # todo: move to settings
        if user_tables_count > 10:
            raise ValidationError('Exceeded max tables allowed.')
        DynamicModel = dynamic_models.create_dynamic_model(fields, model_name)
        if self.model_table_exists(DynamicModel):
            return Response({'message': 'Table already exists.'}, status=status.HTTP_409_CONFLICT)

        dynamic_models.create_model_schema(DynamicModel)
        DynamicModelMetadata.objects.create(
            model_name=model_name,
            fields=fields,
            owner=self.request.user
        )

        return Response({'message': 'Dynamic model created successfully.'}, status=status.HTTP_201_CREATED)

    def put(self, request, id):
        print(f'Updating model {id}')
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        fields = serializer.validated_data['fields']
        model_name = serializer.validated_data['name']
        existing_model_metadata = self.get_model_metadata_by_name(model_name)
        if existing_model_metadata is None:
            return Response({'message': 'Table does not exist.'}, status=status.HTTP_404_NOT_FOUND)
        print(existing_model_metadata.fields)
        CurrentDynamicModel = dynamic_models.create_dynamic_model(existing_model_metadata.fields, model_name)
        UpdatedDynamicModel = dynamic_models.create_dynamic_model(fields, model_name)

        dynamic_models.update_model_schema(CurrentDynamicModel, UpdatedDynamicModel, serializer.validated_data,
                                           existing_model_metadata)
        existing_model_metadata.fields = fields
        existing_model_metadata.save()
        return Response({'message': 'Dynamic model updated successfully.'}, status=status.HTTP_200_OK)

    def get_model_metadata_by_name(self, model_name) -> DynamicModelMetadata:
        return DynamicModelMetadata.objects.filter(model_name=model_name, owner=self.request.user).first()

    def model_table_exists(self, DynamicModel):
        return DynamicModel._meta.db_table in connection.introspection.table_names()


class TableRowAPIView(APIView):
    serializer_class = TableSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, id: str):
        dynamic_model_metadata = get_object_or_404(DynamicModelMetadata, owner=request.user, model_name=id)
        DynamicModel = dynamic_models.create_dynamic_model(dynamic_model_metadata.fields, id)
        serializer = create_dynamic_serializer(dynamic_model_metadata.fields)
        data = serializer(DynamicModel.objects.all()[:1000], many=True).data

        return Response(data, status=200)

    def post(self, request, id: str):
        dynamic_model_metadata = get_object_or_404(DynamicModelMetadata, owner=request.user, model_name=id)
        serializer = create_dynamic_serializer(dynamic_model_metadata.fields)(data=request.data)
        serializer.is_valid(raise_exception=True)
        DynamicModel = dynamic_models.create_dynamic_model(dynamic_model_metadata.fields, id)
        data_count = DynamicModel.objects.all().aggregate(count=Count('id'))[
            'count']
        # todo: move to settings
        if data_count > 10:
            raise ValidationError('Exceeded max rows allowed.')

        DynamicModel.objects.create(**serializer.validated_data)
        return Response({'message': 'Data saved successfully.'}, status=status.HTTP_201_CREATED)


def get_serializer_for_field_type(field_type: str):
    return {
        'string': serializers.CharField(min_length=3, max_length=100),
        'number': serializers.IntegerField(),
        'boolean': serializers.BooleanField(),
    }.get(field_type)


def create_dynamic_serializer(fields):
    fields_dict = {field['title']: get_serializer_for_field_type(field['type']) for field in fields}
    DynamicSerializer = type('DynamicSerializer', (serializers.Serializer,), fields_dict)
    return DynamicSerializer
