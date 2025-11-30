from rest_framework import serializers
from .models import Book, QRCode


class QRCodeSerializer(serializers.ModelSerializer):
    qr_code_url = serializers.SerializerMethodField()

    class Meta:
        model = QRCode
        fields = ['id', 'qr_code', 'qr_code_url', 'created_at']
        read_only_fields = ['id', 'qr_code', 'qr_code_url', 'created_at']

    def get_qr_code_url(self, obj):
        if obj.qr_code:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.qr_code.url)
        return None


class BookSerializer(serializers.ModelSerializer):
    qrcode = QRCodeSerializer(read_only=True)

    class Meta:
        model = Book
        fields = ['id', 'title', 'author', 'isbn', 'description', 
                  'publication_date', 'created_at', 'updated_at', 'qrcode']
        read_only_fields = ['id', 'created_at', 'updated_at', 'qrcode']


class BookCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ['title', 'author', 'isbn', 'description', 'publication_date']


class QRCodeScanSerializer(serializers.Serializer):
    qr_data = serializers.CharField()


class GoogleBooksSearchSerializer(serializers.Serializer):
    """Serializer for Google Books search request."""
    query = serializers.CharField(help_text="Search query (title or author)")
    max_results = serializers.IntegerField(default=10, min_value=1, max_value=40, required=False, help_text="Maximum number of results (1-40)")


class GoogleBookSerializer(serializers.Serializer):
    """Serializer for Google Books API response."""
    title = serializers.CharField()
    authors = serializers.ListField(child=serializers.CharField(), allow_empty=True)
    publishedDate = serializers.CharField(allow_null=True, required=False)
    publisher = serializers.CharField(allow_null=True, required=False)
    description = serializers.CharField(allow_null=True, required=False)
    pageCount = serializers.IntegerField(allow_null=True, required=False)
    categories = serializers.ListField(child=serializers.CharField(), allow_empty=True, required=False)
    averageRating = serializers.FloatField(allow_null=True, required=False)
    ratingsCount = serializers.IntegerField(allow_null=True, required=False)
    language = serializers.CharField(allow_null=True, required=False)
    previewLink = serializers.URLField(allow_null=True, required=False)
    infoLink = serializers.URLField(allow_null=True, required=False)
    thumbnail = serializers.URLField(allow_null=True, required=False)
    isbn10 = serializers.CharField(allow_null=True, required=False)
    isbn13 = serializers.CharField(allow_null=True, required=False)
    googleBooksId = serializers.CharField(allow_null=True, required=False)
