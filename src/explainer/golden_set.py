from typing import List, Dict, Any

def get_golden_set() -> List[Dict[str, Any]]:
    """
    Returns a curated benchmark suite of 32 real-world retail forecasting incidents.
    Used to benchmark LLM explanation accuracy, metric citations, latency, and token cost.
    """
    cases: List[Dict[str, Any]] = []

    # Category 1: Price Shocks (Cases 1 - 8)
    price_scenarios = [
        ("CASE_001", "Severe Dairy Price Inflation (+45%)", "sell_price", 0.42, 0.0001, 0.32, -0.18, 0.45, "price_elasticity", "overstock"),
        ("CASE_002", "Bakery Promotional Discount Flash Sale (-30%)", "sell_price", 0.28, 0.002, 0.29, -0.22, -0.30, "price_elasticity", "stockout"),
        ("CASE_003", "Store CA_01 Meat Category Luxury Tax (+25%)", "sell_price", 0.24, 0.015, 0.25, 0.14, 0.25, "price_elasticity", "overstock"),
        ("CASE_004", "Beverage Bulk Pack Repricing (+35%)", "sell_price", 0.35, 0.0005, 0.31, 0.19, 0.35, "price_elasticity", "overstock"),
        ("CASE_005", "Snack Food Dollar Store Competitor Price Undercut", "sell_price", 0.26, 0.008, 0.27, 0.16, 0.20, "price_elasticity", "overstock"),
        ("CASE_006", "Produce Organic Line Premium Repositioning (+50%)", "sell_price", 0.48, 0.00001, 0.36, 0.24, 0.50, "price_elasticity", "overstock"),
        ("CASE_007", "Household Paper Goods Supply Cost Surge (+40%)", "sell_price", 0.39, 0.0002, 0.33, 0.17, 0.40, "price_elasticity", "overstock"),
        ("CASE_008", "Personal Care Margin Rebalancing (+22%)", "sell_price", 0.22, 0.021, 0.24, 0.11, 0.22, "price_elasticity", "overstock"),
    ]

    for cid, title, feat, psi, ks_p, wape, bias, delta, root_cause, impact in price_scenarios:
        cases.append({
            "case_id": cid,
            "title": title,
            "incident_type": "PRICE_ELASTICITY_ANOMALY",
            "context": {
                "incident_type": "PRICE_DRIFT_ALERT",
                "metrics": {"wape": wape, "bias": bias, "baseline_wape": 0.18},
                "drift_report": {
                    "max_psi": psi,
                    "features": {feat: {"psi": psi, "ks_p_value": ks_p, "status": "CRITICAL_DRIFT", "baseline_mean": 4.50, "current_mean": round(4.50 * (1 + delta), 2)}}
                },
                "decay_report": {"current_wape": wape, "relative_decay": round((wape - 0.18) / 0.18, 3)}
            },
            "ground_truth_root_cause": root_cause,
            "ground_truth_impact": impact,
            "expected_citations": [str(psi), f"{wape:.2f}", f"{bias:+.2f}"]
        })

    # Category 2: Promotional Surges (Cases 9 - 16)
    promo_scenarios = [
        ("CASE_009", "Unannounced Digital Loyalty Flash Promo (BOGO)", "is_promo", 0.38, 0.0002, 0.35, -0.28, 1.8, "promo_surge", "stockout"),
        ("CASE_010", "National TV Advertising Campaign for SuperBowl", "is_promo", 0.45, 0.00005, 0.40, -0.34, 2.2, "promo_surge", "stockout"),
        ("CASE_011", "Weekend Mobile App Push Notification Blast", "is_promo", 0.31, 0.001, 0.28, -0.19, 1.5, "promo_surge", "stockout"),
        ("CASE_012", "Canceled Summer Cookout Promotion", "is_promo", 0.27, 0.004, 0.26, 0.21, -0.7, "promo_surge", "overstock"),
        ("CASE_013", "Vendor Sponsored Endcap Feature Display", "is_promo", 0.29, 0.003, 0.27, -0.17, 1.4, "promo_surge", "stockout"),
        ("CASE_014", "Holiday Clearance Markdown Surge", "is_promo", 0.41, 0.0001, 0.37, -0.25, 2.0, "promo_surge", "stockout"),
        ("CASE_015", "Back to School Bundle Blitz", "is_promo", 0.33, 0.0008, 0.30, -0.22, 1.6, "promo_surge", "stockout"),
        ("CASE_016", "Black Friday Cyber Week Extravaganza", "is_promo", 0.52, 0.00001, 0.44, -0.38, 2.8, "promo_surge", "stockout"),
    ]

    for cid, title, feat, psi, ks_p, wape, bias, delta, root_cause, impact in promo_scenarios:
        cases.append({
            "case_id": cid,
            "title": title,
            "incident_type": "PROMOTIONAL_SURGE_ALERT",
            "context": {
                "incident_type": "PROMOTION_DRIFT_ALERT",
                "metrics": {"wape": wape, "bias": bias, "baseline_wape": 0.18},
                "drift_report": {
                    "max_psi": psi,
                    "features": {feat: {"psi": psi, "ks_p_value": ks_p, "status": "CRITICAL_DRIFT", "baseline_mean": 0.15, "current_mean": 0.70}}
                },
                "decay_report": {"current_wape": wape, "relative_decay": round((wape - 0.18) / 0.18, 3)}
            },
            "ground_truth_root_cause": root_cause,
            "ground_truth_impact": impact,
            "expected_citations": [str(psi), f"{wape:.2f}", f"{bias:+.2f}"]
        })

    # Category 3: Supply Chain & Concept Drift (Cases 17 - 24)
    concept_scenarios = [
        ("CASE_017", "Upstream Supplier Factory Outage (Stockouts)", "lag_1", 0.36, 0.0004, 0.34, 0.31, -0.6, "concept_drift", "stockout"),
        ("CASE_018", "Substitute SKU Cannibalization in Household", "rolling_mean_7", 0.28, 0.002, 0.28, 0.18, -0.35, "concept_drift", "overstock"),
        ("CASE_019", "Post-COVID Return to Office Food Shift", "rolling_mean_28", 0.33, 0.0009, 0.30, 0.15, -0.25, "concept_drift", "overstock"),
        ("CASE_020", "Abnormal Heat Wave Driving Beverage Run", "lag_1", 0.40, 0.0001, 0.38, -0.32, 1.9, "concept_drift", "stockout"),
        ("CASE_021", "Competitor Store Closure Capturing Foot Traffic", "rolling_mean_7", 0.37, 0.0003, 0.32, -0.26, 1.7, "concept_drift", "stockout"),
        ("CASE_022", "Product Reformulation Customer Backlash", "rolling_mean_14", 0.30, 0.0015, 0.29, 0.22, -0.4, "concept_drift", "overstock"),
        ("CASE_023", "Transit Union Port Strike Logistics Delay", "lag_7", 0.35, 0.0006, 0.31, 0.27, -0.5, "concept_drift", "stockout"),
        ("CASE_024", "Viral Social Media TikTok Trend Surge", "lag_1", 0.55, 0.00001, 0.48, -0.42, 3.2, "concept_drift", "stockout"),
    ]

    for cid, title, feat, psi, ks_p, wape, bias, delta, root_cause, impact in concept_scenarios:
        cases.append({
            "case_id": cid,
            "title": title,
            "incident_type": "CONCEPT_DRIFT_ALERT",
            "context": {
                "incident_type": "STRUCTURAL_DEMAND_SHIFT",
                "metrics": {"wape": wape, "bias": bias, "baseline_wape": 0.18},
                "drift_report": {
                    "max_psi": psi,
                    "features": {feat: {"psi": psi, "ks_p_value": ks_p, "status": "CRITICAL_DRIFT", "baseline_mean": 30.0, "current_mean": round(30.0 * (1 + delta), 2)}}
                },
                "decay_report": {"current_wape": wape, "relative_decay": round((wape - 0.18) / 0.18, 3)}
            },
            "ground_truth_root_cause": root_cause,
            "ground_truth_impact": impact,
            "expected_citations": [str(psi), f"{wape:.2f}", f"{bias:+.2f}"]
        })

    # Category 4: Store / Regional Disruptions (Cases 25 - 32)
    regional_scenarios = [
        ("CASE_025", "Severe Winter Blizzard Regional Closure Store_02", "rolling_mean_7", 0.44, 0.00008, 0.42, 0.38, -0.85, "concept_drift", "overstock"),
        ("CASE_026", "Local College Football Game Day Surge Store_01", "lag_1", 0.32, 0.0012, 0.29, -0.21, 1.6, "concept_drift", "stockout"),
        ("CASE_027", "Store Remodel Phased Aisle Closures Store_03", "rolling_mean_14", 0.25, 0.012, 0.24, 0.16, -0.3, "concept_drift", "overstock"),
        ("CASE_028", "Regional Distribution Hub Automation Glitch", "lag_7", 0.31, 0.002, 0.28, 0.19, -0.4, "concept_drift", "stockout"),
        ("CASE_029", "State Holiday Monday Long Weekend Demand", "lag_1", 0.26, 0.009, 0.25, -0.15, 1.4, "concept_drift", "stockout"),
        ("CASE_030", "Local Construction Road Closure Impeding Store Access", "rolling_mean_7", 0.29, 0.003, 0.27, 0.18, -0.35, "concept_drift", "overstock"),
        ("CASE_031", "New Competitor Supercenter Opening Within 2 Miles", "rolling_mean_28", 0.38, 0.0003, 0.34, 0.25, -0.45, "concept_drift", "overstock"),
        ("CASE_032", "Downtown Marathon Weekend Beverage Boom", "lag_1", 0.36, 0.0005, 0.33, -0.27, 2.1, "concept_drift", "stockout"),
    ]

    for cid, title, feat, psi, ks_p, wape, bias, delta, root_cause, impact in regional_scenarios:
        cases.append({
            "case_id": cid,
            "title": title,
            "incident_type": "REGIONAL_INCIDENT_ALERT",
            "context": {
                "incident_type": "REGIONAL_STORE_SHIFT",
                "metrics": {"wape": wape, "bias": bias, "baseline_wape": 0.18},
                "drift_report": {
                    "max_psi": psi,
                    "features": {feat: {"psi": psi, "ks_p_value": ks_p, "status": "CRITICAL_DRIFT", "baseline_mean": 28.0, "current_mean": round(28.0 * (1 + delta), 2)}}
                },
                "decay_report": {"current_wape": wape, "relative_decay": round((wape - 0.18) / 0.18, 3)}
            },
            "ground_truth_root_cause": root_cause,
            "ground_truth_impact": impact,
            "expected_citations": [str(psi), f"{wape:.2f}", f"{bias:+.2f}"]
        })

    # Category 5: Adversarial & Stress Testing Edge Cases (Cases 33 - 42)
    adversarial_scenarios = [
        ("CASE_033", "Zero Sales Across Complete Category (Sensor Disconnection)", "lag_1", 0.89, 0.0, 1.00, -1.00, -1.0, "data_corruption", "outage"),
        ("CASE_034", "Extreme 10,000x Price Keying Error Glitch", "sell_price", 0.95, 0.0, 0.92, 0.85, 1000.0, "data_corruption", "glitch"),
        ("CASE_035", "Simultaneous Triple-Feature Covariate Drift Collision", "rolling_mean_28", 0.58, 0.00001, 0.44, 0.32, 0.8, "concept_drift", "overstock"),
        ("CASE_036", "Leap Year Temporal Alignment Distortion (Feb 29)", "lag_7", 0.22, 0.015, 0.23, 0.08, 0.1, "temporal_anomaly", "minor_bias"),
        ("CASE_037", "Sudden 100% SKU Delisting (Discontinued Line)", "lag_1", 0.72, 0.0, 0.85, -0.80, -1.0, "concept_drift", "stockout"),
        ("CASE_038", "Flash Midnight Database Replication Desynchronization", "rolling_mean_7", 0.41, 0.0002, 0.38, 0.29, -0.4, "data_corruption", "outage"),
        ("CASE_039", "Sudden Government Price Cap Imposition", "sell_price", 0.37, 0.0004, 0.33, -0.25, -0.35, "price_elasticity", "stockout"),
        ("CASE_040", "Omnichannel Inventory Allocation Phantom Reservation", "lag_1", 0.39, 0.0003, 0.35, 0.22, -0.3, "data_corruption", "overstock"),
        ("CASE_041", "Unprecedented 100-Year Flood Physical Distribution Severance", "rolling_mean_14", 0.65, 0.0, 0.52, 0.45, -0.9, "concept_drift", "outage"),
        ("CASE_042", "High-Frequency Automated Algorithmic Arbitrage Bot Run", "is_promo", 0.62, 0.0, 0.50, -0.45, 3.5, "promo_surge", "stockout"),
    ]

    for cid, title, feat, psi, ks_p, wape, bias, delta, root_cause, impact in adversarial_scenarios:
        cases.append({
            "case_id": cid,
            "title": title,
            "incident_type": "ADVERSARIAL_EDGE_CASE",
            "context": {
                "incident_type": "ADVERSARIAL_ANOMALY",
                "metrics": {"wape": wape, "bias": bias, "baseline_wape": 0.18},
                "drift_report": {
                    "max_psi": psi,
                    "features": {feat: {"psi": psi, "ks_p_value": ks_p, "status": "CRITICAL_DRIFT", "baseline_mean": 25.0, "current_mean": round(max(0.1, 25.0 * (1 + delta)), 2)}}
                },
                "decay_report": {"current_wape": wape, "relative_decay": round((wape - 0.18) / 0.18, 3)}
            },
            "ground_truth_root_cause": root_cause,
            "ground_truth_impact": impact,
            "expected_citations": [str(psi), f"{wape:.2f}", f"{bias:+.2f}"]
        })

    return cases
