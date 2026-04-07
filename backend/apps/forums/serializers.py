from rest_framework import serializers

from .models import Discussion, Forum, Post


class PostSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.get_full_name", read_only=True)
    replies = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            "id", "discussion", "user", "user_name", "parent",
            "content", "created_at", "updated_at", "replies",
        ]
        read_only_fields = ["id", "user", "created_at", "updated_at"]

    def get_replies(self, obj):
        if obj.replies.exists():
            return PostSerializer(obj.replies.all(), many=True).data
        return []


class DiscussionSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.get_full_name", read_only=True)
    post_count = serializers.IntegerField(source="posts.count", read_only=True)

    class Meta:
        model = Discussion
        fields = [
            "id", "forum", "user", "user_name", "title",
            "pinned", "locked", "created_at", "post_count",
        ]
        read_only_fields = ["id", "user", "created_at"]


class DiscussionDetailSerializer(DiscussionSerializer):
    posts = PostSerializer(many=True, read_only=True)

    class Meta(DiscussionSerializer.Meta):
        fields = DiscussionSerializer.Meta.fields + ["posts"]


class ForumSerializer(serializers.ModelSerializer):
    discussion_count = serializers.IntegerField(source="discussions.count", read_only=True)

    class Meta:
        model = Forum
        fields = ["id", "activity", "forum_type", "is_anonymous", "discussion_count"]
        read_only_fields = ["id"]
