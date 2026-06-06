import chatbot

def run_tertiary_tests():
    print("--- 🧪 Dennis Financial Tools: Round 3 Verification 🧪 ---")
    
    # 1. ROI: High Growth
    # Scenario: $250 startup investment sells for $5,000
    roi = chatbot.calculate_roi(initial_investment=250, final_value=5000)
    print(f"✅ ROI Calculation (250->5000): {roi['roi_percentage']}")

    # 2. NPV: Long-term / Lower Rate
    # Scenario: $5,000 cost, returns $1k, $2k, $3k, $4k over 4 years at 8% rate
    npv = chatbot.calculate_npv(discount_rate=0.08, initial_investment=5000, cash_flows=[1000, 2000, 3000, 4000])
    print(f"✅ NPV Calculation (8% rate, 4yrs): ${npv['npv']}")

    # 3. IRR: Different scale
    # Scenario: $10,000 investment, returns $4k, $4k, $4k
    irr = chatbot.calculate_irr(initial_investment=10000, cash_flows=[4000, 4000, 4000])
    print(f"✅ IRR Calculation (10k cost, 3yrs): {irr['irr_percentage']}")

    # 4. WACC: Debt-Heavy
    # Scenario: 20% Equity ($200k), 80% Debt ($800k), 18% Equity cost, 7% Debt cost, 21% Tax
    wacc = chatbot.calculate_wacc(equity_value=200000, debt_value=800000, cost_of_equity=0.18, cost_of_debt=0.07, tax_rate=0.21)
    print(f"✅ WACC Calculation (20/80 debt-heavy): {wacc['wacc_percentage']}")

    # 5. Break-Even: Low Margin
    # Scenario: $20,000 fixed costs, $5.00 price, $4.50 variable cost
    be = chatbot.calculate_break_even(fixed_costs=20000, price_per_unit=5.00, variable_cost_per_unit=4.50)
    print(f"✅ Break-Even Point (low margin): {be['break_even_units']} units")

    print("\n--- Round 3 Tests Complete! Dennis is a financial wizard! *Bleep Boop* ---")

if __name__ == "__main__":
    run_tertiary_tests()
