#!/bin/bash
# Activate virtual enviromment
source ~/.env10/bin/activate
if [ $? -ne 0 ]; then
    echo "Failed to activate virtual environment."
    exit 1
fi
# Stripe key 
echo "Setting TEST_STRIPE_KEY"
export TEST_STRIPE_KEY=sk_test_51NJcbbD1RPWlDlnhXqjIuP8aAsbR3u08EO83FB2FHpfhG8nCgsUbD0fWolN5ifoptsh3ZZsKwOPHzHf1z4P1spU900V7doveLa
echo "TEST_STRIPE_KEY set to: $TEST_STRIPE_KEY"
# Webhook Secret
echo "Setting WEBHOOK_SECRET"
export WEBHOOK_SECRET=whsec_PB3S9Ir6ubMIv5N8t0jxum2wx1y9tlMf
echo "WEBHOOK_SECRET set to: $WEBHOOK_SECRET"
# OpenAI API
echo "Setting OPENAI_API_KEY" 
export OPENAI_API_KEY=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
echo "OPENAI_API_KEY set to: $OPENAI_API_KEY" 
# SMTP Password
echo "Setting SMTP_PASSWORD" 
export SMTP_PASSWORD="@Aurora24"
echo "SMTP_PASSWORD set to: $OPENAI_API_KEY" 

# Start nginx
sudo systemctl start nginx
# Start Django

echo "Process complete"

#python manage.py runserver 0.0.0.0:8080

