import stripe
stripe.api_key = "sk_test_4eC39HqLyjWDarjtT1zdp7dc"

# Retrieve the account information
def check_verified(account_id):
    account = stripe.Account.retrieve(account_id)
    if account.charges_enabled and account.payouts_enabled:
        return True
    else:
        return False
    
    