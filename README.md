# Payment Flow Test Suite 🧪

A QA test suite simulating real-world POS payment processing 
scenarios — built to demonstrate manual-to-automated testing 
skills for entry-level QA Engineering roles.

Inspired by hands-on experience integrating and troubleshooting 
Clover POS systems and payment processors (North, CardConnect) 
across 200+ merchant clients.

## What This Tests

| Module | Scenarios Covered |
|--------|------------------|
| **Payment Processing** | Approved sales, card validation, amount boundaries |
| **Refunds** | Full refund, partial refund, double refund prevention |
| **Voids** | Pre-settlement void, double void prevention |
| **Chargebacks** | Filing disputes, resolution outcomes, reason code validation |
| **Transaction Retrieval** | Record integrity, card masking, error handling |

40 test cases total covering happy paths, edge cases, 
boundary values, and negative scenarios.

## Project Structure

payment-flow-test-suite/
├── payment_processor.py   # Core payment logic
├── test_payment_flows.py  # 40 pytest test cases
├── requirements.txt
└── README.md

## Setup & Run

# Install dependencies
pip install -r requirements.txt

# Run all tests
pytest test_payment_flows.py -v

## Skills Demonstrated
- pytest fixtures, test classes, parametrization
- Happy path, edge case, boundary, negative testing
- Payment domain: POS systems, chargebacks, refund workflows

## Author
Alex Le — alexle2030@gmail.com
linkedin.com/in/alexle-ucsd# payment-flow-test-suite
