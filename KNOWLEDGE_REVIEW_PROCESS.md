# Knowledge Review Process for TCM Knowledge Base

**PURPOSE**

This knowledge base was AI-drafted and requires ongoing human/expert verification against reputable sources before being fully trusted. Special care must be taken for herb–drug interaction claims and pregnancy-related claims; these carry higher clinical risk and must be verified by qualified experts before being presented as authoritative to users.

**TRUSTED SOURCES TO VERIFY AGAINST (in priority order)**

1. NCCIH — National Center for Complementary and Integrative Health (https://www.nccih.nih.gov/)
2. MedlinePlus (https://medlineplus.gov/)
3. Memorial Sloan Kettering — About Herbs database (https://www.mskcc.org/cancer-care/diagnosis-treatment/symptoms-side-effects/supportive-care/herbs-supplements)
4. PubMed (peer-reviewed primary research) (https://pubmed.ncbi.nlm.nih.gov/)

**REVIEW PRIORITY ORDER**

- Tier 1 (verify first): any entry with drug interaction or pregnancy contraindication claims
- Tier 2: general symptom/constitution matching claims
- Tier 3: lifestyle/dietary suggestions (lowest risk)

**MONTHLY PROCESS**

- Review 5 entries per month, starting with any entry where `last_human_reviewed` is null, prioritized by tier above.
- For each entry:
  - Search the trusted sources listed above and confirm or correct the claim.
  - Add at least one authoritative citation URL to a new `verified_sources` field (an array of strings).
  - Update `last_human_reviewed` to today's date (ISO yyyy-mm-dd) and set `review_status` to `human_verified` once checked.
  - If a claim cannot be confirmed or is found to be incorrect, clearly flag it: set `review_status` to `flagged`, add explanatory text in `review_notes`, and either correct or remove the erroneous claim (do not leave it presented confidently).

Suggested JSON update pattern for an entry:

```json
{
  "id": "entry-123",
  "name": "Example Herb",
  "claims": {
    "drug_interactions": "may interact with warfarin",
    "pregnancy_contraindication": "avoid in pregnancy"
  },
  "verified_sources": [
    "https://www.example.org/article-about-interaction"
  ],
  "last_human_reviewed": "2026-08-29",
  "review_status": "human_verified",
  "review_notes": "Confirmed interaction with warfarin in MedlinePlus entry."
}
```

- Use conservative wording for any remaining uncertainty (e.g., "insufficient evidence"), and avoid presenting unverified claims as fact.

**TRACKING**

Maintain a simple progress table below to track verification status. Populate this manually or via a small extraction script that lists every entry ID across the TCM knowledge files (for example: `data/tcm_constitutions.json`, `data/tcm_herbs_formulas.json`, and any future files in `data/` that contain knowledge entries).

| Entry ID | Entry Name | Source File | Tier | last_human_reviewed | review_status | verified_sources | Notes |
|---|---|---|---:|---|---|---|---|
| angelica_sinensis | Chinese Angelica Root (Dong Quai) | herbs_formulas | 1 | Not yet | ai_drafted_pending_review |  | Avoid in pregnancy unless directed; interacts with anticoagulant drugs |
| astragalus | Astragalus Root | herbs_formulas | 1 | Not yet | ai_drafted_pending_review |  | Cautions mention interactions with immunosuppressants and blood pressure medications |
| cinnamon | Cinnamon Bark / Twig | herbs_formulas | 1 | Not yet | ai_drafted_pending_review |  | Contraindicated during pregnancy; may interact with BP and blood sugar drugs |
| ginger | Fresh Ginger Root | herbs_formulas | 1 | Not yet | ai_drafted_pending_review |  | May increase bleeding risk with high-dose blood thinners |
| ginseng | Asian Ginseng Root | herbs_formulas | 1 | Not yet | ai_drafted_pending_review |  | May interact with blood thinners and diabetes medications |
| goji_berry | Goji Berry / Lycium Fruit | herbs_formulas | 1 | Not yet | ai_drafted_pending_review |  | May interact with anticoagulant medications such as warfarin |
| hawthorn_berry | Hawthorn Fruit | herbs_formulas | 1 | Not yet | ai_drafted_pending_review |  | Avoid during pregnancy due to potential uterine stimulation |
| licorice_root | Licorice Root | herbs_formulas | 1 | Not yet | ai_drafted_pending_review |  | Interactions with diuretics, corticosteroids, BP medications |
| xiao_yao_san | Free and Easy Wanderer | herbs_formulas | 1 | Not yet | ai_drafted_pending_review |  | Caution during pregnancy or heavy menstrual bleeding |

| chenpi | Aged Tangerine Peel | herbs_formulas | 2 | Not yet | ai_drafted_pending_review |  | Use caution in dry cough / Yin deficiency |
| chrysanthemum | Chrysanthemum Flower | herbs_formulas | 2 | Not yet | ai_drafted_pending_review |  | Allergy caution; constitution-specific cautions noted |
| erchen_tang | Two-Cured Decoction | herbs_formulas | 2 | Not yet | ai_drafted_pending_review |  | Contraindicated in dry cough from Yin deficiency |
| liuwei_dihuang_wan | Six-Ingredient Rehmannia Pill | herbs_formulas | 2 | Not yet | ai_drafted_pending_review |  | Contraindicated in weak spleen digestion or acute diarrhea |
| lily_bulb | Lily Bulb | herbs_formulas | 2 | Not yet | ai_drafted_pending_review |  | Generally mild; constitution-specific cautions |
| pinghe | Balanced Constitution | constitutions | 2 | Not yet | Not yet |  |  |
| qi-yu | Qi-Stagnation Constitution | constitutions | 2 | Not yet | Not yet |  |  |
| qixu | Qi-Deficiency Constitution | constitutions | 2 | Not yet | Not yet |  |  |
| sijunzi_tang | Four Gentlemen Decoction | herbs_formulas | 2 | Not yet | ai_drafted_pending_review |  | Classic formula for spleen Qi deficiency; professional evaluation recommended |
| shi-re | Damp-Heat Constitution | constitutions | 2 | Not yet | Not yet |  |  |
| tan-shi | Phlegm-Dampness Constitution | constitutions | 2 | Not yet | Not yet |  |  |
| te-bing | Special / Allergic Constitution | constitutions | 2 | Not yet | Not yet |  |  |
| tremella | Snow Fungus / White Jelly Mushroom | herbs_formulas | 2 | Not yet | ai_drafted_pending_review |  | Dietary/hydration use; avoid during early-stage acute colds with profuse phlegm |
| xue-yu | Blood-Stasis Constitution | constitutions | 2 | Not yet | Not yet |  |  |
| yangxu | Yang-Deficiency Constitution | constitutions | 2 | Not yet | Not yet |  |  |
| yinxu | Yin-Deficiency Constitution | constitutions | 2 | Not yet | Not yet |  |  |
| yu_ping_feng_san | Jade Windscreen Powder | herbs_formulas | 2 | Not yet | ai_drafted_pending_review |  | Not for high fever / acute heat-type infections |

| jujube | Chinese Red Date (Jujube) | herbs_formulas | 3 | Not yet | ai_drafted_pending_review |  | Primarily dietary; avoid excessive intake in certain digestive conditions |
| mung_bean | Mung Bean | herbs_formulas | 3 | Not yet | ai_drafted_pending_review |  | Dietary/cooling use; not suitable for cold Yang-deficient constitutions |
| poria | Poria Mushroom / Tuckahoe | herbs_formulas | 3 | Not yet | ai_drafted_pending_review |  | Generally mild; dietary use noted |

To generate a CSV of entry IDs from the current JSON files, you can run a quick Python snippet locally:

```bash
python - <<'PY'
import json, csv
files = ['data/tcm_constitutions.json','data/tcm_herbs_formulas.json']
out='tcm_entry_ids.csv'
rows=[]
for f in files:
    try:
        j=json.load(open(f,encoding='utf-8'))
        for e in (j if isinstance(j,list) else j.get('entries',[])):
            rows.append({'id': e.get('id') or e.get('name'), 'file': f})
    except Exception as exc:
        pass
with open(out,'w',newline='',encoding='utf-8') as csvf:
    writer=csv.DictWriter(csvf,fieldnames=['id','file'])
    writer.writeheader()
    writer.writerows(rows)
print('wrote',out)
PY
```

Notes and governance:

- Only credentialed reviewers (clinical or subject-matter experts) should clear Tier 1 items.
- Keep `verified_sources` URLs point to the primary source when possible (official guidance pages, peer-reviewed articles), not secondary blogs.
- Keep an audit trail in commit history for any edits to the knowledge files; require a short `review_notes` entry for each change.

---

Update and maintain the table above monthly; record which 5 entries were reviewed in each month and move on down the priority list until all entries have `review_status` set to `human_verified` or `flagged` with remediation completed.
# TCM Knowledge Base Human Review & Verification Process

> **Document Status**: Operational Guidelines  
> **Target Files**: `data/tcm_constitutions.json`, `data/tcm_herbs_formulas.json`, and all future knowledge base modules.

---

## 1. Purpose & Scope

The reference knowledge bases in this project ([`data/tcm_constitutions.json`](file:///C:/Users/SWI-No.1/my-first-agent/data/tcm_constitutions.json) and [`data/tcm_herbs_formulas.json`](file:///C:/Users/SWI-No.1/my-first-agent/data/tcm_herbs_formulas.json)) were initially compiled via structured AI drafting (`review_status: "ai_drafted_pending_review"`). 

Because this health chatbot surfaces TCM wellness guidance and herbal safety warnings directly to end-users without real-time medical supervision, **ongoing human expert verification against trusted clinical and pharmacological sources is required** before entries are flagged as fully verified (`"human_verified"`).

Special attention must be given to:
- **Herb-Drug Interactions** (e.g., blood thinners, immunosuppressants, anti-hypertensives).
- **Pregnancy & Lactation Contraindications** (e.g., uterine-stimulating or blood-invigorating herbs).
- **Severe Health Condition Contraindications** (e.g., renal impairment, high fever, active organ bleeding).

---

## 2. Trusted Reference Sources (Priority Order)

Reviewers and clinical evaluators must cross-reference all claims against the following authoritative medical and pharmacological databases in priority order:

1. **NCCIH (National Center for Complementary and Integrative Health)**
   - **URI**: [`https://www.nccih.nih.gov/health/herbsataglance`](https://www.nccih.nih.gov/health/herbsataglance)
   - **Focus**: NIH evidence-based herb overviews, safety profiles, and clinical advisories.

2. **MedlinePlus (U.S. National Library of Medicine)**
   - **URI**: [`https://medlineplus.gov/druginfo/herb_All.html`](https://medlineplus.gov/druginfo/herb_All.html)
   - **Focus**: Patient-facing drug and herbal supplement interaction safety data.

3. **Memorial Sloan Kettering Cancer Center — "About Herbs" Database**
   - **URI**: [`https://www.mskcc.org/cancer-care/diagnosis-treatment/symptom-management/integrative-medicine/herbs`](https://www.mskcc.org/cancer-care/diagnosis-treatment/symptom-management/integrative-medicine/herbs)
   - **Focus**: Detailed clinical summaries, mechanism of action, CYP450 enzyme interactions, and contraindications.

4. **PubMed / MEDLINE (Peer-Reviewed Clinical Literature)**
   - **URI**: [`https://pubmed.ncbi.nlm.nih.gov/`](https://pubmed.ncbi.nlm.nih.gov/)
   - **Focus**: Double-blind randomized controlled trials (RCTs), systematic reviews, and toxicological studies.

---

## 3. Review Priority Tiers

To maximize safety efficiency, verification must proceed according to the following 3-tier hierarchy:

### Tier 1: Critical Safety Entries (Verify First)
- **Criteria**: Any herb or formula with claims involving:
  - Anticoagulant / antiplatelet interactions (e.g., *Ginseng*, *Goji*, *Angelica*, *Ginger*, *Cinnamon*).
  - Pregnancy or uterine contractions (e.g., *Cinnamon*, *Angelica*, *Hawthorn*, *Xiao Yao San*).
  - Immunosuppressant or corticosteroid interactions (e.g., *Astragalus*, *Licorice*).
- **Action**: Verify contraindication phrasing against MSKCC or MedlinePlus before deployment.

### Tier 2: General Single Herbs & Classic Formulas
- **Criteria**: Single herbs and classic formulas with general safety cautions (e.g., *Chrysanthemum*, *Poria*, *Chenpi*, *Sijunzi Tang*, *Liu Wei Di Huang Wan*).
- **Action**: Verify traditional uses, typical non-prescriptive preparation forms, and Spleen/Stomach weakness cautions.

### Tier 3: General Lifestyle & Constitution Characteristics
- **Criteria**: Physical traits, disease susceptibilities, and dietary recommendations in [`data/tcm_constitutions.json`](file:///C:/Users/SWI-No.1/my-first-agent/data/tcm_constitutions.json).
- **Action**: Confirm alignment with Professor Wang Qi's Nine Constitution classification standards.

---

## 4. Metadata Maintenance & Audit Workflow

When a human reviewer verifies or updates an entry:

1. Open the JSON target file (e.g., `data/tcm_herbs_formulas.json`).
2. Update the top-level metadata:
   ```json
   {
     "last_updated": "YYYY-MM-DD",
     "last_human_reviewed": "YYYY-MM-DD",
     "review_status": "human_verified"
   }
   ```
3. Run the automated schema validation script:
   ```bash
   python scripts/verify_herbs_json.py
   ```
4. Verify that 0 specific dosage quantities or prescription frequency instructions were introduced during review.
