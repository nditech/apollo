from .models import *
import django_filters
from django import forms


class MessageFilter(django_filters.FilterSet):
    class Meta:
        model = MessageLog
        fields = ['mobile', 'text', 'created']
    mobile = django_filters.CharFilter(widget=forms.TextInput(attrs={
        'class': 'span2',
        'placeholder': 'Mobile'
        }))
    text = django_filters.CharFilter(widget=forms.TextInput(attrs={
        'class': 'span2',
        'placeholder': 'Text'
        }), lookup_type='icontains')
