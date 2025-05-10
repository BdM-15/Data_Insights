"""
Test script to verify tab module imports are working correctly.
"""

print("Testing tab module imports...")

try:
    from src.frontend.pages.tabs import (
        render_market_overview,
        render_future_opportunities,
        render_agency_intelligence,
        render_competitive_analysis,
        render_contract_vehicle_analysis,
        render_geographic_analysis
    )
    print("✓ Successfully imported all tab rendering functions")
except Exception as e:
    print(f"✗ Error importing tab modules: {str(e)}")

print("Test complete.")
