-- Curated reporting views consumed by Power BI (paper Sec. IV-A/VI).
-- These expose only reporting-ready fields and pre-join master + computed data.

CREATE OR REPLACE VIEW v_activity_current AS
SELECT
    a.project_id,
    a.activity_id,
    a.name            AS activity_name,
    a.wbs_code,
    a.trade_category,
    a.is_critical,
    a.total_float_days,
    a.budget,
    k.as_of,
    k.pv, k.ev, k.ac,
    k.cv, k.sv, k.cpi, k.spi, k.eac, k.teac,
    r.delay_probability,
    r.risk_category,
    r.top_features,
    r.model_version
FROM activity a
LEFT JOIN LATERAL (
    SELECT * FROM kpi_result k
    WHERE k.activity_id = a.activity_id
    ORDER BY k.as_of DESC LIMIT 1
) k ON TRUE
LEFT JOIN LATERAL (
    SELECT * FROM risk_result rr
    WHERE rr.activity_id = a.activity_id
    ORDER BY rr.as_of DESC LIMIT 1
) r ON TRUE;

CREATE OR REPLACE VIEW v_project_summary AS
SELECT
    p.project_id,
    p.name            AS project_name,
    p.contractor,
    p.budget_at_completion,
    COUNT(a.activity_id)                          AS activity_count,
    SUM(k.ev)                                     AS total_ev,
    SUM(k.ac)                                     AS total_ac,
    SUM(k.pv)                                     AS total_pv,
    CASE WHEN SUM(k.ac) > 0 THEN SUM(k.ev) / SUM(k.ac) END      AS cpi,
    CASE WHEN SUM(k.pv) > 0 THEN SUM(k.ev) / SUM(k.pv) END      AS spi,
    COUNT(*) FILTER (WHERE r.risk_category = 'High')            AS high_risk_count,
    AVG(r.delay_probability)                      AS avg_delay_probability
FROM project p
LEFT JOIN activity a ON a.project_id = p.project_id
LEFT JOIN kpi_result k ON k.activity_id = a.activity_id
LEFT JOIN risk_result r ON r.activity_id = a.activity_id
GROUP BY p.project_id, p.name, p.contractor, p.budget_at_completion;

CREATE OR REPLACE VIEW v_progress_trend AS
SELECT
    pu.activity_id,
    a.project_id,
    pu.timestamp,
    pu.percent_complete,
    pu.earned_value,
    pu.planned_value
FROM progress_update pu
JOIN activity a ON a.activity_id = pu.activity_id;

CREATE OR REPLACE VIEW v_cost_trend AS
SELECT
    cr.activity_id,
    a.project_id,
    cr.timestamp,
    cr.actual_cost,
    SUM(cr.actual_cost) OVER (
        PARTITION BY cr.activity_id ORDER BY cr.timestamp
    ) AS cumulative_actual_cost
FROM cost_record cr
JOIN activity a ON a.activity_id = cr.activity_id;
