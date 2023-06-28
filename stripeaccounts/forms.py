from django import forms

class StripeForm(forms.Form):
    description = forms.CharField(widget=forms.TextInput(attrs={'size':25,'placeholder':'Product/Business Description','style': 'max-width: 300px;', 'class':'form-control'}))
    mcc =  forms.CharField(widget=forms.TextInput(attrs={'size':25,'placeholder':'Merchant Category Code','style': 'max-width: 300px;', 'class':'form-control'}))
    name = forms.CharField(widget=forms.TextInput(attrs={'size':25,'placeholder':'Business Name','style': 'max-width: 300px;', 'class':'form-control'}))
    phone = forms.CharField(widget=forms.TextInput(attrs={'size':25,'placeholder':'Support Phone','style': 'max-width: 300px;', 'class':'form-control'}))