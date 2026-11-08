# -*- coding: utf-8 -*-
import sys, os, csv, math
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT))

from spec import *

# Derived from the single window definition in spec.py so the generated
# workbook, CSVs and schema cannot silently drift back to an older window.
WIN_QUARTERS = 4 * (int(WIN_END[:4]) - int(WIN_START[:4])) + (int(WIN_END[-1]) - int(WIN_START[-1])) + 1
MIN_QUARTERS = math.ceil(WIN_QUARTERS * 0.70)
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter as L
from openpyxl.formatting.rule import CellIsRule

# Output root. Defaults to <project>/build so regenerating never clobbers the
# checked-in Phase 2 deliverables at the project root. Override with:
#   EWS_OUT=/some/dir python build.py
OUT = Path(os.environ.get("EWS_OUT", PROJECT / "build")).resolve()
CSVD = OUT / "csv"
os.makedirs(CSVD, exist_ok=True)

# ------------------------------------------------------------------ helper tables
COMPILER = {
 "USA": {"ACT_GDP_REAL": "BEA", "ACT_IP": "Federal Reserve Board", "ACT_EMP": "BLS", "ACT_RINC": "BEA", "ACT_CONS": "BEA",
         "ACT_RETAIL": "U.S. Census Bureau", "ACT_INV": "BEA", "LAB_UNEMP": "BLS", "LAB_CLAIMS": "US Dept of Labor", "LAB_VAC": "BLS",
         "LAB_WAGE": "BLS", "PRC_CPI": "BLS", "PRC_CPI_CORE": "BLS", "PRC_PPI": "BLS", "PRC_DEFL": "BEA", "INC_SAVRATE": "BEA",
         "FIN_POLICY": "Federal Reserve", "FIN_SHORT": "Federal Reserve / US Treasury", "FIN_LONG": "Federal Reserve / US Treasury",
         "FIN_M2": "Federal Reserve", "SEN_CCI": "University of Michigan", "FIN_FCI": "Chicago Fed", "SEN_CAPUTIL": "Federal Reserve Board",
         "FIN_HOUSING_START": "U.S. Census Bureau"},
 "JPN": {"ACT_GDP_REAL": "Cabinet Office (ESRI) [verified role]", "ACT_CONS": "Cabinet Office (ESRI) [verified role]", "ACT_INV": "Cabinet Office (ESRI) [verified role]",
         "ACT_RINC": "Cabinet Office (ESRI) [role recalled]", "ACT_IP": "METI [verified role]", "ACT_EMP": "MIC Statistics Bureau [verified role]",
         "LAB_UNEMP": "MIC Statistics Bureau [verified role]", "LAB_WAGE": "MHLW [verified role]", "FIN_POLICY": "BOJ [recalled]", "FIN_SHORT": "BOJ [recalled]",
         "FIN_LONG": "JSDA [verified: SDDS table lists JSDA for government bond yield]", "FIN_M2": "BOJ (money stock) [verified]", "PRC_CPI": "MIC [verified]", "PRC_PPI": "BOJ (CGPI) [verified]", "FIN_EQUITY": "Nikkei 225 is the SDDS-listed index (private provider; outside chain) [verified]", "EXT_RESERVES": "MOF [verified]", "EXT_CA": "MOF (balance of payments) [verified]", "SEN_NAT_BUS": "BOJ (Tankan) [recalled]"},
 "IND": {"ACT_GDP_REAL": "MoSPI / NSO", "ACT_CONS": "MoSPI / NSO", "ACT_INV": "MoSPI / NSO", "ACT_RINC": "MoSPI / NSO [availability pending]", "ACT_IP": "MoSPI / NSO",
         "PRC_CPI": "MoSPI / NSO", "PRC_CPI_CORE": "MoSPI / NSO", "ACT_EMP": "MoSPI (PLFS) [verified]", "LAB_UNEMP": "MoSPI (PLFS) [verified]",
         "FIN_POLICY": "RBI", "FIN_SHORT": "RBI / FIMMDA [recalled]", "FIN_LONG": "RBI / FIMMDA [recalled]", "FIN_M2": "RBI", "FIN_BANKCREDIT": "RBI",
         "EXT_RESERVES": "RBI", "SEN_NAT_BUS": "RBI [recalled]", "SEN_NAT_CONS": "RBI [recalled]"},
 "CHN": {k: "NBS [expected]" for k in ["ACT_GDP_REAL", "ACT_IP", "ACT_RETAIL", "ACT_CONS", "ACT_INV", "ACT_EMP", "PRC_CPI", "PRC_PPI", "SEN_PMI"]},
}

IND_BASE = ("2022-23 (new series, verified: MoSPI release 2026-02-27); legacy 2011-12")
IND_BC = ("Reported/verified 2026-10-24: MoSPI released the new national accounts series with base 2022-23 on 2026-02-27, replacing base 2011-12; "
          "new-series quarterly estimates are reported from Q1 FY2022-23; full back series reported as due by Dec 2026 (secondary source, UNVERIFIED). "
          "Legacy 2011-12 and earlier bases require splicing.")
IND_KI = "FY quarters (Q1 = Apr-Jun = calendar Q2) must be re-labelled; legacy quarterly start date PENDING_VERIFICATION."
OV = {
 ("IND", "ACT_GDP_REAL"): dict(base=IND_BASE, bc=IND_BC, ki=IND_KI, risk="ELEVATED (verified fact: short new-series history; splice needed)", q=["Q-07", "Q-09"]),
 ("IND", "ACT_CONS"): dict(base=IND_BASE, bc=IND_BC + " Expenditure components are released with GDP (verified); specific PFCE line not checked.", ki=IND_KI, risk="ELEVATED (verified fact: splice needed)", q=["Q-07", "Q-09"]),
 ("IND", "ACT_INV"): dict(base=IND_BASE, bc=IND_BC + " Expenditure components are released with GDP (verified); a business-investment split is NOT confirmed.", ki=IND_KI, risk="ELEVATED (verified fact: splice needed; business split unconfirmed)", q=["Q-02", "Q-07"]),
 ("IND", "ACT_RINC"): dict(base=PEND, bc=PEND, ki="Quarterly household disposable income may not exist for India (hypothesis, unverified).", risk="ELEVATED (hypothesis)", q=["Q-04", "Q-06"]),
 ("IND", "ACT_IP"): dict(base="2022-23 reported (secondary sources, June 2026); legacy 2011-12", bc="Reported by secondary sources: new IIP base 2022-23 (mid-2026). Verify on MoSPI; splice with legacy IIP.", ki="Splice windows PENDING.", risk="ELEVATED (reported base change)", q=["Q-08"]),
 ("IND", "PRC_CPI"): dict(base="2024 (reported, PRS Feb 2026 summary; secondary)", bc="New CPI series with base 2024 reported (secondary); verify on MoSPI; splice with legacy CPI.", ki=PEND, risk="UNKNOWN", q=["Q-08"]),
 ("IND", "PRC_CPI_CORE"): dict(base="2024 (reported; secondary)", bc="Follows headline CPI rebase (reported); core definition under new series PENDING.", ki=PEND, risk="UNKNOWN", q=["Q-08"]),
 ("IND", "PRC_PPI"): dict(base="WPI 2011-12 (legacy); Output PPI 2022-23 (reported)", bc="Reported (secondary): new Output PPI base 2022-23; whether WPI continues is UNVERIFIED.", ki="WPI vs PPI continuity PENDING.", risk="ELEVATED (reported series change)", q=["Q-08"]),
 ("IND", "ACT_EMP"): dict(base=NAV, bc="PLFS revamp (verified): quarterly urban-only from 2017 to Dec 2024; monthly bulletins from April 2025; quarterly rural+urban from Apr-Jun 2025.", ki="No continuous all-India quarterly employment series confirmed for 1990-2016.", risk="ELEVATED (verified fact)", q=["Q-04", "Q-06", "Q-09"]),
 ("IND", "LAB_UNEMP"): dict(base=NAV, bc="Same PLFS revamp as employment (verified).", ki="Pre-2017 history PENDING.", risk="ELEVATED (verified fact)", q=["Q-09"]),
 ("IND", "ACT_HOURS"): dict(base=PEND, bc=PEND, ki="Official quarterly total hours for India not recalled (hypothesis).", risk="ELEVATED (hypothesis)", q=["Q-05", "Q-06"]),
 ("IND", "ACT_RETAIL"): dict(base=PEND, bc=PEND, ki="No official monthly retail sales index recalled for India (hypothesis).", risk="ELEVATED (hypothesis)", q=["Q-03", "Q-06"]),
 ("CHN", "ACT_GDP_REAL"): dict(base=PEND, bc=PEND, ki="NBS publishes y/y and SA q/q growth (verified); level index must be constructed; third-party start Mar 1992 UNVERIFIED.", risk="ELEVATED (verified: growth rates only)", q=["Q-11"]),
 ("CHN", "ACT_IP"): dict(base=PEND, bc=PEND, ki="NBS concept is industrial value added (recalled), not an IP volume index.", risk="UNKNOWN", q=["Q-11"]),
 ("CHN", "ACT_RETAIL"): dict(base=PEND, bc=PEND, ki="NBS retail sales are nominal (recalled); real series needs a deflator.", risk="ELEVATED (hypothesis)", q=["Q-03", "Q-11"]),
 ("CHN", "ACT_EMP"): dict(base=PEND, bc=PEND, ki="Quarterly employment availability doubtful (hypothesis).", risk="ELEVATED (hypothesis)", q=["Q-11"]),
 ("CHN", "ACT_HOURS"): dict(base=PEND, bc=PEND, ki="Hours worked availability doubtful (hypothesis).", risk="ELEVATED (hypothesis)", q=["Q-05", "Q-11"]),
 ("CHN", "ACT_RINC"): dict(base=PEND, bc=PEND, ki="Quarterly household income concept PENDING.", risk="ELEVATED (hypothesis)", q=["Q-04", "Q-11"]),
 ("JPN", "ACT_GDP_REAL"): dict(base=PEND, bc=PEND, ki="SNA benchmark revisions/base changes and chain splice PENDING (Q-12).", risk="UNKNOWN", q=["Q-12"]),
}
OV[("JPN", "FIN_LONG")] = dict(base=PEND, bc=PEND, ki="Chain-head producer is JSDA (private body) per the e-Stat table: decision Q-12 uses the next chain source (OECD) unless official BOJ hosting is confirmed.", risk="UNKNOWN", q=["Q-12"], pref=True)
OV[("JPN", "FIN_EQUITY")] = dict(base=PEND, bc=PEND, ki="Chain-head producer is Nikkei (private index provider) per the e-Stat table: decision Q-12 uses the next chain source (OECD) unless official hosting is confirmed.", risk="UNKNOWN", q=["Q-12"], pref=True)
for k in ["ACT_IP", "ACT_EMP", "LAB_UNEMP", "LAB_WAGE", "FIN_POLICY"]:
    OV.setdefault(("JPN", k), dict(base=PEND, bc=PEND, ki="Compiling agency differs by series (Q-12).", risk="UNKNOWN", q=["Q-12"]))
IQ = {"LAB_UNEMP": ["Q-01"], "ACT_INV": ["Q-02"], "ACT_RETAIL": ["Q-03", "Q-24"], "ACT_EMP": ["Q-04"], "ACT_RINC": ["Q-04", "Q-24"], "ACT_HOURS": ["Q-05"],
      "FIN_CREDIT_GDP": ["Q-16", "Q-20"], "FIN_CREDIT_GAP": ["Q-16", "Q-20"], "FIN_BANKCREDIT": ["Q-16", "Q-20"], "FIN_HHCREDIT": ["Q-16", "Q-20"], "FIN_DSR": ["Q-16", "Q-20"],
      "FIN_HOUSEPRICE": ["Q-16", "Q-24", "Q-26"], "FIN_EQUITY": ["Q-27"], "FIN_MCAP_GDP": ["Q-27", "Q-31"], "SEN_CCI": ["Q-28"], "SEN_BCI": ["Q-28"], "SEN_PMI": ["Q-17", "Q-23", "Q-28"],
      "SEN_EPU": ["Q-17"], "COM_OIL": ["Q-18"], "COM_ENERGY": ["Q-18"], "COM_NONFUEL": ["Q-18"], "COM_FOOD": ["Q-18"], "GLB_VIX": ["Q-18", "Q-23"],
      "GLB_WORLD_IP": ["Q-17", "Q-18"], "GLB_WORLD_TRADE": ["Q-17", "Q-18"], "GLB_US_FCI": ["Q-18"], "GLB_US_SLOPE": ["Q-18"], "GLB_CHINA_ACT": ["Q-18"], "GLB_PARTNER_ACT": ["Q-18"],
      "ACT_POP": ["Q-31"], "ACT_GDPPC": ["Q-31"], "EXT_CA": ["Q-20"], "EXT_REER": ["Q-16", "Q-20"], "LAB_CLAIMS": ["Q-20"], "FIN_CREDITSPREAD": ["Q-17"], "SEN_INFLEXP": ["Q-23"],
      "PRC_CPI": ["Q-21"], "PRC_PPI": ["Q-21"]}
SIGN_APPLIES = {"growth": "growth rate", "rate": "level and 4Q change", "ratio": "level and 4Q change", "spread": "level", "survey": "level and 4Q change", "price": "YoY / QoQ change"}

def resolve_app(a):
    return ["GLOBAL"] if a == "GLOBAL" else (ALLC if a == "ALL" else a)

def chain_for(iso):
    return CHAIN.get(iso, DEFAULT_CHAIN)

def src_url(sid):
    return {r[0]: r[3] for r in SOURCE_REGISTRY}.get(sid, PEND)

def lag_text(ind, v):
    lc = v["lagc"] or ind["lagc"]
    if not v["lagc"] and lc in ("NA", "MONTHLY"):
        lc = "NA" if v["freq"] == "Q" else "MONTHLY"
    return LAG[lc]

def qagg_text(ind, v):
    if v["tag"] == "DERIVED":
        return "Derived after inputs are converted to quarterly (see notes); no separate aggregation."
    kind = v["kind"] or ind["kind"]
    t = QAGG.get((v["freq"], kind)) or QAGG.get((v["freq"], "flow")) or "PENDING"
    if ind["beai"] == "Y" and v["freq"] in ("M", "W"):
        t += " | " + QAGG_LABEL
    return t

# ------------------------------------------------------------------ generate rows
OPEN_Q = {q[0] for q in Q if q[7] != "DECIDED"}
rows = []
order_c = {c: i for i, c in enumerate(ALLC + ["GLOBAL"])}
order_i = {x["id"]: i for i, x in enumerate(IND)}
for ind_ in IND:
    for v in ind_["variants"]:
        for iso in resolve_app(v["app"] if v["app"] is not None else ind_["app"]):
            glob = iso == "GLOBAL"
            grp = "GLOBAL" if glob else GROUP[iso]
            ch = ["FRED", "IMF/WB supplement"] if glob else chain_for(iso)
            ov = OV.get((iso, ind_["id"]), {})
            derived = v["tag"] == "DERIVED"
            # --- sources
            if glob:
                pref = "FRED (USA chain assumed for global series; Q-18)" if v["us"] else "IMF/World Bank supplement (hierarchy undefined; Q-18)"
                alts = ["IMF/World Bank supplement", NAV, NAV]
                chain_txt = "GLOBAL series: hierarchy not defined in §7 (assumed FRED -> IMF/WB supplement; Q-18)"
                pid = v["us"] if v["us"] else PEND
            else:
                chain_txt = " > ".join(SRC[c].split(" (")[0] if c != "BOJ_OFFICIAL" else "BOJ/official" for c in ch)
                pref = SRC[ch[0]]
                al = [SRC[c] for c in ch[1:]] + [NAV] * 3
                alts = al[:3]
                pid = v["us"] if (iso == "USA" and v["us"]) else PEND
            if ov.get("pref") and not glob:
                pref = SRC["OECD"] + " (decision Q-12: chain head carries only a private-provider series)"
                alts = [SRC["BOJ_OFFICIAL"] + " (only if official hosting confirmed)", SRC["BIS"], NAV]
            if derived:
                pid, idst = "DERIVED (no download; inputs: see notes)", "DERIVED"
            elif ind_["id"] == "SEN_CLI" and not glob:
                idst = "DATAFLOW_OBSERVED_SERIES_KEY_PENDING"
            elif pid != PEND:
                idst = "ID_RECALLED_NOT_VERIFIED"
            else:
                idst = "PENDING_VERIFICATION"
            if pid not in (PEND,) and not derived and not str(pid).startswith("DERIVED"):
                url, ust = "https://fred.stlouisfed.org/series/" + pid, "constructed_from_unverified_id"
            elif glob and not v["us"]:
                url, ust = src_url("IMF"), "portal_root"
            else:
                sid = "FRED" if glob else ch[0]
                url, ust = src_url(sid), "portal_root"
            a1u = src_url(ch[1]) if (not glob and len(ch) > 1) else PEND
            # --- status / priority
            prio = ind_["prio"]
            status = {"P0": "CANDIDATE_CORE", "P1": "CANDIDATE_CORE", "P2": "CANDIDATE_SUPPLEMENTARY", "P3": "CANDIDATE_OPTIONAL"}[prio]
            excl = "NONE_ASSIGNED (pending coverage audit; failed series stay documented, §8)"
            if ind_["role"] == "COMPARATOR_ONLY":
                status, excl = "COMPARATOR_ONLY", "Not a model feature: comparator only (§63, §66)."
            if ind_["role"] == "SUPPORT_INPUT":
                status, excl = "SUPPORT_INPUT", "Denominator for per-capita transforms only."
            iid = ind_["id"]
            if iid == "SEN_PMI" and iso != "CHN":
                status, excl = "CANDIDATE_CONDITIONAL", "Conditional (decision Q-17): kept only if a §7 source hosts the PMI; excluded after the verification pass if absent."
            elif iid in ("GLB_WORLD_IP", "GLB_WORLD_TRADE"):
                status, excl = "CANDIDATE_CONDITIONAL", "Conditional (decision Q-18): IMF supplement only; excluded if IFS does not carry it; GLB_PANEL_IP is the primary global-IP feature."
            elif iid == "SEN_EPU" and iso != "USA":
                status, excl = "EXCLUDED_BY_DECISION", "Decision Q-17: no §7 source hosts non-US policy-uncertainty indices."
            if iid == "EXT_FX_USD" and iso == "USA":
                status, excl = "NOT_APPLICABLE", "USD is the numeraire; use EXT_REER for the US."
            held = status in ("EXCLUDED_BY_DECISION", "NOT_APPLICABLE")
            # --- batch
            if held:
                batch = "NOT_COLLECTED"
            elif prio == "P0":
                batch = {"TIER1": "B01", "TIER2": "B02"}.get(grp, "B03")
            elif prio == "P1":
                batch = {"TIER1": "B04", "GLOBAL": "B04", "TIER2": "B05"}.get(grp, "B06")
            elif prio == "P2":
                batch = {"TIER1": "B07", "GLOBAL": "B07", "TIER2": "B08"}.get(grp, "B09")
            else:
                batch = "B10"
            # --- label / predictor
            if ind_["beai"] == "Y":
                lt = ind_["label_tx"]
                lc = ind_["label_c"] + ("; Label B input" if ind_["id"] == "ACT_GDP_REAL" else "")
                bw = NAV
            elif ind_["beai"] == "PENDING_DECISION":
                lt = "PENDING_DECISION (Q-01): if approved, g = first difference, sign flipped so + = stronger activity (§14)."
                lc, bw = ind_["label_c"], ind_["beai_why"]
            else:
                lt, lc, bw = "NOT_APPLICABLE (firewall: not BEAI-eligible)", ind_["label_c"], ind_["beai_why"] or NB
            if ind_["pred_c"].startswith("N"):
                pt = "NOT_APPLICABLE: " + ind_["pred_c"]
            else:
                pt = ind_["pred_tx"] or FORM_TX[ind_["form"]]
            sup = ind_["role"] == "SUPPORT_INPUT"
            qs = list(IQ.get(ind_["id"], [])) + list(ov.get("q", []))
            if iso == "IND" and ind_["beai"] == "Y": qs.append("Q-06")
            if iso == "CHN": qs.append("Q-11")
            if iso == "JPN": qs.append("Q-12")
            if iso == "DEU": qs.append("Q-13")
            if grp == "BROAD_OECD" and prio == "P0": qs.append("Q-14")
            if grp in ("BROAD_OECD", "CHINA", "TIER2") or iso in ("JPN",): qs.append("Q-15")
            if iso == "IND": qs.append("Q-10")
            if ind_["sa"].startswith("SA preferred") and grp in ("BROAD_OECD", "CHINA", "TIER1"): qs.append("Q-19")
            qs.append("Q-32")
            qs = sorted(set(qs))
            qopen = [x for x in qs if x in OPEN_Q]; qdec = [x for x in qs if x not in OPEN_Q]
            ki = ov.get("ki", PEND)
            if iso == "DEU" and ind_["cat"] in (CAT[1], CAT[2], CAT[3]):
                ki = ("Reunification break 1990-91: check West Germany vs unified series (Q-13). " + ("" if ki == PEND else ki))
            S1, S4 = (NAV, NAV) if sup else (ind_["s1"], ind_["s4"])
            if sup or ind_["role"] == "COMPARATOR_ONLY" or ind_["pred_c"].startswith("N"):
                scom = "NOT_A_FEATURE"
            elif ind_["id"] == "FIN_LONG":
                scom = "COMPONENT_OF_FIN_SLOPE (sign tested on the spread)"
            else:
                ch_ = [h for h, sg in (("1Q_2Q", S1), ("4Q", S4)) if sg in ("POSITIVE", "NEGATIVE")]
                scom = "COMMITTED_ALL_HORIZONS" if len(ch_) == 2 else (f"COMMITTED_{ch_[0]}_ONLY" if ch_ else "NOT_COMMITTED (excluded from the §62 agreement statistic)")
            major = "Y" if (prio in ("P0", "P1") and scom != "NOT_A_FEATURE") else "N"
            row = dict(
                series_key=f"{iso}.{ind_['id']}.{v['freq']}.{v['tag']}", country_iso3=iso, country_name=("Global / panel-level" if glob else NAME[iso]),
                country_group=grp, indicator_id=ind_["id"], indicator_name=ind_["name"], category=ind_["cat"], subcategory=ind_["sub"],
                variant_tag=v["tag"], variant_description=v["desc"] or "Default variant",
                intended_role=ind_["role"], label_contribution=lc,
                predictor_contribution=("N (support input only)" if sup else ind_["pred_c"]),
                beai_eligible=ind_["beai"], beai_exclusion_reason=bw, label_pipeline_transform=lt, predictor_pipeline_transform=pt,
                source_chain=chain_txt, preferred_source=pref, preferred_source_series_id=pid, id_status=idst,
                preferred_source_url=url, url_status=ust,
                alt_source_1=alts[0], alt_source_1_series_id=PEND if alts[0] != NAV else NAV, alt_source_1_url=a1u if alts[0] != NAV else NAV,
                alt_source_2=alts[1], alt_source_2_series_id=PEND if alts[1] != NAV else NAV,
                alt_source_3=alts[2], alt_source_3_series_id=PEND if alts[2] != NAV else NAV,
                supplement_source_hint=ind_["imf"] or "IMF/World Bank only if chain sources fail (Q-30)",
                original_compiler_expected=COMPILER.get(iso, {}).get(ind_["id"], PEND if iso in COMPILER else "NSO / central bank via OECD (compiler PENDING_VERIFICATION)") if not glob else PEND,
                oecd_dataset_family_hint=ind_["oecd"] or NAV, bis_dataset_hint=ind_["bis"] or NAV,
                dataset_id_observed=("OECD.SDD.STES,DSD_STES@DF_CLI" if ind_["id"] == "SEN_CLI" else "NONE_OBSERVED"),
                native_frequency_expected=v["freq"], native_frequency_verified=PEND, units_expected=ind_["units"] or PEND, units_verified=PEND,
                sa_status_expected=ind_["sa"], sa_status_verified=PEND, target_window_start=WIN_START, target_window_end=WIN_END,
                collect_from="Earliest available (§6: preserve longest defensible history)", available_start_date=PEND, available_end_date=PEND,
                coverage_target_window_pct=PEND, missingness_pct=PEND, missingness_pattern=PEND,
                availability_risk=ov.get("risk", "UNKNOWN"), revision_class_prior=ind_["rev"] + " (class-level prior; not verified)",
                revision_status_verified=PEND, base_year_current=ov.get("base", PEND), base_year_changes=ov.get("bc", PEND), known_issues_to_check=ki,
                quarterly_transformation=qagg_text(ind_, v), availability_lag_assumption=lag_text(ind_, v),
                collection_method=("DERIVE_AFTER_INPUTS" if derived else "DOWNLOAD"),
                expected_sign_1Q_2Q=S1, expected_sign_4Q=S4,
                sign_rationale=(NAV if sup else (f"Applies to {SIGN_APPLIES.get(ind_['form'],'series')}. " + (ind_["why"] or "No directional prior stated; excluded from REWI sign-agreement statistic unless a sign is pre-committed (Q-22, §62)."))),
                sign_evidence_basis=ind_["basis"], sign_commitment=scom, major_predictor_for_sign_check=major, literature_support=ind_["lit"] or "none in matrix", redundancy_group=ind_["red"] or "none",
                ablation_entry_level_tier1=(ind_["abl1"] or NAV) if not (sup or ind_["role"] == "COMPARATOR_ONLY") else NAV,
                ablation_entry_level_tier2=(ind_["abl2"] or NAV) if not (sup or ind_["role"] == "COMPARATOR_ONLY") else NAV,
                proposal_section_ref=ind_["sec"], priority_class=prio, collection_batch=batch, collection_rank=0,
                inclusion_status=status, exclusion_reason=excl,
                row_verification_status=("PARTIAL: ID recalled (unverified); all other fields pending" if idst == "ID_RECALLED_NOT_VERIFIED" else
                                         ("PARTIAL: source facts verified 2026-10-24 (see base_year_changes / known issues); all else pending" if iso in ("IND", "CHN") and ov else "UNVERIFIED")),
                open_questions="; ".join(qopen) or "NONE", decisions_applied="; ".join(qdec) or "NONE", retrieval_date="NOT_YET_RETRIEVED", data_version_id="NOT_YET_RETRIEVED",
                notes=(ind_["notes"] or "NONE"))
            if derived:
                row["notes"] = (row["notes"] + " Derived: " + {"FIN_SLOPE": "FIN_LONG minus FIN_SHORT.", "ACT_GDPPC": "ACT_GDP_REAL / ACT_POP.", "GLB_US_FCI": "FIN_FCI (USA).",
                                "GLB_US_SLOPE": "FIN_SLOPE (USA).", "GLB_CHINA_ACT": "CHN ACT_IP / ACT_GDP_REAL.", "GLB_PARTNER_ACT": "partner ACT_GDP_REAL x trade weights."}.get(ind_["id"], "")).strip()
            rows.append(row)

# derived-row special chain text
for r in rows:
    if r["collection_method"] == "DERIVE_AFTER_INPUTS":
        r["preferred_source"] = "DERIVED"; r["source_chain"] = "DERIVED (no source download)"; r["preferred_source_url"] = NAV; r["url_status"] = NAV
        r["alt_source_1"] = r["alt_source_2"] = r["alt_source_3"] = NAV
        r["alt_source_1_series_id"] = r["alt_source_2_series_id"] = r["alt_source_3_series_id"] = r["alt_source_1_url"] = NAV
        r["original_compiler_expected"] = NAV

# ranks
BO = {"B01": 1, "B02": 2, "B03": 3, "B04": 4, "B05": 5, "B06": 6, "B07": 7, "B08": 8, "B09": 9, "B10": 10, "NOT_COLLECTED": 99}
PO = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
rows.sort(key=lambda r: (BO[r["collection_batch"]], PO[r["priority_class"]], order_c[r["country_iso3"]], order_i[r["indicator_id"]], r["series_key"]))
for i, r in enumerate(rows, 1):
    r["collection_rank"] = i if r["collection_batch"] != "NOT_COLLECTED" else 9999
assert len({r["series_key"] for r in rows}) == len(rows), "duplicate keys"
bad = [r["series_key"] for r in rows if r["beai_eligible"] == "Y" and r["indicator_id"] not in
       ["ACT_GDP_REAL", "ACT_IP", "ACT_EMP", "ACT_HOURS", "ACT_RINC", "ACT_CONS", "ACT_RETAIL", "ACT_INV"]]
assert not bad, bad
COLS = list(rows[0].keys())

# ------------------------------------------------------------------ schema
G = {}
def S(name, grp, dtype, allowed, desc, example=""):
    G[name] = (grp, dtype, allowed, desc, example)
def _fill(x): return x if str(x).strip() else "NOT_APPLICABLE"
S("series_key", "Identification", "string (PK)", "{ISO3}.{indicator_id}.{freq}.{variant_tag}", "Unique key = country x indicator x native frequency x variant (§8).", "USA.ACT_GDP_REAL.Q.NA")
S("country_iso3", "Identification", "string", "ISO3 or GLOBAL", "Economy code.", "IND")
S("country_name", "Identification", "string", "free text", "Economy name.", "India")
S("country_group", "Identification", "enum", "TIER1|TIER2|BROAD_OECD|CHINA|GLOBAL", "Panel tier (§5).", "TIER1")
S("indicator_id", "Identification", "string", "see Indicator_Dictionary", "Stable indicator code.", "ACT_IP")
S("indicator_name", "Identification", "string", "free text", "Indicator name.", "Industrial production index")
S("category", "Identification", "enum", "7 categories (Controlled_Vocab)", "Category from the brief.", "Coincident activity")
S("subcategory", "Identification", "string", "free text", "Sub-group; 'Core coincident (BEAI candidate, §11)' marks the eight label candidates.", "")
S("variant_tag", "Identification", "string", "STD|NA|LFS|ESTAB|US|US_CS|OECD_BIS|DERIVED", "Distinguishes alternative series for the same indicator/frequency.", "NA")
S("variant_description", "Identification", "string", "free text", "What the variant is.", "")
S("intended_role", "Role and firewall", "enum", "LABEL_AND_PREDICTOR_SEPARATE|PREDICTOR_ONLY|SUPPORT_INPUT|COMPARATOR_ONLY", "Role in Pipelines A/B.", "PREDICTOR_ONLY")
S("label_contribution", "Role and firewall", "string", "free text", "Contribution to label construction (§8).", "BEAI input (Pipeline A)...")
S("predictor_contribution", "Role and firewall", "string", "Y... | N...", "Contribution to the predictor set (§8).", "Y (Pipeline B)")
S("beai_eligible", "Role and firewall", "enum", "Y|N", "Y only for the eight §11 indicators (decision Q-01: unemployment is N). HARD FIREWALL.", "N")
S("beai_exclusion_reason", "Role and firewall", "string", "free text or NOT_APPLICABLE", "Why the series cannot enter BEAI.", "")
S("label_pipeline_transform", "Role and firewall", "string", "free text", "Pipeline A transformation (separate from B).", "")
S("predictor_pipeline_transform", "Role and firewall", "string", "free text", "Pipeline B transformation set (§26-29).", "")
S("source_chain", "Sources", "string", "free text", "Ordered source priority from §7.", "FRED > OECD > BIS")
S("preferred_source", "Sources", "string", "free text", "First source in the chain (availability PENDING).", "FRED (St. Louis Fed)")
S("preferred_source_series_id", "Sources", "string", "ID | PENDING_VERIFICATION | DERIVED", "Official series ID. Only recalled US FRED IDs are filled; all unverified.", "GDPC1")
S("id_status", "Sources", "enum", "ID_RECALLED_NOT_VERIFIED|DATAFLOW_OBSERVED_SERIES_KEY_PENDING|DERIVED|PENDING_VERIFICATION", "Verification state of the ID.", "PENDING_VERIFICATION")
S("preferred_source_url", "Sources", "url", "https URL", "Series URL (constructed) or portal root.", "https://fred.stlouisfed.org/series/GDPC1")
S("url_status", "Sources", "enum", "portal_root|constructed_from_unverified_id|NOT_APPLICABLE", "How the URL was built.", "portal_root")
S("alt_source_1", "Sources", "string", "free text", "First fallback in chain.", "OECD")
S("alt_source_1_series_id", "Sources", "string", "PENDING_VERIFICATION|NOT_APPLICABLE", "Series ID at fallback 1.", "")
S("alt_source_1_url", "Sources", "url", "https URL", "Portal root of fallback 1.", "")
S("alt_source_2", "Sources", "string", "free text", "Second fallback.", "BIS")
S("alt_source_2_series_id", "Sources", "string", "PENDING_VERIFICATION|NOT_APPLICABLE", "Series ID at fallback 2.", "")
S("alt_source_3", "Sources", "string", "free text", "Third fallback (India only).", "")
S("alt_source_3_series_id", "Sources", "string", "PENDING_VERIFICATION|NOT_APPLICABLE", "Series ID at fallback 3.", "")
S("supplement_source_hint", "Sources", "string", "free text", "IMF/World Bank supplement (§7).", "")
S("original_compiler_expected", "Sources", "string", "free text", "Expected compiling agency (provenance; tags show verification level).", "BEA")
S("oecd_dataset_family_hint", "Sources", "string", "free text", "OECD dataset family NAME (not an ID).", "")
S("bis_dataset_hint", "Sources", "string", "free text", "BIS dataset name where the BIS is native.", "")
S("dataset_id_observed", "Sources", "string", "free text", "Dataset/dataflow ID seen in documentation this session.", "NONE_OBSERVED")
S("native_frequency_expected", "Series properties", "enum", "D|W|M|Q|A", "Expected native frequency of this variant.", "Q")
S("native_frequency_verified", "Series properties", "enum", "D|W|M|Q|A|PENDING_VERIFICATION", "Verified frequency.", "")
S("units_expected", "Series properties", "string", "free text", "Expected unit concept.", "")
S("units_verified", "Series properties", "string", "free text", "Verified unit.", "")
S("sa_status_expected", "Series properties", "string", "free text", "Expected seasonal-adjustment status.", "SA preferred")
S("sa_status_verified", "Series properties", "enum", "SA|NSA|NOT_APPLICABLE|PENDING_VERIFICATION", "Verified status.", "")
S("target_window_start", "Series properties", "period", "YYYYQn", "Target window start (§6).", "1990Q1")
S("target_window_end", "Series properties", "period", "YYYYQn", "Target window end (§6).", WIN_END)
S("collect_from", "Series properties", "string", "free text", "Collect earliest available history (§6).", "")
S("available_start_date", "Series properties", "date", "YYYY-MM or PENDING_VERIFICATION", "First observation.", "")
S("available_end_date", "Series properties", "date", "YYYY-MM or PENDING_VERIFICATION", "Last observation.", "")
S("coverage_target_window_pct", "Series properties", "float", "0-100 or PENDING_VERIFICATION", f"Share of the {WIN_QUARTERS} quarters in {WIN_START}-{WIN_END} with data; the §19 threshold is 70% (>={MIN_QUARTERS} quarters).", "")
S("missingness_pct", "Series properties", "float", "0-100 or PENDING_VERIFICATION", "Missing share within the available span.", "")
S("missingness_pattern", "Series properties", "string", "free text", "Where gaps occur.", "")
S("availability_risk", "Series properties", "string", "UNKNOWN|ELEVATED (verified fact)|ELEVATED (hypothesis)|...", "Risk the series is unavailable; hypotheses are labelled.", "UNKNOWN")
S("revision_class_prior", "Series properties", "string", "HIGH|MEDIUM|LOW (class-level prior)", "Generic revision tendency of this indicator class (NOT verified for the series).", "HIGH")
S("revision_status_verified", "Series properties", "string", "free text", "Series-specific revision facts.", "")
S("base_year_current", "Series properties", "string", "free text", "Current base year.", "")
S("base_year_changes", "Series properties", "string", "free text", "Base-year/splice events.", "")
S("known_issues_to_check", "Series properties", "string", "free text", "Breaks and issues to verify.", "")
S("quarterly_transformation", "Transformation", "string", "free text", "Monthly->quarterly rule (§27).", "")
S("availability_lag_assumption", "Transformation", "string", "free text", "Lag assumption from §30 (class) used for Pipeline B only.", "")
S("collection_method", "Transformation", "enum", "DOWNLOAD|DERIVE_AFTER_INPUTS", "How the series is obtained.", "DOWNLOAD")
S("expected_sign_1Q_2Q", "Predictor semantics", "enum", "POSITIVE|NEGATIVE|AMBIGUOUS|NOT_APPLICABLE", "Pre-registered sign vs recession risk at 1Q-2Q (§8, §62).", "NEGATIVE")
S("expected_sign_4Q", "Predictor semantics", "enum", "POSITIVE|NEGATIVE|AMBIGUOUS|NOT_APPLICABLE", "Pre-registered sign at 4Q (RQ6).", "AMBIGUOUS")
S("sign_rationale", "Predictor semantics", "string", "free text", "Why; and which transform the sign refers to.", "")
S("sign_evidence_basis", "Predictor semantics", "string", "free text", "LITERATURE importance vs HYPOTHESIS. The matrix gives importance, rarely sign.", "")
S("sign_commitment", "Predictor semantics", "enum", "COMMITTED_ALL_HORIZONS|COMMITTED_4Q_ONLY|COMMITTED_1Q_2Q_ONLY|COMPONENT_OF_FIN_SLOPE...|NOT_COMMITTED...|NOT_A_FEATURE", "Whether a sign is pre-registered for the §62 sign-agreement check, by horizon.", "COMMITTED_ALL_HORIZONS")
S("major_predictor_for_sign_check", "Predictor semantics", "enum", "Y|N", "Y = P0/P1 predictor: must carry a committed sign (or be a component series).", "Y")
S("literature_support", "Predictor semantics", "string", "P-ids from literature matrix", "Matrix papers that use or rank the variable.", "P1;P5")
S("redundancy_group", "Predictor semantics", "string", "RG_*", "Overlap group for pruning (Q-22).", "RG_OUTPUT")
S("ablation_entry_level_tier1", "Predictor semantics", "enum", "A|B|C|D|E|F|NOT_APPLICABLE", "First §55 Track-1 level containing the series (provisional; Q-21).", "A")
S("ablation_entry_level_tier2", "Predictor semantics", "enum", "I|II|III|NOT_APPLICABLE", "First §55 Track-2 level (provisional).", "I")
S("proposal_section_ref", "Inclusion", "string", "§ refs", "Traceability to the proposal.", "§11")
S("priority_class", "Inclusion", "enum", "P0|P1|P2|P3", "Collection priority (analyst judgement, see README).", "P0")
S("collection_batch", "Inclusion", "enum", "B01..B10|NOT_COLLECTED", "Collection order batch.", "B01")
S("collection_rank", "Inclusion", "int", "1..N; 9999 for NOT_COLLECTED", "Global collection order.", "1")
S("inclusion_status", "Inclusion", "enum", "CANDIDATE_CORE|CANDIDATE_SUPPLEMENTARY|CANDIDATE_OPTIONAL|CANDIDATE_CONDITIONAL|EXCLUDED_BY_DECISION|NOT_APPLICABLE|COMPARATOR_ONLY|SUPPORT_INPUT|EXCLUDED_AFTER_AUDIT|INCLUDED_AFTER_AUDIT", "Decision state; final include/exclude only after the Phase 3 audit (§83).", "CANDIDATE_CORE")
S("exclusion_reason", "Inclusion", "string", "free text", "Reason for hold/exclusion.", "")
S("row_verification_status", "Inclusion", "string", "free text", "How much of the row is verified.", "UNVERIFIED")
S("open_questions", "Inclusion", "string", "Q-ids ; separated or NONE", "Logged items still awaiting verification or action that affect this row (Decisions_Log).", "Q-32")
S("decisions_applied", "Inclusion", "string", "Q-ids ; separated or NONE", "Decisions already taken (Decisions_Log) that govern this row.", "Q-01; Q-19")
S("retrieval_date", "Inclusion", "date", "YYYY-MM-DD or NOT_YET_RETRIEVED", "Retrieval date (§73).", "NOT_YET_RETRIEVED")
S("data_version_id", "Inclusion", "string", "free text", "Data version tag (§73).", "NOT_YET_RETRIEVED")
S("notes", "Inclusion", "string", "free text", "Other notes.", "")
missing = [c for c in COLS if c not in G]
assert not missing, missing

# ------------------------------------------------------------------ other tables
IND_COLS = ["indicator_id", "indicator_name", "category", "subcategory", "concept_definition", "intended_role", "beai_eligible", "beai_exclusion_reason",
            "applicability", "native_frequency_candidates", "form", "availability_lag_class", "expected_sign_1Q_2Q", "expected_sign_4Q", "sign_evidence_basis",
            "literature_support", "priority_class", "redundancy_group", "ablation_entry_level_tier1", "ablation_entry_level_tier2", "proposal_section_ref", "notes"]
ind_rows = []
for x in IND:
    app = x["app"]
    appt = "GLOBAL (single series)" if app == "GLOBAL" else ("ALL 40 economies" if app == "ALL" else ", ".join(app))
    ind_rows_notes = None
    ind_rows.append(dict(indicator_id=x["id"], indicator_name=x["name"], category=x["cat"], subcategory=x["sub"], concept_definition=x["concept"],
        intended_role=x["role"], beai_eligible=x["beai"], beai_exclusion_reason=(NAV if x["beai"] == "Y" else (x["beai_why"] or NB)), applicability=appt,
        native_frequency_candidates="; ".join(f"{v['freq']}.{v['tag']}" for v in x["variants"]), form=x["form"], availability_lag_class=x["lagc"],
        expected_sign_1Q_2Q=x["s1"], expected_sign_4Q=x["s4"], sign_evidence_basis=x["basis"], literature_support=x["lit"] or "none in matrix",
        priority_class=x["prio"], redundancy_group=x["red"] or "none", ablation_entry_level_tier1=x["abl1"] or NAV, ablation_entry_level_tier2=x["abl2"] or NAV,
        proposal_section_ref=x["sec"], notes=(x["notes"] or "NONE")))

CN = {
 "USA": ("Calendar quarters.", "NBER chronology available (Label C).", "Series IDs in the catalogue are recalled, not verified."),
 "JPN": ("Calendar quarters (fiscal year Apr-Mar used only for some annual data).", "Compiling agencies differ; consumption-tax episodes and SNA rebasing to check.", "BOJ API launched 2026-02-18; agency roles verified via e-Stat table."),
 "IND": ("Fiscal year Apr-Mar: FY Q1 = Apr-Jun = calendar Q2; re-label at ingestion.", "New 2022-23 national accounts base (2026-02-27); IIP/CPI/PPI base changes reported; PLFS revamp 2025.", "See Q-07 to Q-10."),
 "CHN": ("Calendar quarters.", "Growth-rate-only GDP publication; data-quality concerns; employment/hours doubtful.", "NBS portal verified; q/q is SA growth."),
 "DEU": ("Calendar quarters.", "1990-91 reunification break.", "Q-13."),
}
csr = []
for iso, nm, grp in COUNTRIES:
    ch = chain_for(iso)
    al = [SRC[c] for c in ch[1:]] + [NAV] * 3
    cn = CN.get(iso, ("Calendar quarters (assumed; verify).", "PENDING_VERIFICATION" + ("; transition-economy early-1990s coverage unknown" if iso in ("CZE", "HUN", "POL", "SVK", "SVN", "EST", "LVA", "LTU") else ""), "OECD -> BIS per §7."))
    csr.append(dict(country_iso3=iso, country_name=nm, country_group=grp, source_priority_chain=" > ".join(SRC[c].split(" (")[0] if c != "BOJ_OFFICIAL" else "BOJ/official" for c in ch),
                    preferred_source=SRC[ch[0]], alt_source_1=al[0], alt_source_2=al[1], alt_source_3=al[2], supplements="IMF; World Bank (§7)",
                    ablation_track=("Track 1: full 6-level (A-F)" if grp == "TIER1" else "Track 2: simplified 3-level (I-III)" if grp == "TIER2" else "Not in ablation (pooled panel only)"),
                    deep_dive_set=("Y" if grp in ("TIER1", "TIER2") else "N"), calendar_note=cn[0], structural_notes=cn[1], verified_facts=cn[2],
                    first_collection_batch=("B01 (P0)" if grp == "TIER1" else "B02 (P0)" if grp == "TIER2" else "B03 (P0, audit gate)")))

BATCHES = [("B01", "Tier 1 (USA, JPN, IND) x P0", "Label inputs for the three case studies; decides BEAI feasibility (§19)", "None"),
           ("B02", "Tier 2 x P0", "Label inputs for the five deep-dive countries", "None"),
           ("B03", "Broader OECD + China x P0", "Coverage audit: which countries pass §19 (>=6/8 core at >=70% coverage) before predictors are collected", "Gate for B06/B09"),
           ("B04", "Tier 1 x P1 + GLOBAL P1", "Core predictors incl. Baseline 2 inputs (§32)", "After B01"),
           ("B05", "Tier 2 x P1", "Core predictors", "After B02"),
           ("B06", "Broader panel x P1", "Core predictors for countries passing the B03 gate only", "B03 pass"),
           ("B07", "Tier 1 x P2 + GLOBAL P2", "Supplementary predictors for full ablation (§55 Track 1)", "After B04"),
           ("B08", "Tier 2 x P2", "Supplementary predictors", "After B05"),
           ("B09", "Broader panel x P2", "Supplementary predictors, gated", "B03 pass"),
           ("B10", "All x P3", "Optional, comparators and low-support series", "Time permitting"),
           ("NOT_COLLECTED", "EXCLUDED_BY_DECISION / NOT_APPLICABLE", "Excluded by a logged decision or structurally not applicable", "See exclusion_reason")]
PRIO_WHY = {"P0": "Required to build Pipeline A labels (§11) and to decide §19 eligibility; collect first.",
            "P1": "Core predictor: multiple anchor-paper support or required by §32 Baseline 2; expected to be harmonised in OECD/BIS (coverage expectation unverified).",
            "P2": "Supplementary predictor: narrower support or coverage; needed for the full §55 ablation.",
            "P3": "Optional/low-support, outside the source hierarchy, or time-permitting (§63)."}

VERIF = [
 ("V-01", "OECD.Stat offline since 2024-07-01; OECD Data Explorer; API host sdmx.oecd.org; 60 downloads per hour; example dataflow OECD.SDD.STES,DSD_STES@DF_CLI", "https://www.oecd.org/en/data/insights/data-explainers/2024/09/OECD-DE-FAQ.html ; https://www.oecd.org/en/data/insights/data-explainers/2024/09/api.html", TODAY, "Primary documentation"),
 ("V-02", "BIS dataset names (credit to non-financial sector, credit-to-GDP gaps, DSR, property prices selected/long, EER monthly, XRU, policy rates) and example benchmark revisions", "https://www.bis.org/statistics/", TODAY, "Primary documentation; series keys NOT verified"),
 ("V-03", "India new GDP series base 2022-23 released 2026-02-27; quarterly new-series estimates from Q1 FY2022-23; expenditure components released with GDP", "https://static.pib.gov.in/WriteReadData/specificdocs/documents/2026/feb/doc2026227806401.pdf ; https://static.pib.gov.in/WriteReadData/specificdocs/documents/2026/aug/doc_9745_20260831_15364001.pdf", TODAY, "PIB (government) press documents"),
 ("V-04", "India IIP base 2022-23, CPI base 2024, Output PPI base 2022-23, GDP back series due Dec 2026", "https://prsindia.org/files/policy/policy_annual_policy_review/Monthly Policy Review/2026-02-01/MPR-Feb_2026.pdf ; https://vajiramandravi.com/current-affairs/new-gdp-series-2022-23/", TODAY, "SECONDARY sources: verify on MoSPI"),
 ("V-05", "RBI DBIE portal and Handbook of Statistics scope (national income, prices, money, banking, markets, external)", "https://data.rbi.org.in ; https://website.rbi.org.in/", TODAY, "RBI pages"),
 ("V-06", "PLFS: quarterly urban-only from 2017; revamped 2025 with monthly bulletins from April 2025 and quarterly rural+urban from Apr-Jun 2025", "https://mospi.gov.in/sites/default/files/publication_reports/PLFS_Monthly_Bulletin_April_2025_final.pdf", TODAY, "MoSPI publications"),
 ("V-07", "BOJ Time-Series Data Search and API (launched 2026-02-18); e-Stat/SDDS table of agency roles; ESRI national accounts page", "https://www.boj.or.jp/en/statistics/outline/notice_2026/not260218a.htm ; https://www.e-stat.go.jp/en/data/nsdp/ ; https://www.esri.cao.go.jp/en/sna/menu.html", TODAY, "Official pages"),
 ("V-08", "NBS portal data.stats.gov.cn; q/q GDP growth is SA growth; quarterly-from-1992 claim from CEIC listing NOT verified at source", "https://www.stats.gov.cn/english/PressRelease/202610/t20261021_1965671.html ; https://www.ceicdata.com/en/china/gross-domestic-product-quarterly", TODAY, "NBS release verified; vendor claim unverified"),
 ("V-09", "Proposal rules used: §5-8, §9-20, §23-31, §32, §51-53, §55, §62, §65, §76, §83", "plan_ML.docx (uploaded)", TODAY, "Authoritative input"),
 ("V-10", "Literature matrix P-ids/D-ids/PA-ids used for sign evidence and source cross-references", "literature_matrix.xlsx (uploaded)", TODAY, "Authoritative input; matrix itself notes several items are abstract-level"),
 ("V-12", "RBI Handbook of Statistics 2025-26 (28th edition, 245 tables) released 2026-07-31; DBIE portal = data.rbi.org.in", "https://www.rbi.org.in/scripts/BS_PressReleaseDisplay.aspx?prid=63268", TODAY, "RBI press release (re-checked in self-review)"),
 ("V-13", "BIS listing includes Consumer prices, Policy rates (monthly), US dollar exchange rates, Effective exchange rate indices (monthly), Property prices selected/long, DSR, TOTAL_CREDIT; data.bis.org/bulkdownload exists", "https://data.bis.org/bulkdownload ; https://github.com/expersso/BIS", TODAY, "Portal page plus third-party package listings (re-checked in self-review)"),
 ("V-14", "e-Stat SDDS Plus table: producing agency per Japanese series (see Source_Registry); JSDA supplies government bond yield and Nikkei supplies the stock index", "https://www.e-stat.go.jp/en/data/nsdp/", TODAY, "Official portal (re-fetched in self-review)"),
 ("V-15", "SELF-REVIEW corrections applied 2026-10-24: (a) curve-slope literature support corrected (P5 removed; P2, P4, P9, P15, P17 added); (b) GDP-per-capita sign basis downgraded to hypothesis; (c) wrong blocking-question link for the OECD CLI removed; (d) Japan government-bond-yield and stock-index producers corrected; (e) Dua & Banerji URL taken from the matrix; (f) unsupported phrase about a legacy RBI host removed; (g) BIS portal URL status upgraded to verified", "this workbook", TODAY, "Internal audit"),
 ("V-16", "plan_ML.docx is the single authoritative proposal. A duplicate upload named plan_ML_1.docx was a naming error and carried no additional information, so every ambiguity was resolved by the most plan-aligned reading and logged in Decisions_Log with its deviation type.", "plan_ML.docx", "2026-10-29", "Naming clarification supplied by the project team 2026-10-29"),
 ("V-11", "NOT verified this session: every series ID other than the OECD DF_CLI dataflow; all US FRED IDs are recalled from memory; all start/end dates, missingness, units, SA status, revision facts", "n/a", TODAY, "Pending Phase 2 verification pass (Q-32)"),
]
CV = [("beai_eligible", "Y", "One of the eight §11 indicators"), ("beai_eligible", "N", "Never a BEAI input"), 
      ("intended_role", "LABEL_AND_PREDICTOR_SEPARATE", "Label (A) and predictor (B) copies built separately"), ("intended_role", "PREDICTOR_ONLY", "Pipeline B only"),
      ("intended_role", "SUPPORT_INPUT", "Denominator only"), ("intended_role", "COMPARATOR_ONLY", "Compared with model output only (§63)"),
      ("priority_class", "P0", "Label construction inputs"), ("priority_class", "P1", "Core predictors"), ("priority_class", "P2", "Supplementary"), ("priority_class", "P3", "Optional"),
      ("inclusion_status", "CANDIDATE_CORE", "P0/P1 candidate"), ("inclusion_status", "CANDIDATE_SUPPLEMENTARY", "P2 candidate"), ("inclusion_status", "CANDIDATE_OPTIONAL", "P3 candidate"),
      ("inclusion_status", "CANDIDATE_CONDITIONAL", "Kept only if a §7 source hosts it (Q-17, Q-18)"), ("inclusion_status", "EXCLUDED_BY_DECISION", "Excluded by a logged decision"), ("inclusion_status", "NOT_APPLICABLE", "Structurally n/a"), ("inclusion_status", "COMPARATOR_ONLY", "Not a feature"),
      ("inclusion_status", "SUPPORT_INPUT", "Input only"), ("inclusion_status", "INCLUDED_AFTER_AUDIT", "Post-audit decision (future)"), ("inclusion_status", "EXCLUDED_AFTER_AUDIT", "Post-audit decision (future)"),
      ("expected_sign", "POSITIVE", "Higher/rising value raises recession risk"), ("expected_sign", "NEGATIVE", "Higher/rising value lowers recession risk"), ("expected_sign", "AMBIGUOUS", "No pre-registered direction"),
      ("decision_status", "DECIDED", "Settled by a plan-aligned decision"), ("decision_status", "DECIDED_PENDING_VERIFICATION", "Decision taken; a fact still needs verifying"), ("decision_status", "OPEN_ACTION", "Action not yet done"), ("deviation_type", "NONE", "Follows the plan"), ("deviation_type", "INTERPRETATION", "Plan ambiguous; one reading chosen"), ("deviation_type", "EXTENSION", "Plan silent; rule added"), ("id_status", "ID_RECALLED_NOT_VERIFIED", "Recalled US FRED ID, unchecked"), ("id_status", "PENDING_VERIFICATION", "Unknown"),
      ("null tokens", "PENDING_VERIFICATION", "Fact not yet verified (never a guess)"), ("null tokens", "NOT_APPLICABLE", "Field does not apply"), ("null tokens", "NOT_YET_RETRIEVED", "Phase 3 not run"),
      ("frequency", "D|W|M|Q|A", "Daily, weekly, monthly, quarterly, annual")] + [("category", c, "One of the seven categories in the brief") for c in CAT.values()]

# ------------------------------------------------------------------ write CSV
def wcsv(name, header, data):
    with open(f"{CSVD}/{name}.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
        w.writerow(header)
        for d in data:
            w.writerow([d[h] if isinstance(d, dict) else d[i] for i, h in enumerate(header)] if isinstance(d, dict) else list(d))

wcsv("series_catalogue", COLS, rows)
wcsv("indicator_dictionary", IND_COLS, ind_rows)
CSR_COLS = list(csr[0].keys()); wcsv("country_source_rules", CSR_COLS, csr)
SR_COLS = ["source_id", "name", "project_role", "portal_url", "access_method", "url_status", "facts_verified_2026-10-24", "caveats"]; wcsv("source_registry", SR_COLS, SOURCE_REGISTRY)
CP_COLS = ["collection_rank", "collection_batch", "priority_class", "series_key", "country_iso3", "indicator_id", "indicator_name", "category", "intended_role", "preferred_source",
           "preferred_source_series_id", "id_status", "collection_method", "availability_risk", "inclusion_status", "open_questions"]
cp = sorted([r for r in rows], key=lambda r: r["collection_rank"]); wcsv("collection_priority", CP_COLS, cp)
wcsv("collection_batches", ["batch", "scope", "rationale", "gate"], BATCHES)
wcsv("label_firewall_rules", ["rule_id", "rule", "proposal_basis", "enforcement"], FIREWALL)
wcsv("label_references", ["ref_id", "applies_to", "reference", "use", "producer", "url", "url_status", "notes", "proposal_ref"], REFERENCES)
SC_COLS = ["column_name", "group", "data_type", "allowed_values_or_format", "description", "example"]
schema_rows = [tuple(_fill(v) for v in ((c,) + G[c])) for c in COLS]; wcsv("schema", SC_COLS, schema_rows)
wcsv("controlled_vocabularies", ["field", "value", "meaning"], CV)
USED_Q = {x for r in rows for x in (r["open_questions"] + "; " + r["decisions_applied"]).split("; ")}
DL_COLS = ["question_id", "area", "issue", "decision", "plan_basis", "deviation_type", "deviation_detail", "status", "remaining_action", "affected_series", "priority", "row_linked"]
DL_ROWS = [q + ("ROW_LINKED" if q[0] in USED_Q else "PROJECT_LEVEL",) for q in Q]
wcsv("decisions_log", DL_COLS, DL_ROWS)
UN_COLS = ["question_id", "area", "open_item", "decision_taken", "status", "affected_series", "priority"]
UN_ROWS = [(q[0], q[1], q[8], q[3], q[7], q[9], q[10]) for q in Q if q[7] != "DECIDED"]
wcsv("unresolved_questions", UN_COLS, UN_ROWS)
wcsv("verification_log", ["log_id", "fact", "source_url", "checked_on", "reliability"], VERIF)

# ------------------------------------------------------------------ write workbook
wb = Workbook()
F = "Arial"
HFILL = PatternFill("solid", fgColor="1F3864"); HFONT = Font(name=F, bold=True, color="FFFFFF", size=10)
BF = Font(name=F, size=10); TF = Font(name=F, size=14, bold=True)
thin = Side(style="thin", color="D9D9D9")

def sheet(name, header, data, widths=None, wrap=False, first=False, pend_rule=False):
    ws = wb.active if first else wb.create_sheet()
    ws.title = name
    ws.append(header)
    for d in data:
        ws.append([d[h] for h in header] if isinstance(d, dict) else list(d))
    for c in ws[1]:
        c.fill, c.font = HFILL, HFONT
        c.alignment = Alignment(wrap_text=True, vertical="center")
    for row in ws.iter_rows(min_row=2):
        for c in row:
            c.font = BF
            c.alignment = Alignment(wrap_text=wrap, vertical="top")
    for i, h in enumerate(header, 1):
        ws.column_dimensions[L(i)].width = (widths or {}).get(h, 18)
    ws.freeze_panes = "B2"
    ws.auto_filter.ref = ws.dimensions
    ws.row_dimensions[1].height = 30
    if pend_rule:
        ws.conditional_formatting.add(ws.dimensions, CellIsRule(operator="equal", formula=['"PENDING_VERIFICATION"'], fill=PatternFill("solid", bgColor="FFF2CC")))
    return ws

# README
rd = wb.active; rd.title = "README"
lines = [
 ("Phase 2 Data Dictionary: Cross-Country Recession Early-Warning Framework", "t"),
 (f"Generated {TODAY}. Authoritative inputs: plan_ML.docx (proposal; §n refs) and literature_matrix.xlsx (P-/D-/PA-ids). No data was downloaded and no model was trained.", ""),
 ("WHAT THIS IS", "h"),
 ("A catalogue of CANDIDATE series (country x indicator x native frequency x variant), their roles, source chains, transformations and open questions. It is the Phase 2 deliverable of §76 and feeds the Phase 3 audit (§83).", ""),
 ("HARD RULES", "h"),
 ("1. Only eight indicators may build BEAI (beai_eligible = Y): real GDP, industrial production, employment, real income, real consumption, retail/sales, business investment, hours worked (§11). Financial, credit, price, external, commodity, survey, global and other labour series are predictor-only. The Summary sheet has a live check that must show 0 violations.", ""),
 ("2. Unemployment is NOT a BEAI input (decision Q-01): §11, §12 and §19 define eight series without it, so §14's unemployment rule is treated as illustrative. It is a predictor only.", ""),
 ("3. For the eight dual-role indicators the label (Pipeline A) and predictor (Pipeline B) transformations are separate columns and separate pipelines; BEAI outputs are not predictors (§31).", ""),
 ("4. Source order follows §7 literally per country. IMF/World Bank are supplements only.", ""),
 ("DECISIONS AND DEVIATIONS", "h"),
 (f"Decisions_Log records {len(Q)} decisions taken on the most plan-aligned reading: {sum(q[7]=='DECIDED' for q in Q)} final, {sum(q[7]=='DECIDED_PENDING_VERIFICATION' for q in Q)} awaiting a fact check, {sum(q[7]=='OPEN_ACTION' for q in Q)} open actions. Deviation types: {sum(q[5]=='NONE' for q in Q)} follow the plan, {sum(q[5]=='INTERPRETATION' for q in Q)} are interpretations of an ambiguous clause, {sum(q[5]=='EXTENSION' for q in Q)} add a rule where the plan is silent. Unresolved_Questions lists only the items not yet DECIDED.", ""),
 ("VERIFICATION POLICY", "h"),
 ("PENDING_VERIFICATION = not yet verified (never a guess). Series IDs: only US FRED IDs that I recalled with high confidence are filled and flagged ID_RECALLED_NOT_VERIFIED; every non-US ID is pending. Start/end dates, missingness, units, SA status, revision facts and coverage % are ALL pending. Sheet Verification_Log lists what was actually checked on 2026-10-24 (India base-year changes, PLFS revamp, OECD/BIS/BOJ/NBS/RBI platform facts).", ""),
 ("ELIGIBILITY ARITHMETIC (from §19)", "h"),
 (f"Target window {WIN_START}-{WIN_END} = {WIN_QUARTERS} quarters. 70% coverage = {0.70 * WIN_QUARTERS:.1f}, so at least {MIN_QUARTERS} quarters per core indicator; a country needs >=6 of the 8 core indicators at that level, and a quarter needs >=4 core indicators to be dated (§18).", ""),
 ("PRIORITY CLASSES (analyst judgement, not from the proposal)", "h"),
 ("P0 label inputs; P1 core predictors (anchor-paper support or §32 Baseline 2); P2 supplementary; P3 optional. Collection order is in Collection_Batches; the broad panel is gated by the B03 audit.", ""),
 ("SHEETS", "h"),
 ("Summary (live formulas) | Series_Catalogue (master) | Indicator_Dictionary | Country_Source_Rules | Source_Registry | Collection_Priority | Collection_Batches | Priority_Indicators | Label_Firewall | Label_References | Schema | Controlled_Vocab | Decisions_Log | Unresolved_Questions | Verification_Log", ""),
 ("CSV: UTF-8, comma-separated, header row, semicolon-separated lists, tokens PENDING_VERIFICATION / NOT_APPLICABLE / NOT_YET_RETRIEVED. Files are in the csv folder.", ""),
]
for i, (t, k) in enumerate(lines, 1):
    c = rd.cell(row=i, column=1, value=t)
    c.font = TF if k == "t" else Font(name=F, bold=True, size=11, color="1F3864") if k == "h" else BF
    c.alignment = Alignment(wrap_text=True, vertical="top")
rd.column_dimensions["A"].width = 150

# Summary placeholder (filled after catalogue is written)
sm = wb.create_sheet("Summary")
cat_ws = sheet("Series_Catalogue", COLS, rows, widths={**{c: 22 for c in COLS}, "series_key": 34, "predictor_pipeline_transform": 50, "label_pipeline_transform": 50, "notes": 50,
               "known_issues_to_check": 40, "base_year_changes": 40, "quarterly_transformation": 40, "availability_lag_assumption": 34, "preferred_source_url": 40, "sign_rationale": 40,
               "exclusion_reason": 34, "label_contribution": 34, "oecd_dataset_family_hint": 34, "bis_dataset_hint": 30}, pend_rule=True)
cat_ws.freeze_panes = "C2"
sheet("Indicator_Dictionary", IND_COLS, ind_rows, widths={"concept_definition": 50, "notes": 50, "beai_exclusion_reason": 40, "sign_evidence_basis": 34, "indicator_name": 32, "subcategory": 28, "category": 26}, wrap=True)
sheet("Country_Source_Rules", CSR_COLS, csr, widths={"structural_notes": 50, "verified_facts": 40, "calendar_note": 40, "source_priority_chain": 28, "preferred_source": 30}, wrap=True)
sheet("Source_Registry", SR_COLS, SOURCE_REGISTRY, widths={"name": 34, "project_role": 36, "portal_url": 36, "access_method": 36, "url_status": 30, "facts_verified_2026-10-24": 70, "caveats": 50}, wrap=True)
sheet("Collection_Priority", CP_COLS, cp, widths={"series_key": 34, "indicator_name": 34, "preferred_source": 30, "category": 26})
sheet("Collection_Batches", ["batch", "scope", "rationale", "gate"], BATCHES, widths={"scope": 34, "rationale": 80, "gate": 24}, wrap=True)

# Priority_Indicators with formulas
pi_hdr = ["indicator_id", "indicator_name", "category", "intended_role", "beai_eligible", "priority_class", "why_this_priority", "literature_support", "proposal_section_ref", "series_rows_in_catalogue"]
pw = wb.create_sheet("Priority_Indicators"); pw.append(pi_hdr)
kcol = L(COLS.index("indicator_id") + 1)
for x in sorted(ind_rows, key=lambda r: (r["priority_class"], r["category"], r["indicator_id"])):
    n = pw.max_row + 1
    pw.append([x["indicator_id"], x["indicator_name"], x["category"], x["intended_role"], x["beai_eligible"], x["priority_class"], PRIO_WHY[x["priority_class"]],
               x["literature_support"], x["proposal_section_ref"], f"=COUNTIF(Series_Catalogue!${kcol}:${kcol},A{n})"])
for c in pw[1]: c.fill, c.font = HFILL, HFONT
for row in pw.iter_rows(min_row=2):
    for c in row: c.font = BF; c.alignment = Alignment(wrap_text=True, vertical="top")
for i, w in enumerate([22, 36, 28, 28, 14, 10, 70, 18, 18, 14], 1): pw.column_dimensions[L(i)].width = w
pw.freeze_panes = "B2"; pw.auto_filter.ref = pw.dimensions

sheet("Label_Firewall", ["rule_id", "rule", "proposal_basis", "enforcement"], FIREWALL, widths={"rule": 110, "proposal_basis": 24, "enforcement": 50}, wrap=True)
sheet("Label_References", ["ref_id", "applies_to", "reference", "use", "producer", "url", "url_status", "notes", "proposal_ref"], REFERENCES, widths={"reference": 40, "notes": 70, "url": 40}, wrap=True)
sheet("Schema", SC_COLS, schema_rows, widths={"column_name": 32, "group": 20, "data_type": 14, "allowed_values_or_format": 44, "description": 70, "example": 30}, wrap=True)
sheet("Controlled_Vocab", ["field", "value", "meaning"], CV, widths={"field": 20, "value": 34, "meaning": 60}, wrap=True)
sheet("Decisions_Log", DL_COLS, DL_ROWS, widths={"issue": 60, "decision": 80, "plan_basis": 26, "deviation_detail": 60, "remaining_action": 40, "affected_series": 28, "area": 16, "status": 26, "deviation_type": 16, "row_linked": 18}, wrap=True)
sheet("Unresolved_Questions", UN_COLS, UN_ROWS, widths={"open_item": 70, "decision_taken": 80, "affected_series": 30, "area": 16, "status": 28}, wrap=True)
sheet("Verification_Log", ["log_id", "fact", "source_url", "checked_on", "reliability"], VERIF, widths={"fact": 80, "source_url": 70, "reliability": 40}, wrap=True)

# Summary content
def colr(name):
    c = L(COLS.index(name) + 1); return f"Series_Catalogue!${c}$2:${c}${len(rows)+1}"
sm["A1"] = "Summary (live formulas over Series_Catalogue)"; sm["A1"].font = TF
items = [("Total candidate series rows", f"=COUNTA({colr('series_key')})"), ("", None),
         ("By country group", None)] + [(g, f'=COUNTIF({colr("country_group")},"{g}")') for g in ["TIER1", "TIER2", "BROAD_OECD", "CHINA", "GLOBAL"]] + \
        [("", None), ("By priority class", None)] + [(p, f'=COUNTIF({colr("priority_class")},"{p}")') for p in ["P0", "P1", "P2", "P3"]] + \
        [("", None), ("By inclusion status", None)] + [(s, f'=COUNTIF({colr("inclusion_status")},"{s}")') for s in ["CANDIDATE_CORE", "CANDIDATE_SUPPLEMENTARY", "CANDIDATE_OPTIONAL", "CANDIDATE_CONDITIONAL", "EXCLUDED_BY_DECISION", "NOT_APPLICABLE", "COMPARATOR_ONLY", "SUPPORT_INPUT"]] + \
        [("", None), ("Firewall checks", None),
         ("Rows with beai_eligible = Y", f'=COUNTIF({colr("beai_eligible")},"Y")'),
         ("VIOLATIONS: beai_eligible = Y outside core-coincident subcategory (must be 0)", f'=COUNTIFS({colr("beai_eligible")},"Y",{colr("subcategory")},"<>{CORE_SUB}")'),
         ("VIOLATIONS: core-coincident rows not flagged Y (must be 0)", f'=COUNTIFS({colr("subcategory")},"{CORE_SUB}",{colr("beai_eligible")},"<>Y")'),
         ("VIOLATIONS: unemployment rows flagged BEAI-eligible (must be 0)", f'=COUNTIFS({colr("indicator_id")},"LAB_UNEMP",{colr("beai_eligible")},"Y")'),
         ("VIOLATIONS: major predictors (P0/P1) without a committed sign (must be 0)", f'=COUNTIFS({colr("major_predictor_for_sign_check")},"Y",{colr("sign_commitment")},"NOT_COMMITTED*")'),
         ("", None), ("Verification status", None),
         ("Rows with recalled (unverified) series ID", f'=COUNTIF({colr("id_status")},"ID_RECALLED_NOT_VERIFIED")'),
         ("Rows with a verified available_start_date (expected 0 until audit)", f'=COUNTA({colr("available_start_date")})-COUNTIF({colr("available_start_date")},"PENDING_VERIFICATION")'),
         ("Rows with a verified missingness_pct (expected 0 until audit)", f'=COUNTA({colr("missingness_pct")})-COUNTIF({colr("missingness_pct")},"PENDING_VERIFICATION")'),
         ("", None), ("Indicators", None),
         ("Indicator definitions", "=COUNTA(Indicator_Dictionary!A2:A200)"),
         ("Predictor-eligible indicators (excl. support/comparator)", '=COUNTIF(Indicator_Dictionary!F2:F200,"PREDICTOR_ONLY")+COUNTIF(Indicator_Dictionary!F2:F200,"LABEL_AND_PREDICTOR_SEPARATE")'),
         ("Decisions logged", "=COUNTA(Decisions_Log!A2:A200)"),
         ("Items not yet fully DECIDED (Unresolved_Questions)", '=COUNTA(Decisions_Log!A2:A200)-COUNTIF(Decisions_Log!H2:H200,"DECIDED")'),
         ("Deviations: INTERPRETATION", '=COUNTIF(Decisions_Log!F2:F200,"INTERPRETATION")'),
         ("Deviations: EXTENSION", '=COUNTIF(Decisions_Log!F2:F200,"EXTENSION")')]
for i, (a, b) in enumerate(items, 3):
    sm.cell(row=i, column=1, value=a).font = Font(name=F, bold=(b is None and a != ""), size=10)
    if b is not None:
        c = sm.cell(row=i, column=2, value=b); c.font = BF
sm.column_dimensions["A"].width = 80; sm.column_dimensions["B"].width = 14
wb._sheets = [wb[n] for n in ["README", "Summary", "Series_Catalogue", "Indicator_Dictionary", "Country_Source_Rules", "Source_Registry", "Collection_Priority", "Collection_Batches",
                              "Priority_Indicators", "Label_Firewall", "Label_References", "Schema", "Controlled_Vocab", "Decisions_Log", "Unresolved_Questions", "Verification_Log"]]
wb.save(str(OUT / "recession_ews_data_dictionary.xlsx"))
print("rows", len(rows), "cols", len(COLS))
from collections import Counter
print(Counter(r["country_group"] for r in rows)); print(Counter(r["priority_class"] for r in rows)); print(Counter(r["inclusion_status"] for r in rows)); print(Counter(r["collection_batch"] for r in rows))
print("recalled IDs:", sum(r["id_status"] == "ID_RECALLED_NOT_VERIFIED" for r in rows))

import shutil
os.makedirs(OUT / "src", exist_ok=True)
shutil.copy(PROJECT / "spec.py", OUT / "src" / "spec.py"); shutil.copy(PROJECT / "build.py", OUT / "src" / "build.py")
