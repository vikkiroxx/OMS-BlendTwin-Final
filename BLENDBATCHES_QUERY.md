# BlendBatches Query – Excel Data Source

## Summary

The **BlendBatches** Excel sheet data comes from the **`bts_BlendBatches`** table, not from the quality tables (`bts_SimulatedStreamQuality`, `bts_TQTSCSTRModel`, etc.). Those quality tables store per-cycle data (many rows per blend), while the Excel has one row per blend batch.

---

## Column Mapping (Excel → Database)

| Excel Column    | DB Column         | Notes                          |
|-----------------|-------------------|--------------------------------|
| ID              | `id`              |                                |
| RefID           | `refid`           |                                |
| BlendNo         | `no`              |                                |
| BlendID         | `blend_id`        |                                |
| Grade           | `grade`           |                                |
| BlendStartTime  | `blendstarttime`  |                                |
| BlendEndTime    | `blendendtime`    |                                |
| Destination     | `destination`     | Tank ID (e.g. TK-3053)         |
| LoadSize        | `load_size`       |                                |
| HeelVolume      | `heel_volume`     |                                |
| TankCapacity    | `tank_capcity_bl` | Note: typo in DB (capcity)     |
| Duration        | `blend_duration`  |                                |
| Productprice    | `product_price_$` |                                |
| nComps          | `ncomps`          |                                |
| Optimizable     | `optimizable`     |                                |
| ForAIModel      | `for_ai_model`    |                                |
| nCycles         | `5_mins_ncycles`  |                                |

---

## SQL Query – BlendBatches (matches Excel)

```sql
SELECT
    id AS ID,
    refid AS RefID,
    no AS BlendNo,
    blend_id AS BlendID,
    grade AS Grade,
    blendstarttime AS BlendStartTime,
    blendendtime AS BlendEndTime,
    destination AS Destination,
    load_size AS LoadSize,
    heel_volume AS HeelVolume,
    tank_capcity_bl AS TankCapacity,
    blend_duration AS Duration,
    `product_price_$` AS Productprice,
    ncomps AS nComps,
    optimizable AS Optimizable,
    for_ai_model AS ForAIModel,
    `5_mins_ncycles` AS nCycles
FROM bts_BlendBatches
ORDER BY id;
```

### Optional filters

```sql
-- Filter by RefID (e.g. blendtwin)
WHERE refid = 'blendtwin'

-- Filter by BlendID
WHERE blend_id = '20200617-005'

-- Filter by date range (if blendstarttime is datetime)
WHERE blendstarttime >= '2020-06-01' AND blendstarttime < '2020-07-01'
```

---

## Quality Tables vs BlendBatches

The quality tables contain **per-cycle** data (one row per 5‑minute blend cycle):

- `bts_SimulatedStreamQuality` – stream quality (ron, mon, etc.) per cycle
- `bts_TQTSCSTRModel` – tank quality from CSTR model per cycle
- `bts_TQTSHybridModel` – tank quality from hybrid model per cycle
- `bts_TQTSLaggedModel` – tank quality from lagged model per cycle

They are linked to blends via `blendid` but have many rows per blend. They are not the source of the BlendBatches Excel layout (one row per blend).

---

## Trend Query Workbench Usage

1. Create a new trend with the SQL above.
2. Use parameter `:blendid` if you want to filter by BlendID.
3. Execute and export or plot as needed.
