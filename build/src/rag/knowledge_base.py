"""FINTRAC regulatory knowledge base for RAG.

Contains real FINTRAC guidance text, money laundering indicators,
typology descriptions, and STR writing guidance. In production,
this would be populated from FINTRAC's published guidance documents,
internal compliance policies, and approved STR examples.
"""

FINTRAC_DOCUMENTS = [
    # ── ML/TF Indicators (from FINTRAC guidance) ──
    {
        "id": "fintrac-ml-indicators-structuring",
        "title": "FINTRAC ML Indicators: Structuring",
        "category": "indicators",
        "typology": "structuring",
        "content": """FINTRAC Money Laundering Indicator: Structuring / Smurfing

Transactions conducted or attempted below the $10,000 CAD reporting threshold
to avoid triggering a Large Cash Transaction Report (LCTR) or other reporting
requirements under the PCMLTFA.

Key indicators:
- Multiple cash deposits just below $10,000 within a short period (24-48 hours)
- Deposits made at different branches or ATMs on the same day
- Client breaks a single large transaction into multiple smaller ones
- Pattern of transactions at $9,900, $9,800, or similar round numbers just below threshold
- Client appears nervous or rushed during transactions
- Multiple individuals depositing to the same account in structured amounts

FINTRAC Reference: ML/TF Indicator Group A - Structuring Transactions
Regulatory Basis: PCMLTFA Section 7, Proceeds of Crime (Money Laundering) and
Terrorist Financing Suspicious Transaction Reporting Regulations
""",
    },
    {
        "id": "fintrac-ml-indicators-rapid-movement",
        "title": "FINTRAC ML Indicators: Rapid Movement of Funds",
        "category": "indicators",
        "typology": "rapid_movement",
        "content": """FINTRAC Money Laundering Indicator: Rapid Movement of Funds

Funds deposited and quickly withdrawn or transferred, suggesting the account
is being used as a pass-through rather than for legitimate financial purposes.

Key indicators:
- Funds deposited and withdrawn within 24-48 hours
- Incoming wire transfer immediately followed by outgoing wire to different jurisdiction
- Deposits via e-Transfer followed by immediate wire withdrawal
- Pattern of deposit-withdraw cycles with no investment activity
- Account used solely as conduit — no savings, no purchases, no normal activity
- Funds moved through multiple accounts before final withdrawal

FINTRAC Reference: ML/TF Indicator Group B - Moving Funds
Regulatory Basis: PCMLTFA Suspicious Transaction Reporting Requirements
Note: Rapid movement is a hallmark of the "layering" phase of money laundering,
where criminals create distance between illicit funds and their source.
""",
    },
    {
        "id": "fintrac-ml-indicators-crypto",
        "title": "FINTRAC ML Indicators: Virtual Currency (Crypto) Transactions",
        "category": "indicators",
        "typology": "crypto_layering",
        "content": """FINTRAC Money Laundering Indicator: Virtual Currency Transactions

Suspicious patterns involving cryptocurrency that may indicate money laundering,
terrorist financing, or sanctions evasion.

Key indicators:
- Conversion of fiat currency to virtual currency and immediate transfer to external wallet
- Use of privacy-enhanced cryptocurrencies (Monero, Zcash, Dash)
- Multiple conversions between different virtual currencies (chain-hopping)
- Virtual currency transactions inconsistent with client's stated income or profile
- Transfers to/from virtual currency exchanges in high-risk jurisdictions
- Use of mixing or tumbling services
- Large purchases of virtual currency with no apparent legitimate purpose
- Client is unable or unwilling to explain the source of funds used for virtual currency purchase

FINTRAC Reference: ML/TF Indicator Group F - Virtual Currency Indicators
Note: Since June 2020, Money Services Businesses dealing in virtual currencies
must register with FINTRAC and comply with reporting obligations.
Virtual currency transactions of $10,000 CAD or more must be reported.
""",
    },
    {
        "id": "fintrac-ml-indicators-pep",
        "title": "FINTRAC ML Indicators: Politically Exposed Persons",
        "category": "indicators",
        "typology": "pep_sanctions_hit",
        "content": """FINTRAC Guidance: Politically Exposed Persons (PEPs) and Sanctions

Enhanced due diligence is required for domestic and foreign PEPs, heads of
international organizations, and their family members and close associates.

PEP-related indicators:
- Client identified as a current or former senior political figure
- Transactions inconsistent with known legitimate income of a public official
- Use of corporate vehicles or trusts to obscure PEP relationship
- Transactions involving countries known for high levels of corruption
- Unexplained wealth relative to known sources of income
- Family members or associates conducting transactions on behalf of PEP

Sanctions screening requirements:
- Screen against Canadian sanctions lists (SEMA, UNA, JVCFOA)
- Screen against UN Security Council consolidated list
- Screen against OFAC Specially Designated Nationals list
- Immediate reporting of any confirmed sanctions match
- No transactions permitted with sanctioned individuals or entities

FINTRAC Reference: PCMLTFA Section 9.3 (PEP obligations)
Frequency: Ongoing monitoring, not just at onboarding
""",
    },
    {
        "id": "fintrac-ml-indicators-round-tripping",
        "title": "FINTRAC ML Indicators: Round-Tripping",
        "category": "indicators",
        "typology": "round_tripping",
        "content": """FINTRAC Money Laundering Indicator: Round-Tripping / Circular Transfers

Funds sent out and returned to the original account or entity, often through
intermediate accounts or jurisdictions, to create the appearance of legitimate
business transactions.

Key indicators:
- Transfer out followed by equivalent transfer back within 7-14 days
- Circular flow through multiple accounts returning to origin
- Use of correspondent banking to route funds through multiple jurisdictions
- Invoicing for goods or services that don't appear to exist
- Matching credits and debits with no economic purpose
- Loan-back arrangements where client borrows against their own laundered deposits

FINTRAC Reference: ML/TF Indicator Group C - Circular Flow of Funds
Note: Round-tripping is particularly common in trade-based money laundering
and real estate transactions. In investment accounts, look for securities
purchased and sold at a loss with no tax benefit.
""",
    },
    {
        "id": "fintrac-ml-indicators-dormant",
        "title": "FINTRAC ML Indicators: Dormant Account Activity",
        "category": "indicators",
        "typology": "dormant_activation",
        "content": """FINTRAC Money Laundering Indicator: Dormant Account Reactivation

A previously inactive account suddenly shows significant activity, which may
indicate the account is being used for money laundering after a period of
establishing legitimacy.

Key indicators:
- Account dormant for 180+ days suddenly receives large deposits
- Reactivation coincides with changes in account ownership or authorized signatories
- Activity pattern after reactivation is inconsistent with account's original purpose
- Multiple dormant accounts reactivated simultaneously
- Large transactions immediately following reactivation

FINTRAC Reference: ML/TF Indicator Group D - Account Activity Patterns
Note: Dormant accounts are particularly valuable to launderers because they
have an established history and may receive less scrutiny than new accounts.
""",
    },
    {
        "id": "fintrac-ml-indicators-velocity",
        "title": "FINTRAC ML Indicators: Unusual Transaction Volume",
        "category": "indicators",
        "typology": "velocity_spike",
        "content": """FINTRAC Money Laundering Indicator: Unusual Transaction Volume / Velocity

A sudden and significant increase in the frequency or volume of transactions
that is inconsistent with the client's known profile and expected activity.

Key indicators:
- Transaction volume increases 5x or more above established baseline
- Spike in activity without corresponding change in client circumstances
- High-frequency trading or transfers not consistent with investment strategy
- Sudden increase in e-Transfer or wire activity
- Volume inconsistent with client's stated occupation and income

FINTRAC Reference: ML/TF Indicator Group E - Unusual Client Behaviour
Note: Velocity analysis should compare against the client's own baseline
(personal deviation) AND peer group baseline (cohort deviation) to distinguish
genuine lifestyle changes from suspicious activity.
""",
    },
    # ── STR Writing Guidance ──
    {
        "id": "fintrac-str-guidance",
        "title": "FINTRAC: How to Write a Suspicious Transaction Report",
        "category": "str_guidance",
        "typology": "general",
        "content": """FINTRAC Guidance: Completing a Suspicious Transaction Report (STR)

An STR must be filed when there are reasonable grounds to suspect that a
transaction or attempted transaction is related to the commission or attempted
commission of a money laundering or terrorist financing offence.

Section 1 - Subject Information:
Include full identifying information: name, date of birth, address, occupation,
identification documents. Note any discrepancies in identification.

Section 2 - Suspicious Activity Description:
Describe the activity that raised suspicion. Be specific and factual.
Include dates, amounts, methods, and counterparties. Explain WHY the
activity is suspicious, not just WHAT happened.

Section 3 - Indicators:
Reference specific FINTRAC ML/TF indicators that apply to this case.
Use FINTRAC's published indicator categories where possible.

Section 4 - Key Transactions:
List the specific transactions that triggered the report. Include
transaction dates, amounts, types, and counterparties.

Section 5 - Risk Assessment:
Provide your assessment of the overall risk level and confidence.
Note any mitigating factors.

Section 6 - Recommended Action:
State whether you recommend filing the STR. If not filing, explain
why the suspicious indicators were resolved.

Filing deadline: STRs must be filed within 30 days of the determination
that there are reasonable grounds to suspect ML/TF.
Attempted transactions: Must also be reported if suspicious.
Tipping off: It is a criminal offence to disclose the existence of an STR
to the subject or any other person, except as authorized by law.
""",
    },
    # ── Wealthsimple-specific context ──
    {
        "id": "ws-products-aml",
        "title": "Wealthsimple Products: AML Risk Considerations",
        "category": "internal_policy",
        "typology": "general",
        "content": """Wealthsimple Product-Specific AML Considerations

TFSA / RRSP / FHSA / RESP (Registered Accounts):
- Contribution limits provide natural transaction caps
- Over-contribution may indicate structuring across account types
- Withdrawals from TFSA are not taxable — potential layering vehicle
- RRSP withdrawals trigger withholding tax, reducing appeal for ML

Personal (Non-Registered) Accounts:
- No contribution limits — higher ML risk
- Monitor for large, unexplained deposits
- Watch for rapid buying/selling of low-liquidity securities (wash trading)

Crypto Trading:
- Highest AML risk product due to pseudonymity
- Privacy coins (Monero, Zcash) require enhanced monitoring
- External wallet transfers need source-of-funds verification
- Monitor for fiat-to-crypto-to-external-wallet pattern
- Chain-hopping between multiple cryptocurrencies before withdrawal

P2P Transfers / Wealthsimple Cash:
- E-Transfer limits provide some natural control
- Monitor for multiple P2P transfers to same recipient
- Watch for rapid P2P followed by crypto purchase

General considerations:
- Wealthsimple's client base skews younger (18-35)
- Lower average account balances than traditional banks
- High crypto adoption rate among client base
- Mobile-first platform — IP and device fingerprinting available
""",
    },
    {
        "id": "fintrac-geographic-risk",
        "title": "FINTRAC: High-Risk Geographic Indicators",
        "category": "indicators",
        "typology": "geographic_anomaly",
        "content": """FINTRAC Guidance: Geographic Risk Factors

Transactions involving certain jurisdictions carry elevated ML/TF risk.

High-risk jurisdiction indicators:
- Transactions to/from FATF-identified high-risk jurisdictions
- IP addresses originating from sanctioned countries
- Counterparties in jurisdictions with weak AML frameworks
- Multiple international transfers to countries with no apparent business connection
- Use of correspondent banks in jurisdictions known for secrecy

Canadian-specific geographic considerations:
- Cross-border transactions to/from US require CTR reporting at $10K+
- Transfers to/from known tax havens (Cayman Islands, BVI, Panama)
- IP address analysis: Canadian client transacting from unexpected foreign IP

Note: Geographic risk alone is not sufficient for an STR. It must be
combined with other suspicious indicators to reach reasonable grounds.
""",
    },
    {
        "id": "fintrac-third-party",
        "title": "FINTRAC ML Indicators: Third-Party Involvement",
        "category": "indicators",
        "typology": "third_party_pattern",
        "content": """FINTRAC Money Laundering Indicator: Third-Party Involvement

Transactions appear to be conducted on behalf of or directed by another
party, which may indicate nominee or straw-man arrangements.

Key indicators:
- Multiple unrelated clients sending funds to the same beneficiary
- Client appears to be acting on instructions from someone else
- Transactions don't match the client's known financial profile
- Use of someone else's account to receive or send funds
- Client unable to explain the business relationship with counterparty
- Pattern of funding from multiple sources followed by single large transfer

FINTRAC Reference: ML/TF Indicator Group G - Third-Party Involvement
Note: Third-party ML is increasingly common in digital financial services
where face-to-face verification is not standard. Enhanced due diligence
on the source and destination of funds is critical.
""",
    },
    {
        "id": "fintrac-age-amount",
        "title": "FINTRAC ML Indicators: Inconsistent Client Profile",
        "category": "indicators",
        "typology": "age_amount_mismatch",
        "content": """FINTRAC Money Laundering Indicator: Client Profile Inconsistencies

Transactions or account activity that is inconsistent with the client's
known profile, occupation, or stated source of funds.

Key indicators:
- Transaction amounts inconsistent with declared income or occupation
- Young client (18-25) with very large investment account balances
- Student or entry-level employee conducting high-value transactions
- Client's declared occupation does not support observed transaction activity
- Significant change in transaction patterns without explanation
- Account balance or activity inconsistent with peer group

FINTRAC Reference: ML/TF Indicator Group E - Unusual Client Behaviour
Note: Profile inconsistency alone does not confirm ML. Many legitimate
scenarios (inheritance, legal settlement, cryptocurrency gains) can explain
unusual activity. The key is whether the client can provide a reasonable
explanation when asked.
""",
    },
]
