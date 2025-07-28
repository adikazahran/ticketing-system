# tickets/forms.py
from django import forms
from .models import Ticket, Comment
from django.contrib.auth.models import User

class TicketForm(forms.ModelForm):
    assigned_to = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True).order_by('username'),
        required=False,
        empty_label="Pilih Pengguna (Opsional)"
    )

    class Meta:
        model = Ticket
        fields = ['title', 'description', 'status', 'priority', 'assigned_to']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5, 'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'title': 'Judul Tiket',
            'description': 'Deskripsi Tiket',
            'status': 'Status',
            'priority': 'Prioritas',
            'assigned_to': 'Ditugaskan Kepada',
        }

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Tambahkan komentar...', 'class': 'form-control'}),
        }
        labels = {
            'content': 'Komentar',
        }