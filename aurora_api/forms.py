from django import forms



class ContactForm(forms.Form):
    SERVICE_CHOICES = [
        ('', 'Select a Department'),
        ('council_tax', 'Council Tax'),
        ('business_rates', 'Business Rates'),
        ('report_it', 'Report It'),
        ('parking', 'Parking'),
        ('registration_services', 'Registration Services'),
        ('waste_recycling', 'Waste & Recycling'),
    
    ]
    
    service_type = forms.ChoiceField(choices=SERVICE_CHOICES)
    first_name = forms.CharField(required=False, widget=forms.TextInput(attrs={'size':10, 'placeholder':'John', 'style': 'max-width: 300px; color:black;', 'class':'form-control'}))
    last_name = forms.CharField(required=False, widget=forms.TextInput(attrs={'size':10, 'placeholder':'Doe', 'style': 'max-width: 300px;', 'class':'form-control'}))
    phone_number = forms.CharField(required=False, widget=forms.TextInput(attrs={'size':10, 'placeholder':'Phone No', 'style': 'max-width: 300px;', 'class':'form-control'}))
    email = forms.CharField(required=False, widget=forms.TextInput(attrs={'size':10, 'placeholder':'example@email.com', 'style': 'max-width: 300px;', 'class':'form-control'}))
    request = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 4, 'placeholder': 'Nature of your enquiry...', 'style': 'max-width: 300px;', 'class': 'form-control'}))




