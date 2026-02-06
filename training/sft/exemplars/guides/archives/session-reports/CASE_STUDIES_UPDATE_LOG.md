# Case Studies Document — Update Log

**Date:** February 6, 2026  
**File:** `motadata-coder_case-studies_2026-01-09.md`  
**Status:** ✅ Updated & Complete

---

## Changes Implemented

### 1. Added Case Study 7: IBM watsonx Code Assistant

**Location:** Line 337 (after Case Study 6)

**Content Added:**
- **Organization Profile:** IBM internal deployment, N=669 survey + N=15 usability testing
- **Key Findings:**
  - Majority reported net positive productivity (but **not uniform** across devs)
  - High ownership concern: "Who owns bugs in AI-generated code?"
  - Significant minority actively refused to use the assistant
  - Trust threshold: 30-50% acceptance rate
- **Critical Insight:** Benefits are heterogeneous, not universal
- **Relevance to Motadata:**
  - Enterprise reality mirror (hundreds of devs, not 10 friends)
  - Plan for 30-50% active usage, not 100%
  - Must define responsibility framework explicitly
  - Survey templates reusable for Motadata pilot

**Evidence Strength:** ★★★★★ (Peer-reviewed, large-N, mixed-methods)

---

### 2. Confirmed "Best vs Worst RCTs" Section Present

**Location:** Line 485 (between "Comparative Analysis" and "Risk Mitigation")

**Status:** ✅ Already in document (no changes needed)

**Content:**
- **Best Case (Turing RCT):** +15–33% PR uplift
- **Worst Case (METR RCT):** –19% productivity regression
- **Key Insight:** Without governance, you drift toward METR's worst case
- **Implications for Motadata:** 
  - Golden Exemplars = guardrails
  - CI-gated evaluation = reality check
  - Structured adoption required

---

### 3. Updated Citations & References

**Location:** Lines 739-742

**Added Three New Sources:**

1. **[paper:IBM-WCA]** — Justin D. Weisz et al., "Examining the Use and Impact of an AI Code Assistant on Developer Productivity and Experience in the Enterprise" (IBM, CHI EA 2025, Dec 2024).

2. **[study:Turing-PR]** — Turing Research, "Using LLM Coding Assistants to Increase Software Development Productivity" (Whitepaper / Blog, Jan 2026).

3. **[study:METR-2025]** — Joel Becker et al., METR, "Measuring the Impact of LLMs on Experienced Developer Productivity" (RCT report, July 2025).

**Category:** Additional Primary Sources (new subsection)

---

### 4. Updated Evidence Summary in Conclusion

**Location:** Lines 704-711

**Added:**
- IBM watsonx: Net positive but heterogeneous (30-50% usage)
- Best-case RCT (Turing): +15–33% PR uplift
- Worst-case RCT (METR): –19% productivity regression

**Total Evidence Sources:** Now 8 organizations + 2 RCTs

---

### 5. Updated Document Metadata

**Changes:**
1. **Header:** Added "(Updated: February 6, 2026)" to document date (line 3)
2. **Footer:** Changed status from "Complete, ready for download" to "Updated — Feb 6, 2026 (Added IBM WCA case study, Best/Worst RCT analysis)" (line 750)

---

## Document Structure (Verified)

### Case Studies (7 total)
1. ✅ Wiz — Fine-tuned security scanning (86% precision)
2. ✅ Together AI + Morph Labs — RAG fine-tuning (16-19% better than GPT-4o)
3. ✅ Tabnine — Enterprise self-hosted (94% pattern adherence)
4. ✅ GitHub Copilot — Enterprise benchmark (30% acceptance, 88% retention)
5. ✅ Enterprise Qwen — Production deployment (85%+ accuracy, 99.9% uptime)
6. ✅ TabbyML — Open-source self-hosted copilot
7. ✅ **IBM watsonx (NEW)** — Enterprise internal deployment (N=669 study)

### Major Sections
1. ✅ Executive Summary
2. ✅ Case Studies 1-7
3. ✅ Synthesis: What "50% of Coding Goals" Means
4. ✅ Comparative Analysis: Open-Source vs Closed-Source
5. ✅ Best vs Worst RCTs (NEW analysis framework)
6. ✅ Risk Mitigation
7. ✅ Evidence Strength Assessment
8. ✅ Recommendations for Motadata-Coder
9. ✅ Conclusion
10. ✅ Citations & References (3 new sources added)

---

## Quality Verification

### Linting
- ✅ No linter errors
- ✅ All markdown formatting valid
- ✅ Table structures correct

### Content Integrity
- ✅ All case studies maintain consistent format
- ✅ All citations properly tagged with [source:ID]
- ✅ All new content matches existing tone and style
- ✅ Evidence strength ratings included
- ✅ Relevance to Motadata sections included

### References
- ✅ All new citations ([paper:IBM-WCA], [study:Turing-PR], [study:METR-2025]) used consistently
- ✅ Citations section organized by category
- ✅ All sources properly attributed

---

## Impact Assessment

### Before Update
- 6 case studies
- Limited coverage of enterprise adoption heterogeneity
- No RCT-based productivity bracketing
- Missing productivity regression risk analysis

### After Update
- **7 case studies** (added IBM watsonx)
- **Enterprise reality check** (30-50% active usage, not 100%)
- **Productivity bracketing** (+15–33% best case, –19% worst case)
- **Failure mode analysis** (over-trust, context interference)
- **Governance justification** (Golden Exemplars prevent METR-style regression)

### For Motadata-Coder Strategy

**New Insights Added:**

1. **Adoption heterogeneity** — Not all devs will benefit equally
2. **Responsibility anxiety** — Developers unsure who owns AI bugs
3. **Productivity ceiling** — Best realistic case is +15–33%, not 100%+
4. **Regression risk** — Without governance, can cause –19% productivity loss
5. **Survey templates** — IBM's methodology reusable for Motadata pilot

**Strategic Implications:**

1. **Lower expectations** — Target 30-50% active usage, not 100%
2. **Define ownership** — Explicit responsibility framework required
3. **Track reality** — Compare perceived vs actual productivity (METR lesson)
4. **Validate governance** — Golden Exemplars justify their complexity

---

## Document Metrics

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| **Total Case Studies** | 6 | 7 | +1 |
| **Total Lines** | ~551 | ~753 | +202 |
| **Evidence Sources** | 10 | 13 | +3 |
| **RCT Studies** | 0 explicit | 2 explicit | +2 |
| **Enterprise Studies** | 2 | 3 | +1 (IBM) |
| **Evidence Strength (5-star)** | 2 | 3 | +1 (IBM) |

---

## Key Additions Summary

### Case Study 7 (IBM watsonx)
- **Sample Size:** N=669 (largest developer survey in doc)
- **Methodology:** Mixed-methods (survey + usability)
- **Key Finding:** Benefits heterogeneous; responsibility anxiety real
- **Strategic Value:** Sets realistic adoption expectations

### Best vs Worst RCTs Framework
- **Best Case (Turing):** +15–33% PR uplift
- **Worst Case (METR):** –19% regression without governance
- **Strategic Value:** Justifies Golden Exemplars investment

### New Citations
- IBM CHI paper (peer-reviewed, Dec 2024)
- Turing productivity whitepaper (Jan 2026)
- METR RCT report (Jul 2025)

---

## Next Steps

### For Document
✅ Complete — No further action required

### For Motadata-Coder Program

**Informed by IBM WCA Study:**
1. Design pilot with explicit responsibility framework
2. Create adoption tracking (usage % vs impact %)
3. Prepare for 30-50% active usage, not 100%
4. Build survey using IBM's constructs

**Informed by METR RCT:**
1. Validate Golden Exemplars prevent over-trust
2. Track perceived vs actual productivity
3. Focus on experienced devs as high-risk group
4. Test on large codebase tasks explicitly

---

## File Status

**Location:** `/root/m-coder/training/sft/exemplars/guides/motadata-coder_case-studies_2026-01-09.md`

**Status:** ✅ Production-ready  
**Lines:** 753 (updated from 551)  
**Linting:** ✅ No errors  
**Completeness:** ✅ All sections updated  
**Citations:** ✅ All references added

---

**Update Complete:** February 6, 2026  
**Implemented by:** AI Assistant  
**Program:** Golden Exemplars — Motadata AI Training
