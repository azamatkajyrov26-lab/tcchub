from rest_framework import serializers

from .models import Activity, ActivityCompletion, Folder, FolderFile, Resource


class ResourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resource
        fields = ["id", "activity", "file", "file_type", "file_size", "external_url"]
        read_only_fields = ["id"]


class FolderFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = FolderFile
        fields = ["id", "folder", "file", "original_name"]
        read_only_fields = ["id"]


class FolderSerializer(serializers.ModelSerializer):
    files = FolderFileSerializer(many=True, read_only=True)

    class Meta:
        model = Folder
        fields = ["id", "activity", "name", "description", "files"]
        read_only_fields = ["id"]


class ActivitySerializer(serializers.ModelSerializer):
    resource = ResourceSerializer(read_only=True)
    folder = FolderSerializer(read_only=True)

    class Meta:
        model = Activity
        fields = [
            "id", "section", "activity_type", "title", "description",
            "order", "is_visible", "completion_type", "due_date",
            "resource", "folder",
        ]
        read_only_fields = ["id"]


class ActivityCompletionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActivityCompletion
        fields = ["id", "user", "activity", "completed", "completed_at"]
        read_only_fields = ["id", "user", "completed_at"]
