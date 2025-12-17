# Demo Mode Guide

## 🎯 How to Use Demo Mode

To demonstrate a successful loan approval with PDF generation, use the following phone number:

**Demo Phone Number:** `7982130057`

## What Happens in Demo Mode

When you enter phone number `7982130057`:

1. **Credit Score:** Automatically set to **800** (excellent credit)
2. **Pre-approved Limit:** Set to **Rs. 10,00,000** (1 million)
3. **Result:** Loan will be **automatically approved** (as long as loan amount ≤ 10 lakhs)
4. **PDF Generation:** Sanction letter PDF will be generated and available for download

## Demo Flow

1. Start a new session
2. Provide your name (e.g., "Shaurya Singh")
3. Provide loan amount (e.g., "5 lakhs" or "500000")
4. Provide tenure (e.g., "24 months" or "2 years")
5. **Enter phone number: `7982130057`** ← This triggers demo mode
6. KYC verification will show credit score 800
7. Loan will be approved
8. PDF sanction letter will be generated
9. Download button will appear

## Example Conversation

```
You: Shaurya Singh
Bot: [Asks for loan purpose]

You: Car purchase
Bot: [Asks for loan amount]

You: 5 lakhs
Bot: [Asks for tenure]

You: 24 months
Bot: [Asks for phone number]

You: 7982130057  ← DEMO MODE TRIGGERED
Bot: ✅ KYC verified! Credit score: 800
     ✅ Loan approved!
     📄 Sanction letter ready for download
```

## Notes

- **Any loan amount up to 10 lakhs** will be approved in demo mode
- No salary verification needed in demo mode
- PDF will be generated automatically
- Works for any name/customer

## For Production

To disable or change the demo phone number, edit:
`backend/agents/verification_agent.py` → Line 58

Change `DEMO_PHONE_NUMBER = "7982130057"` to your desired number or remove the demo mode entirely.

