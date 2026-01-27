from rest_framework import serializers
from .models import Document

class DocumentSerializer(serializers.ModelSerializer):
    # Format the date specifically for the frontend
    upload_date = serializers.SerializerMethodField()
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = [
            'id', 
            'title', 
            'category', 
            'file_url', 
            'file_size', 
            'file_type', 
            'upload_date'
        ]
        read_only_fields = ['file_size', 'file_type', 'upload_date']

    def get_upload_date(self, obj):
        # Returns format like: "Oct 12, 2024"
        return obj.created_at.strftime("%b %d, %Y")

    def get_file_url(self, obj):
        request = self.context.get('request')
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return None