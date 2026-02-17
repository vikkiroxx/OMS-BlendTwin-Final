# Multi-Models Plot Data Query

## Overview

The "Multi-models Data for Plots" view combines data from four tables:
- **bts_SimulatedStreamQuality** – Stream quality (ron, etc.) per stream per cycle
- **bts_TQTSCSTRModel** – Tank quality from CSTR model
- **bts_TQTSLaggedModel** – Tank quality from Lagged model  
- **bts_TQTSHybridModel** – Tank quality from Hybrid model

Output columns: `id`, `RefID`, `blendid`, `cycleno`, `TimeStamp`, `TankNo`, `Stream`, `Quality`, `Stream Quality`, `CSTRModel`, `LaggedModel`, `HybridModel`, `Tank Volume`, `Inflow`, `Outflow`.

---

## Parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| `:blendid` | Blend identifier | `20200617-005` |
| `:tankno` | Tank identifier | `TK-3052` |
| `:stream` | Stream name (must exist in model tables for this tank) | `heavy_hydrotreated_naphtha` or `alkylate` |

**Note:** The `stream` parameter must match a stream that has model data for the given tank. Use the helper query below to find valid combinations.

---

## Main Query

```sql
SELECT
    ROW_NUMBER() OVER (ORDER BY cstr.cycleno) AS id,
    cstr.refid AS RefID,
    cstr.blendid,
    cstr.cycleno,
    cstr.timestamp AS TimeStamp,
    cstr.tankno AS TankNo,
    cstr.stream AS Stream,
    'ron' AS Quality,
    ssq.ron AS `Stream Quality`,
    cstr.ron AS CSTRModel,
    lagged.ron AS LaggedModel,
    hyb.ron AS HybridModel,
    cstr.tankvol AS `Tank Volume`,
    CAST(NULLIF(TRIM(cstr.streamin), '') AS DECIMAL(15,2)) AS Inflow,
    CAST(NULLIF(TRIM(cstr.blendout), '') AS DECIMAL(15,2)) AS Outflow
FROM bts_TQTSCSTRModel cstr
LEFT JOIN bts_SimulatedStreamQuality ssq
    ON cstr.blendid = ssq.blendid
    AND cstr.cycleno = ssq.cycleno
    AND cstr.stream = ssq.stream
LEFT JOIN bts_TQTSLaggedModel lagged
    ON cstr.blendid = lagged.blendid
    AND cstr.cycleno = lagged.cycleno
    AND cstr.tankno = lagged.tankno
    AND cstr.stream = lagged.stream
LEFT JOIN bts_TQTSHybridModel hyb
    ON cstr.blendid = hyb.blendid
    AND cstr.cycleno = hyb.cycleno
    AND cstr.tankno = hyb.tankno
    AND cstr.stream = hyb.stream
WHERE cstr.blendid = :blendid
  AND cstr.tankno = :tankno
  AND cstr.stream = :stream
ORDER BY cstr.cycleno;
```

---

## Variant: Stream Quality from Different Stream

If you want to show **stream quality** from one stream (e.g. `alkylate`) while using **tank/model data** from another (e.g. tank’s actual stream), use `:stream_quality` for the quality source:

```sql
SELECT
    ROW_NUMBER() OVER (ORDER BY cstr.cycleno) AS id,
    cstr.refid AS RefID,
    cstr.blendid,
    cstr.cycleno,
    cstr.timestamp AS TimeStamp,
    cstr.tankno AS TankNo,
    :stream_quality AS Stream,
    'ron' AS Quality,
    ssq.ron AS `Stream Quality`,
    cstr.ron AS CSTRModel,
    lagged.ron AS LaggedModel,
    hyb.ron AS HybridModel,
    cstr.tankvol AS `Tank Volume`,
    CAST(NULLIF(TRIM(cstr.streamin), '') AS DECIMAL(15,2)) AS Inflow,
    CAST(NULLIF(TRIM(cstr.blendout), '') AS DECIMAL(15,2)) AS Outflow
FROM bts_TQTSCSTRModel cstr
LEFT JOIN bts_SimulatedStreamQuality ssq
    ON cstr.blendid = ssq.blendid
    AND cstr.cycleno = ssq.cycleno
    AND ssq.stream = :stream_quality
LEFT JOIN bts_TQTSLaggedModel lagged
    ON cstr.blendid = lagged.blendid
    AND cstr.cycleno = lagged.cycleno
    AND cstr.tankno = lagged.tankno
    AND cstr.stream = lagged.stream
LEFT JOIN bts_TQTSHybridModel hyb
    ON cstr.blendid = hyb.blendid
    AND cstr.cycleno = hyb.cycleno
    AND cstr.tankno = hyb.tankno
    AND cstr.stream = hyb.stream
WHERE cstr.blendid = :blendid
  AND cstr.tankno = :tankno
  AND cstr.stream = :stream
ORDER BY cstr.cycleno;
```

---

## Helper: Valid Tank + Stream Combinations

```sql
SELECT DISTINCT blendid, tankno, stream
FROM bts_TQTSCSTRModel
WHERE blendid = :blendid
ORDER BY tankno, stream;
```

---

## Example Parameter Values

| blendid | tankno | stream |
|---------|--------|--------|
| 20200617-005 | TK-3052 | heavy_hydrotreated_naphtha |
| 20200617-005 | TK-3051 | alkylate |

---

## Troubleshooting: No Data Returned

1. **Parameters not filled** – Ensure BlendID, tankno, and stream are filled before Execute. The UI now auto-shows parameter inputs when SQL has `:param` placeholders.
2. **Wrong stream for tank** – For TK-3052 use `heavy_hydrotreated_naphtha` (not `alkylate`). For TK-3051 use `alkylate`.
3. **Typo in column name** – Use `cstr.blendout` (not `blenout`) for the Outflow column.

---

## Column Mapping

| Output Column | Source |
|--------------|--------|
| id | Row number |
| RefID | cstr.refid |
| blendid | cstr.blendid |
| cycleno | cstr.cycleno |
| TimeStamp | cstr.timestamp |
| TankNo | cstr.tankno |
| Stream | cstr.stream |
| Quality | Fixed `'ron'` (can extend for mon, rvp, etc.) |
| Stream Quality | ssq.ron |
| CSTRModel | cstr.ron |
| LaggedModel | lagged.ron |
| HybridModel | hyb.ron |
| Tank Volume | cstr.tankvol |
| Inflow | cstr.streamin (cast to numeric) |
| Outflow | cstr.blendout (cast to numeric) |
