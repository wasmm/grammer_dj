from django import forms
from .models import Acts_follow

class Add_Act_Form(forms.ModelForm):

    class Meta:
        model = Acts_follow
        fields = ('act', 'target', )




    
