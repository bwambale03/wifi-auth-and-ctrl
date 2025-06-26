#!/bin/bash

# Configuration
ADMIN_USER="superadmin"
ADMIN_PASS="SecureRandomPassword2025!"
BASE_URL="http://localhost:5000"

# Step 0: Prompt for TOTP code
echo "Please enter the current TOTP code from your authenticator app:"
read TOTP_CODE

# Step 1: Prompt for plan selection
echo "Available Plans:"
echo "1. 1 Hour  - \$0.5"
echo "2. 1 Day   - \$2"
echo "3. 1 Week  - \$10"
while true; do
  echo "Enter the plan ID (1, 2, or 3):"
  read PLAN_ID
  if [[ "$PLAN_ID" =~ ^[1-3]$ ]]; then
    break
  else
    echo "Error: Invalid plan ID. Please enter 1, 2, or 3."
  fi
done

# Step 2: Prompt for quantity
while true; do
  echo "Enter the number of codes to generate (1-100):"
  read QUANTITY
  if [[ "$QUANTITY" =~ ^[1-9][0-9]?$|^100$ ]]; then
    break
  else
    echo "Error: Quantity must be an integer between 1 and 100."
  fi
done

# Step 3: Log in with username and password
echo "Step 3: Logging in..."
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/admin/login" \
  -H "Content-Type: application/json" \
  -d "{\"username\": \"$ADMIN_USER\", \"password\": \"$ADMIN_PASS\"}" \
  -c cookies.txt)

echo "Login Response:"
echo "$LOGIN_RESPONSE" | jq .

# Extract temp_token
TEMP_TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.temp_token')
if [ -z "$TEMP_TOKEN" ] || [ "$TEMP_TOKEN" == "null" ]; then
  echo "Error: Failed to extract temp_token"
  exit 1
fi

# Step 4: Verify TOTP code
echo "Step 4: Verifying TOTP with code: $TOTP_CODE..."
VERIFY_RESPONSE=$(curl -s -X POST "$BASE_URL/api/admin/verify-totp" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TEMP_TOKEN" \
  -d "{\"totp_code\": \"$TOTP_CODE\"}" \
  -c cookies.txt -b cookies.txt)

echo "Verify TOTP Response:"
echo "$VERIFY_RESPONSE" | jq .

# Extract access_token from cookies
JWT_TOKEN=$(grep 'access_token' cookies.txt | awk '{print $7}')
if [ -z "$JWT_TOKEN" ]; then
  echo "Error: Failed to extract access_token from cookies"
  exit 1
fi

# Step 5: Generate access codes
echo "Step 5: Generating $QUANTITY access codes for plan ID $PLAN_ID..."
GENERATE_RESPONSE=$(curl -s -X POST "$BASE_URL/api/payments/generate-codes" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -b cookies.txt \
  -d "{\"plan_id\": \"$PLAN_ID\", \"quantity\": $QUANTITY}")

echo "Generate Codes Response:"
echo "$GENERATE_RESPONSE" | jq .

# Check for errors in generate response
if echo "$GENERATE_RESPONSE" | grep -q '"error"'; then
  echo "Error: Failed to generate codes"
  exit 1
fi

# Step 6: Display print prompt
echo "Codes generated successfully. Ready to print:"
echo "$GENERATE_RESPONSE" | jq -r '.codes[] | "Code: \(.code), Plan: \(.plan_name), Duration: \(.duration_hours) hours, Price: \(.price)"'

# Step 7: Verify in database
echo "Step 7: Verifying database..."
psql -U internet_user -d internet_service -h localhost -p 5432 -c "SELECT code, plan_id, duration_hours, price, status FROM access_codes ORDER BY created_at DESC LIMIT $QUANTITY;"