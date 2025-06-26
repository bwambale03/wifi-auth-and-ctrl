#!/bin/bash

# Debugging Admin Auth Flow

# 1. Check Flask server is running
echo "1. Checking Flask server..."
curl -s http://localhost:5000/api/packages | jq . || {
    echo "Flask server not responding properly"
    exit 1
}

# 2. Reset database
echo "2. Resetting database..."
flask reset-db

# 3. Create fresh admin (will show TOTP secret)
echo "3. Creating admin user..."
flask create-admin

# 4. Manually test login
echo "4. Test this manually with the TOTP secret shown above:"
echo "curl -X POST http://localhost:5000/api/admin/login \\"
echo "  -H \"Content-Type: application/json\" \\"
echo "  -d '{\"username\":\"superadmin\",\"password\":\"SecureRandomPassword2025!\"}'"
