import requests
import json

print("Testing GET /budget_scan endpoint...")
print("=" * 60)

try:
    response = requests.get(
        "http://localhost:8080/budget_scan",
        headers={"X-API-Key": "dev-api-key-12345"},
        timeout=30
    )

    print(f"Status Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    print()

    if response.status_code == 200:
        data = response.json()
        print("✅ SUCCESS!")
        print(f"Budgets: {len(data.get('budgets', []))}")
        print()

        for budget in data.get('budgets', []):
            print(f"  {budget['name']:12} - £{budget['spent']:8.2f} / £{budget['amount']:8.2f}")

        if any(b['spent'] > 0 for b in data.get('budgets', [])):
            print("\n🎉 REAL DATA IS SHOWING!")
        else:
            print("\n⚠️  All budgets show £0 spent")

    else:
        print(f"❌ ERROR: {response.status_code}")
        print(f"Response: {response.text}")

except Exception as e:
    print(f"❌ EXCEPTION: {e}")
    import traceback
    traceback.print_exc()




