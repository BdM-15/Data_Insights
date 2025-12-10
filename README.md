# Data Insights: Intelligent Federal Contract Analysis Platform

**Transform weeks of manual research into hours of strategic advantage.**

Data Insights is a business intelligence workstation that automates federal contract research, competitive analysis, and capture planning. It turns 66+ million government spending records into actionable insights and professional capture profiles—all running privately on your own computer.

## What Problem Does This Solve?

**The Challenge:** Business development teams pursuing federal contracts spend 40-60 hours per opportunity gathering data, analyzing competitors, researching incumbents, and writing capture plans. Most of this work is repetitive, manual, and never reused.

**The Solution:** Data Insights automates the research and document creation process, reducing time-to-insight by 85% while producing consistent, professional outputs that your executives and proposal teams can rely on.

**The Result:** Your team spends less time in spreadsheets and more time building customer relationships, crafting winning solutions, and closing deals.

## Who Benefits and How

### Business Development Leaders

- **See market opportunities instantly:** Which agencies are spending in your areas? Where are the trends?
- **Track competitors systematically:** Who's winning what, where, and with which partners?
- **Make data-driven decisions:** Bid/no-bid calls backed by actual spending patterns and win rates
- **Measure what matters:** Track your win rate improvements and market share growth

### Capture Managers

- **Generate capture profiles in hours, not weeks:** From opportunity selection to professional document
- **Access instant incumbent intelligence:** Contract history, performance, teaming, and weaknesses
- **Get AI-drafted win themes:** With citations to actual data, not generic marketing speak
- **Find teaming partners automatically:** Based on complementary capabilities and past performance

### Analysts and Researchers

- **Stop fighting with spreadsheets:** Ask questions in plain English, get instant visualizations
- **Eliminate repetitive data work:** No more downloading, cleaning, and manual calculations
- **Focus on strategy, not data entry:** Spend time on interpretation and recommendations
- **Build knowledge that persists:** Research that lives beyond individual projects

### Proposal Teams

- **Start with better intelligence:** Competitive analysis and positioning already done
- **Reuse proven content:** Win themes and capability descriptions refined over time
- **Trust the numbers:** Every figure traces back to source records with full audit trail

## What You Get: End-State Capabilities

### 1. Strategic Intelligence Dashboard

**The big picture for decision makers:**

- Total market spending and year-over-year trends in your target segments
- Top contractors ranked by dollar volume and number of contracts
- Market share analysis showing competitive positioning
- Contracts expiring in the next 24 months with recompete potential
- Geographic and agency concentration patterns

### 2. Advanced Opportunity Explorer

**Deep dive on specific opportunities:**

- Complete incumbent profile: history, performance, teaming relationships
- Recompete radar with strategic fit scores
- Partner recommendations based on complementary capabilities
- Contract vehicle analysis (IDIQ, BPA, GSA schedules)
- Set-aside opportunity identification

### 3. Capability Profile Manager

**Your company's positioning, maintained automatically:**

- Structured profile of what you actually deliver (core/differentiator/emerging)
- Evidence-based, derived from your contract performance history
- Capability comparison against requirements and competitors
- Gap analysis identifying where you need partners or new capabilities

### 4. AI Data Agent

**Research assistant that speaks your language:**

- Ask questions in plain English: "Who are the top Navy IT contractors?"
- Get instant answers backed by database records
- Draft narrative sections for capture plans and proposals
- All processing happens locally—complete privacy

### 5. Automated Capture Profile Generator

**The game-changer: complete capture profiles in minutes**

The Capture Profile Generator is an AI-powered tool that automatically creates comprehensive documents with contract details, competitive analysis, and strategic insights to support government contract pursuit. It transforms raw contract data into actionable intelligence by combining historical information, competitor analysis, and market trends, while generating narrative sections like executive summaries and win strategies. This automation saves capture teams significant time in gathering and analyzing information, allowing them to focus on developing winning proposals rather than manual intelligence collection and document creation.

**What you get in the generated document:**

- **Executive Summary:** Decision brief for leadership go/no-go with PWin score
- **Market Analysis:** Spending trends, growth patterns, competitive landscape
- **Opportunity Profile:** Contract details, incumbent analysis, strategic value assessment
- **Competitive Positioning:** Your strengths vs. incumbent vs. field, with gap analysis
- **Win Themes:** AI-drafted differentiators based on data, with source citations
- **Teaming Strategy:** Recommended partners from subcontracting pattern analysis
- **Risk Assessment:** Modification history, pricing patterns, recompete indicators
- **Action Plan:** Next steps and capture strategy recommendations
- **Supporting Data:** Full methodology, source references, audit trail

**Impact:** Reduces capture planning from 73-100 hours to 8-11 hours (85% time savings)

**Output:** Professional Word document ready for leadership review or proposal kickoff. (PDF export planned)

## Why Privacy Matters

**Everything runs on your computer. Nothing leaves your building.**

- Your competitive strategy stays confidential
- Customer relationship intelligence remains private
- No risk of data leaks to competitors or vendors
- No subscription dependencies or per-user costs
- Works offline once installed
- You control who sees what

Unlike cloud-based competitors, your business intelligence never touches someone else's servers.

## The Technology: Proven and Mature

This isn't experimental. It's built on the same enterprise-grade technologies used by Fortune 500 companies:

- **Database:** PostgreSQL handling 66+ million contract records with instant queries
- **AI:** Local language models (like ChatGPT, but running on your PC) for narrative generation
- **Interface:** Modern web dashboard anyone can use without training
- **Automation:** Proven workflow orchestration and machine learning

**Hardware requirements:** Business-grade PC with decent graphics card. That's it.

## Business Impact: Real Numbers

### Time Savings Per Opportunity

| Activity                | Before           | After          | Improvement         |
| ----------------------- | ---------------- | -------------- | ------------------- |
| Market research         | 20-30 hours      | 2-3 hours      | 85% faster          |
| Competitive analysis    | 15-20 hours      | 1-2 hours      | 90% faster          |
| Incumbent research      | 10-15 hours      | 30 min         | 95% faster          |
| Capability comparison   | 8-10 hours       | 1 hour         | 90% faster          |
| Writing capture profile | 20-25 hours      | 3-4 hours      | 85% faster          |
| **Total**               | **73-100 hours** | **8-11 hours** | **~60 hours saved** |

### Annual Impact (20 Major Pursuits/Year)

- **1,200 hours returned** to your team (30 work-weeks)
- Equivalent to **adding a full-time senior analyst** without hiring costs
- Or **pursue 2-3x more opportunities** with the same team size
- **10% win rate improvement** = 2 additional contract wins
- **ROI typically achieved in 3-6 weeks**

### Quality Improvements

- **80%+ consistency** in capture profile quality and format
- **Traceable insights:** Every figure links back to source records
- **Knowledge retention:** Intelligence survives employee turnover
- **Faster decisions:** Leadership gets reliable intel when they need it

## Getting Started

### Prerequisites

- Windows PC with PostgreSQL installed
- Python virtual environment (included as `insight_venv`)
- Optional: Graphics card for AI features (NVIDIA recommended)

### Quick Start

1. **Configure environment variables:**

   - Copy `.env.example` to `.env`
   - Update database connection settings
   - Set any optional feature flags

2. **Activate the environment and launch:**

```powershell
# Activate virtual environment
& C:\GitHub\Data_Insights\insight_venv\Scripts\Activate.ps1

# Run the application
streamlit run C:\GitHub\Data_Insights\app.py
```

3. **Access the dashboard:**
   - Open your browser to the URL shown (typically http://localhost:8501)
   - Start with Strategic Dashboard to explore the data
   - Move to Advanced Opportunity Explorer for specific pursuits

### First Steps

1. **Explore the Strategic Dashboard** to understand overall market trends
2. **Filter by your target markets** (agencies, NAICS codes, regions)
3. **Review the Capability Stance** page to build your company profile
4. **Try the AI Data Agent** with simple questions about your market
5. **Generate your first capture profile** from the Opportunity Explorer

## Roadmap: Milestones to Full Capability

### Milestone 1: Core Functionality ✅ Complete

**1.1 Data Querying and Filtering**

- Filter contract data by agency, NAICS/PSC codes, date range, contract type
- Multi-dimensional filtering with smart defaults

**1.2 Visualization Suite**

- Interactive spending trends, top recipients, expiring contracts
- Market share analysis and geographic maps
- Export capabilities for reports

### Milestone 2: Advanced AI Tools 🛠️ Next 6 Months

**2.1 AI-Powered Visualization Tool**

- Context-aware chart generation from natural language
- Interactive drill-down with automated insights

**2.2 Conversational Data Agent (Chatbot)**

- Natural language querying and analysis
- Narrative generation for reports
- Local AI processing for privacy

**Impact:** Reduces analyst cognitive load through automation

### Milestone 3: External Data Integration 📅 12 Months

**3.1 SAM.gov and SBA SubNet**

- Active opportunity monitoring and alerts
- Subcontracting and mentor-protégé data

**3.2 GovWin IQ and Bloomberg Government**

- Advanced market intelligence
- Agency budget trends and policy impact

**Impact:** Forward-looking intelligence complements historical analysis

### Milestone 4: Enhanced Capture Management 📈 12-15 Months

**4.1 Pipeline and Opportunity Qualification**

- Automated opportunity feeds
- PWin scoring and bid/no-bid recommendations

**4.2 Competitive Analysis Dashboards**

- Real-time competitor tracking
- Teaming partner identification with capability matching

**Impact:** Proactive capture with automated qualification

### Milestone 5: Enhanced Capture Profile Generator 🎯 15-18 Months (Flagship)

**The Transformational Capability:**

**5.1 One-Click Document Generation**

- AI-driven narratives with source citations
- Integrated visualizations and strategic insights
- PWin calculations and ghosting strategies
- Teaming recommendations with rationale
- 9 comprehensive sections (see Capture Profile Generator above)

**5.2 Strategic Recommendations Engine**

- Multi-factor PWin calculations
- Competitor vulnerability analysis
- Pricing guidance from historical patterns
- Capture timeline recommendations

**Business Impact:**

- 85% time reduction (73-100 hours → 8-11 hours per opportunity)
- 3-6 week ROI for mid-size contractors
- 80%+ consistency without revision

**Export:** Word, PDF, and Markdown formats

### Milestone 6: Advanced Features 🚀 18-24 Months

**6.1 Advanced Filtering and Semantic Search**

- Keyword search across full contract text
- Multi-select filters with saved sets
- Complex natural language queries
- Custom role-based dashboards

**6.2 CRM Integration and Workflow Automation**

- Salesforce API for bidirectional data flow
- Automated pipeline updates
- Contact and relationship synchronization
- Proposal milestone tracking

**Impact:** Complete ecosystem from opportunity ID through proposal submission

## Support and Documentation

- **White Paper:** See `docs/WHITE_PAPER.md` for business case and ROI analysis
- **Technical Details:** Review `docs/PLANNING.md` for architecture and data model
- **Data Dictionary:** Reference `docs/CAPTUREINTEL.md` for field definitions
- **Product Requirements:** Check `docs/capture_insights_prd_v2.md` for feature specifications

## Key Differentiators

**vs. Cloud BI Tools:**

- ✅ Complete privacy—data never leaves your building
- ✅ No ongoing subscription costs
- ✅ Federal contracting domain expertise built-in
- ✅ AI features included, not add-ons

**vs. Commercial GovCon Databases:**

- ✅ Unlimited users at no additional cost
- ✅ Full data access, not filtered or sampled
- ✅ Customizable for your specific needs
- ✅ AI-generated narratives, not just data

**vs. Spreadsheets:**

- ✅ Handles 66+ million records instantly
- ✅ Consistent, repeatable analysis
- ✅ Professional document generation
- ✅ Knowledge that persists and grows

## Technical Architecture (For IT Teams)

- **Frontend:** Streamlit multipage app with custom navigation
- **Database:** PostgreSQL with three-schema ETL pipeline (raw → interim → processed)
- **Data Processing:** Automated deduplication, transformation, and indexing
- **AI:** Local LLM inference via Ollama (GPU-accelerated when available)
- **Agents:** Model Context Protocol (MCP) for advanced automation
- **Configuration:** Centralized via `config.py` with `.env` for secrets
- **Security:** No external API calls; allowlist monitoring; audit logging

**Key Pages:**

- Strategic Dashboard (`src/frontend/pages/strategic_dashboard.py`)
- Advanced Opportunity Explorer (`src/frontend/pages/advanced_opportunity_explorer.py`)
- Capability Stance (`src/frontend/pages/capability_stance.py`)
- AI Data Agent (`src/frontend/pages/ai_chat.py`)

## License & Status

Internal project for federal business development teams. Contact repository owner for access and implementation guidance.

---

**Bottom Line:** Data Insights transforms federal contract intelligence from a manual art into an automated science—letting your team focus on strategy, relationships, and winning, not data wrangling.
