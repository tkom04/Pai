#!/usr/bin/env python
"""Debug script to isolate the budget scan hanging issue."""
import asyncio
import sys
from datetime import date, timedelta

sys.path.insert(0, '.')

async def main():
    print("="*60)
    print("DEBUGGING BUDGET SCAN HANGING ISSUE")
    print("="*60)

    try:
        # Step 1: Import modules
        print("\n1️⃣  Importing modules...")
        from app.auth.open_banking import open_banking_oauth_manager
        from app.services.budgets import budget_service
        from app.models import BudgetScanRequest
        print("   ✅ Imports successful")

        # Step 2: Check authentication
        print("\n2️⃣  Checking Open Banking authentication...")
        user_id = "default-user"
        is_auth = await open_banking_oauth_manager.is_authenticated(user_id)
        print(f"   ✅ Authenticated: {is_auth}")

        if not is_auth:
            print("   ❌ Not authenticated - stopping")
            return

        # Step 3: Create request
        print("\n3️⃣  Creating budget scan request...")
        to_date = date.today()
        from_date = date(2025, 9, 1)  # From Sept 1st (we know there are transactions)

        request = BudgetScanRequest(
            period={"from": from_date.isoformat(), "to": to_date.isoformat()},
            source="open_banking"
        )
        print(f"   ✅ Request created: {from_date} to {to_date}")

        # Step 4: Run with detailed logging
        print("\n4️⃣  Running budget scan (this is where it might hang)...")
        print("   ⏳ Waiting...")

        # Add timeout
        try:
            result = await asyncio.wait_for(
                budget_service.scan_budget(request, user_id=user_id),
                timeout=15.0
            )

            print(f"   ✅ SUCCESS! Got {len(result.categories)} categories")

            print("\n5️⃣  Results:")
            for cat in result.categories:
                print(f"   {cat.name:12} - £{cat.spent:7.2f} / £{cat.cap:7.2f}")

            return result

        except asyncio.TimeoutError:
            print("   ❌ TIMEOUT after 15 seconds!")
            print("   This means budget_service.scan_budget() is hanging")
            return None

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("\n🚀 Starting debug test...\n")
    result = asyncio.run(main())

    if result:
        print("\n✅ TEST PASSED - Budget scan works!")
    else:
        print("\n❌ TEST FAILED - Budget scan hung or errored")

    print("\nDone!")

