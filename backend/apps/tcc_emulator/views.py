from rest_framework import viewsets
from rest_framework.permissions import AllowAny

from apps.tcc_emulator.models import EmulatedDataSource, EmulatedNodeStatus
from apps.tcc_emulator.serializers import (
    EmulatedDataSourceSerializer,
    EmulatedNodeStatusSerializer,
)


class EmulatedDataSourceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = EmulatedDataSource.objects.select_related("data_source")
    serializer_class = EmulatedDataSourceSerializer
    permission_classes = [AllowAny]


class EmulatedNodeStatusViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = EmulatedNodeStatus.objects.select_related("node")
    serializer_class = EmulatedNodeStatusSerializer
    permission_classes = [AllowAny]
    filterset_fields = ["node", "date"]
    ordering_fields = ["date", "throughput_percent"]
