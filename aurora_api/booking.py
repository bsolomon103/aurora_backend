from .models import Treatments
def costs(category, customer):
    category = category.title()
    treatment = Treatments.objects.get(customer_name=customer, treatment__contains=category)
    return treatment


