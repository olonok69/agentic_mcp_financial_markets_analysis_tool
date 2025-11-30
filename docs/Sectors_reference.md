# 📊 Multi-Sector Analysis - Symbols Reference Guide

A comprehensive reference for all sectors and symbols available in the Multi-Sector Analysis feature. This document provides detailed information about each company, their market characteristics, and sector classifications.

---

## 📋 Quick Reference

### Sector Overview

| Sector | Stocks | Characteristic | Market Sensitivity |
|--------|--------|----------------|-------------------|
| 🏦 Banking | 10 | Interest rate sensitive | High (Fed policy) |
| 💻 Technology | 10 | Growth-oriented | Medium (earnings) |
| 🌱 Clean Energy | 9 | High volatility | High (policy/sentiment) |
| 🏥 Healthcare | 10 | Defensive | Low (steady demand) |
| 🛒 Consumer | 10 | Cyclical | High (consumer spending) |

**Total:** 49 symbols across 5 sectors

### Default Configuration

```python
DEFAULT_SECTORS = {
    "Banking": "JPM,BAC,WFC,C,GS,MS,USB,PNC,TFC,COF",
    "Technology": "AAPL,MSFT,GOOGL,META,NVDA,AMD,CRM,ORCL,ADBE,INTC",
    "Clean Energy": "TSLA,NIO,RIVN,LCID,PLUG,SEDG,NEE,ICLN,ENPH",
    "Healthcare": "JNJ,UNH,PFE,MRK,ABBV,LLY,TMO,ABT,BMY,AMGN",
    "Consumer": "AMZN,HD,MCD,NKE,SBUX,TGT,LOW,COST,TJX,CMG",
}
```

---

## 🏦 Banking Sector

Financial institutions including commercial banks, investment banks, and diversified financial services companies. This sector is highly sensitive to Federal Reserve interest rate policy and economic cycles.

### Key Drivers
- Federal Reserve interest rate decisions
- Yield curve shape (spread between short and long-term rates)
- Loan demand and credit quality
- Regulatory environment
- Economic growth expectations

### Symbols

| Symbol | Company | Sub-Sector | Market Cap | Dividend | Description |
|--------|---------|------------|------------|----------|-------------|
| **JPM** | JPMorgan Chase & Co | Diversified Bank | ~$500B | Yes | Largest U.S. bank by assets. Investment banking, commercial banking, asset management. |
| **BAC** | Bank of America | Commercial Bank | ~$300B | Yes | Second-largest U.S. bank. Consumer banking, wealth management, global banking. |
| **WFC** | Wells Fargo & Co | Commercial Bank | ~$180B | Yes | Major retail and commercial bank. Strong mortgage lending presence. |
| **C** | Citigroup Inc | Global Bank | ~$120B | Yes | Global banking with strong international presence. Institutional clients focus. |
| **GS** | Goldman Sachs Group | Investment Bank | ~$150B | Yes | Premier investment bank. Trading, asset management, wealth management. |
| **MS** | Morgan Stanley | Investment Bank | ~$150B | Yes | Leading investment bank. Strong wealth management and trading divisions. |
| **USB** | U.S. Bancorp | Regional Bank | ~$70B | Yes | Fifth-largest U.S. bank. Consumer and business banking, payments. |
| **PNC** | PNC Financial Services | Regional Bank | ~$65B | Yes | Major regional bank. Retail banking, corporate banking, asset management. |
| **TFC** | Truist Financial | Regional Bank | ~$50B | Yes | Formed from BB&T and SunTrust merger. Southeast and Mid-Atlantic focus. |
| **COF** | Capital One Financial | Consumer Finance | ~$55B | Yes | Credit card issuer and digital bank. Auto loans, consumer banking. |

### Sector Metrics to Watch
- Net Interest Margin (NIM)
- Loan Loss Provisions
- Return on Equity (ROE)
- Efficiency Ratio
- Common Equity Tier 1 (CET1) Ratio

---

## 💻 Technology Sector

Technology companies spanning hardware, software, cloud computing, semiconductors, and digital services. This sector drives innovation and tends to outperform during economic expansions.

### Key Drivers
- Enterprise IT spending
- Cloud computing adoption
- AI and machine learning demand
- Consumer electronics cycles
- Semiconductor supply/demand dynamics

### Symbols

| Symbol | Company | Sub-Sector | Market Cap | Dividend | Description |
|--------|---------|------------|------------|----------|-------------|
| **AAPL** | Apple Inc | Consumer Electronics | ~$3T | Yes | iPhone, Mac, iPad, Services. World's most valuable company. |
| **MSFT** | Microsoft Corp | Enterprise Software | ~$3T | Yes | Windows, Azure cloud, Office 365, LinkedIn, Gaming (Xbox). |
| **GOOGL** | Alphabet Inc | Internet Services | ~$2T | No | Google Search, YouTube, Google Cloud, Android, Waymo. |
| **META** | Meta Platforms | Social Media | ~$1.3T | Yes | Facebook, Instagram, WhatsApp, Reality Labs (VR/AR). |
| **NVDA** | NVIDIA Corp | Semiconductors | ~$3T | Yes | GPU leader. AI/ML chips, data center, gaming, automotive. |
| **AMD** | Advanced Micro Devices | Semiconductors | ~$250B | No | CPUs and GPUs. Data center, gaming, embedded systems. |
| **CRM** | Salesforce Inc | Enterprise Software | ~$270B | No | CRM software leader. Sales Cloud, Service Cloud, Marketing Cloud. |
| **ORCL** | Oracle Corp | Enterprise Software | ~$350B | Yes | Database software, cloud infrastructure, enterprise applications. |
| **ADBE** | Adobe Inc | Creative Software | ~$230B | No | Creative Cloud (Photoshop, Illustrator), Document Cloud, Experience Cloud. |
| **INTC** | Intel Corp | Semiconductors | ~$110B | Yes | CPU manufacturer. Data center, PC, foundry services. Turnaround phase. |

### Sector Metrics to Watch
- Revenue Growth Rate
- Cloud Revenue / ARR
- Gross Margin
- R&D as % of Revenue
- Free Cash Flow Margin

---

## 🌱 Clean Energy Sector

Companies focused on renewable energy, electric vehicles, and sustainable technology. This sector exhibits high volatility and is sensitive to government policy, subsidies, and environmental regulations.

### Key Drivers
- Government incentives and subsidies (IRA, tax credits)
- Oil and gas prices
- Battery technology advancement
- EV adoption rates
- Climate policy and regulations
- Interest rates (capital-intensive projects)

### Symbols

| Symbol | Company | Sub-Sector | Market Cap | Dividend | Description |
|--------|---------|------------|------------|----------|-------------|
| **TSLA** | Tesla Inc | Electric Vehicles | ~$800B | No | EV leader. Vehicles, energy storage, solar, AI/robotics. |
| **NIO** | NIO Inc | Electric Vehicles | ~$10B | No | Chinese premium EV maker. Battery-as-a-service model. |
| **RIVN** | Rivian Automotive | Electric Vehicles | ~$15B | No | Electric trucks and SUVs. Amazon delivery van partnership. |
| **LCID** | Lucid Group | Electric Vehicles | ~$7B | No | Luxury EV maker. Lucid Air sedan. Saudi Arabia investment. |
| **PLUG** | Plug Power Inc | Hydrogen/Fuel Cells | ~$3B | No | Hydrogen fuel cell systems. Green hydrogen production. |
| **SEDG** | SolarEdge Technologies | Solar Equipment | ~$3B | No | Solar inverters and power optimizers. Energy storage. |
| **NEE** | NextEra Energy | Renewable Utilities | ~$150B | Yes | Largest renewable energy producer. Florida utility + clean energy. |
| **ICLN** | iShares Global Clean Energy ETF | ETF | ~$3B | Yes | ETF tracking global clean energy companies. Diversified exposure. |
| **ENPH** | Enphase Energy | Solar Equipment | ~$25B | No | Microinverters for solar. Home energy management systems. |

### Sector Metrics to Watch
- Vehicle Deliveries (EVs)
- Energy Generation Capacity (GW)
- Gross Margin Trend
- Cash Burn Rate
- Order Backlog

---

## 🏥 Healthcare Sector

Pharmaceutical companies, biotechnology firms, medical device manufacturers, and healthcare services. This defensive sector provides stability during economic downturns due to consistent healthcare demand.

### Key Drivers
- Drug pipeline and FDA approvals
- Patent expirations (loss of exclusivity)
- Healthcare policy and drug pricing
- Aging population demographics
- M&A activity
- Clinical trial results

### Symbols

| Symbol | Company | Sub-Sector | Market Cap | Dividend | Description |
|--------|---------|------------|------------|----------|-------------|
| **JNJ** | Johnson & Johnson | Diversified Healthcare | ~$380B | Yes | Pharmaceuticals, medical devices, consumer health (spun off). |
| **UNH** | UnitedHealth Group | Health Insurance | ~$500B | Yes | Largest health insurer. Optum health services division. |
| **PFE** | Pfizer Inc | Pharmaceuticals | ~$160B | Yes | Major pharma. Oncology, vaccines, rare disease. Post-COVID normalization. |
| **MRK** | Merck & Co | Pharmaceuticals | ~$270B | Yes | Keytruda (cancer), vaccines (Gardasil), animal health. |
| **ABBV** | AbbVie Inc | Biopharmaceuticals | ~$310B | Yes | Immunology (Humira, Skyrizi, Rinvoq), oncology, aesthetics (Botox). |
| **LLY** | Eli Lilly & Co | Pharmaceuticals | ~$750B | Yes | GLP-1 leader (Mounjaro, Zepbound). Diabetes, obesity, Alzheimer's. |
| **TMO** | Thermo Fisher Scientific | Life Sciences Tools | ~$200B | Yes | Lab equipment, reagents, diagnostics. Serves pharma/biotech R&D. |
| **ABT** | Abbott Laboratories | Medical Devices | ~$200B | Yes | Diagnostics, medical devices (FreeStyle Libre), nutrition, pharma. |
| **BMY** | Bristol-Myers Squibb | Pharmaceuticals | ~$120B | Yes | Oncology, cardiovascular, immunology. Opdivo, Eliquis. |
| **AMGN** | Amgen Inc | Biotechnology | ~$160B | Yes | Biotech pioneer. Inflammation, oncology, cardiovascular, bone health. |

### Sector Metrics to Watch
- Revenue Growth (organic)
- Pipeline Value / Phase 3 Assets
- Patent Cliff Exposure
- R&D Productivity
- Dividend Yield (defensive income)

---

## 🛒 Consumer Discretionary Sector

Retailers, restaurants, apparel companies, and consumer services. This cyclical sector performs well during economic expansions when consumer confidence and spending are high.

### Key Drivers
- Consumer confidence index
- Employment and wage growth
- Discretionary income levels
- E-commerce trends
- Housing market (home improvement)
- Commodity costs (restaurants/retail)

### Symbols

| Symbol | Company | Sub-Sector | Market Cap | Dividend | Description |
|--------|---------|------------|------------|----------|-------------|
| **AMZN** | Amazon.com Inc | E-commerce/Cloud | ~$2T | No | E-commerce leader. AWS cloud. Advertising, streaming (Prime). |
| **HD** | Home Depot Inc | Home Improvement | ~$380B | Yes | Largest home improvement retailer. Pro and DIY customers. |
| **MCD** | McDonald's Corp | Quick Service Restaurants | ~$210B | Yes | Global fast food leader. Franchise model. Real estate holdings. |
| **NKE** | Nike Inc | Athletic Apparel | ~$120B | Yes | Global athletic footwear and apparel leader. Jordan brand. |
| **SBUX** | Starbucks Corp | Coffee/Restaurants | ~$110B | Yes | Global coffeehouse chain. Loyalty program. China growth. |
| **TGT** | Target Corp | Discount Retail | ~$55B | Yes | General merchandise retailer. Omnichannel strategy. Private labels. |
| **LOW** | Lowe's Companies | Home Improvement | ~$140B | Yes | Second-largest home improvement retailer. Pro customer focus. |
| **COST** | Costco Wholesale | Warehouse Retail | ~$380B | Yes | Membership warehouse club. High customer loyalty. Private label (Kirkland). |
| **TJX** | TJX Companies | Off-Price Retail | ~$130B | Yes | Off-price retailer. TJ Maxx, Marshalls, HomeGoods. Treasure hunt model. |
| **CMG** | Chipotle Mexican Grill | Fast Casual | ~$85B | No | Fast casual Mexican chain. Digital ordering strength. |

### Sector Metrics to Watch
- Same-Store Sales (Comps)
- E-commerce Growth
- Consumer Confidence Index
- Traffic vs Ticket Growth
- Inventory Turnover

---

## 📈 Sector Correlation & Portfolio Considerations

### Correlation Matrix (Conceptual)

| | Banking | Technology | Clean Energy | Healthcare | Consumer |
|---|:---:|:---:|:---:|:---:|:---:|
| **Banking** | 1.00 | 0.60 | 0.40 | 0.35 | 0.65 |
| **Technology** | 0.60 | 1.00 | 0.55 | 0.45 | 0.70 |
| **Clean Energy** | 0.40 | 0.55 | 1.00 | 0.30 | 0.50 |
| **Healthcare** | 0.35 | 0.45 | 0.30 | 1.00 | 0.40 |
| **Consumer** | 0.65 | 0.70 | 0.50 | 0.40 | 1.00 |

*Note: Correlations are approximate and vary over time*

### Sector Behavior by Economic Cycle

| Economic Phase | Best Performers | Worst Performers |
|---------------|-----------------|------------------|
| **Early Recovery** | Technology, Consumer, Banking | Healthcare |
| **Expansion** | Technology, Consumer | Healthcare, Utilities |
| **Late Cycle** | Healthcare, Banking | Technology, Clean Energy |
| **Recession** | Healthcare | Consumer, Banking, Clean Energy |

### Diversification Benefits

| Sector Pair | Diversification Benefit | Rationale |
|-------------|------------------------|-----------|
| Technology + Healthcare | ✅ High | Growth vs Defensive |
| Banking + Clean Energy | ✅ High | Rate sensitive vs Policy driven |
| Consumer + Healthcare | ✅ High | Cyclical vs Defensive |
| Technology + Consumer | ⚠️ Medium | Both growth-oriented |
| Banking + Consumer | ⚠️ Medium | Both economically sensitive |

---

## 🔧 Customization Guide

### Adding New Sectors

You can customize sectors in the Streamlit interface or via API:

```python
# Example: Add Industrials sector
custom_sectors = {
    "Industrials": "CAT,DE,UNP,HON,GE,BA,LMT,RTX,UPS,MMM"
}
```

### Suggested Additional Sectors

| Sector | Symbols | Use Case |
|--------|---------|----------|
| **Industrials** | CAT, DE, UNP, HON, GE, BA, LMT, RTX, UPS, MMM | Manufacturing, infrastructure |
| **Real Estate (REITs)** | AMT, PLD, EQIX, SPG, O, DLR, PSA, WELL, AVB, VTR | Income, rate sensitivity |
| **Communication Services** | NFLX, DIS, CMCSA, T, VZ, TMUS, CHTR, EA, TTWO, WBD | Media, telecom |
| **Materials** | LIN, APD, SHW, ECL, NEM, FCX, NUE, DD, DOW, VMC | Commodities, inflation hedge |
| **Utilities** | NEE, DUK, SO, D, AEP, XEL, EXC, SRE, WEC, ES | Defensive, income |

### Sector Weight Recommendations

For balanced multi-sector analysis:

| Approach | Banking | Tech | Clean Energy | Healthcare | Consumer |
|----------|---------|------|--------------|------------|----------|
| **Equal Weight** | 20% | 20% | 20% | 20% | 20% |
| **Market Weight** | 12% | 30% | 5% | 15% | 12% |
| **Defensive Tilt** | 15% | 20% | 10% | 30% | 25% |
| **Growth Tilt** | 15% | 35% | 15% | 15% | 20% |

---

## ⚠️ Important Notes

### Data Availability
- All symbols are traded on major U.S. exchanges (NYSE, NASDAQ)
- Historical data available via Yahoo Finance API
- ICLN is an ETF, not an individual stock

### Analysis Considerations
- **Market Cap Variance**: Ranges from ~$3B (PLUG) to ~$3T (AAPL, MSFT, NVDA)
- **Volatility Variance**: Clean Energy stocks typically 2-3x more volatile than Healthcare
- **Dividend Status**: Not all stocks pay dividends (growth stocks often reinvest)

### Compute Requirements
| Configuration | Stocks | Tool Calls | Estimated Time |
|--------------|--------|------------|----------------|
| 2 Sectors | 19-20 | ~80 | 3-5 minutes |
| 3 Sectors | 29-30 | ~120 | 5-8 minutes |
| 5 Sectors | 49 | ~196 | 10-20 minutes |

---

## 📚 Additional Resources

- [Yahoo Finance](https://finance.yahoo.com/) - Real-time quotes and news
- [SEC EDGAR](https://www.sec.gov/edgar/) - Company filings
- [Federal Reserve](https://www.federalreserve.gov/) - Interest rate decisions
- [Sector SPDRs](https://www.sectorspdrs.com/) - Sector ETF information

---

*Last Updated: November 2024*

*Note: Market caps are approximate and change daily. Always verify current data before making investment decisions.*