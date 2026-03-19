from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django import forms # forms eklendi
from .models import Comment, Rating, User # User modeli import edildi

User = get_user_model()

class CustomUserCreationForm(UserCreationForm):
    # Kullanıcı adı alanını özelleştir
    username = forms.CharField(
        max_length=33, # Karakter limitini 33 yap
        help_text="Zorunlu. 33 karakter ya da daha az olmalı. Sadece harfler, rakamlar ve @/./+/-/_ karakterleri kullanılabilir.",
        label="Kullanıcı adı",
        widget=forms.TextInput(attrs={'autocomplete': 'username'})
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'first_name', 'last_name') # bio kaldırıldı, username Meta\'dan da kaldırılabilir veya bırakılabilir.

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('content',)
        widgets = {
            'content': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Yorumunuzu yazın...'}),
        }
        labels = {
            'content': '' # Etiketi gizleyelim, placeholder yeterli
        }

class RatingForm(forms.ModelForm):
    class Meta:
        model = Rating
        fields = ('score',)
        widgets = {
            'score': forms.Select(attrs={'class': 'form-select form-select-sm'})
        }
        labels = {
            'score': 'Puanınız'
        }

class UserProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        # Kullanıcının değiştirmesine izin verilen alanlar:
        fields = ('first_name', 'last_name', 'email', 'bio', 'profile_picture')
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
            'profile_picture': forms.FileInput(), # Profil resmi için dosya inputu
        }

class MessageForm(forms.Form):
    text = forms.CharField(widget=forms.Textarea(attrs={
        'rows': 3, 
        'placeholder': 'Mesajınızı yazın...', 
        'class': 'form-control', 
        'id': 'message-text-input'
        }), label="") 