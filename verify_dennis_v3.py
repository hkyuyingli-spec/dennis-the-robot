import chatbot
from nutribot import i18n
import os

current_lang = os.getenv('NUTRIBOT_LANG') or 'en'

def run_tertiary_tests():
    print(i18n.translate('verify_financial_header', current_lang))
    
    # 1. ROI: High Growth
    # Scenario: $250 startup investment sells for $5,000
    roi = chatbot.calculate_roi(initial_investment=250, final_value=5000)
    print(i18n.translate('roi_calculation', current_lang).format(value=roi['roi_percentage']))

    # 2. NPV: Long-term / Lower Rate
    # Scenario: $5,000 cost, returns $1k, $2k, $3k, $4k over 4 years at 8% rate
    npv = chatbot.calculate_npv(discount_rate=0.08, initial_investment=5000, cash_flows=[1000, 2000, 3000, 4000])
    print(i18n.translate('npv_calculation', current_lang).format(value=npv['npv']))

    # 3. IRR: Different scale
    # Scenario: $10,000 investment, returns $4k, $4k, $4k
    irr = chatbot.calculate_irr(initial_investment=10000, cash_flows=[4000, 4000, 4000])
    print(i18n.translate('irr_calculation', current_lang).format(value=irr['irr_percentage']))

    # 4. WACC: Debt-Heavy
    # Scenario: 20% Equity ($200k), 80% Debt ($800k), 18% Equity cost, 7% Debt cost, 21% Tax
    wacc = chatbot.calculate_wacc(equity_value=200000, debt_value=800000, cost_of_equity=0.18, cost_of_debt=0.07, tax_rate=0.21)
    print(i18n.translate('wacc_calculation', current_lang).format(value=wacc['wacc_percentage']))

    # 5. Break-Even: Low Margin
    # Scenario: $20,000 fixed costs, $5.00 price, $4.50 variable cost
    be = chatbot.calculate_break_even(fixed_costs=20000, price_per_unit=5.00, variable_cost_per_unit=4.50)
    print(i18n.translate('break_even_point', current_lang).format(value=be['break_even_units']))

    print("\n" + i18n.translate('round3_tests_complete', current_lang))

if __name__ == "__main__":
    run_tertiary_tests()
