# recommender/forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import UserProfile, STRAND_CHOICES, YEAR_LEVEL_CHOICES

class UserSettingsForm(forms.ModelForm):
    email = forms.EmailField(required=True)
    
    new_password = forms.CharField(label='New Password (Optional)', 
                                   widget=forms.PasswordInput, 
                                   required=False)
    confirm_password = forms.CharField(label='Confirm New Password', 
                                       widget=forms.PasswordInput, 
                                       required=False)
    
    name = forms.CharField(max_length=100, required=True)
    age = forms.IntegerField(min_value=10, required=True)
    strand = forms.ChoiceField(choices=STRAND_CHOICES, required=True)
    university = forms.CharField(max_length=200, required=True)
    year_level = forms.ChoiceField(choices=YEAR_LEVEL_CHOICES, required=True)

    class Meta:
        model = UserProfile
        fields = ['name', 'age', 'strand', 'university', 'year_level']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if kwargs.get('instance') and kwargs['instance'].user:
            self.fields['email'].initial = kwargs['instance'].user.email
            
    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')

        if new_password or confirm_password:
            if not new_password or not confirm_password:
                raise ValidationError("If changing your password, both 'New Password' and 'Confirm New Password' fields must be filled.")

            if new_password != confirm_password:
                self.add_error('confirm_password', 'New passwords do not match.')
            
            try:
                validate_password(new_password, self.instance.user)
            except ValidationError as e:
                self.add_error('new_password', e)
                
        return cleaned_data

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    
    name = forms.CharField(max_length=100, required=True)
    age = forms.IntegerField(min_value=10, required=True)
    strand = forms.ChoiceField(choices=STRAND_CHOICES, required=True)
    university = forms.CharField(max_length=200, required=True)
    year_level = forms.ChoiceField(choices=YEAR_LEVEL_CHOICES, required=True)

    class Meta:
        model = User
        fields = ('username', 'email')
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']

        if commit:
            user.save()
            profile = UserProfile.objects.create(
                user=user,
                name=self.cleaned_data['name'],
                age=self.cleaned_data['age'],
                strand=self.cleaned_data['strand'],
                university=self.cleaned_data['university'],
                year_level=self.cleaned_data['year_level']
            )
        return user