# Where the expected values come from

Every expected number in `food.jsonl` was read from one of the files below. The files are
not committed (they live in the git-ignored `data/raw/`); the checksums let Stage 5 confirm
it ingests the same bytes, and re-verify every expected value against them.

## USDA FoodData Central, SR Legacy (amino acids, F8)

| | |
|---|---|
| Release | SR Legacy, April 2018 (FoodData Central CSV export) |
| Official URL | `https://fdc.nal.usda.gov/fdc-datasets/FoodData_Central_sr_legacy_food_csv_2018-04.zip` |
| Retrieved from | Wayback Machine capture `20260807022403` of the official URL (2026-10-30): `*.usda.gov` does not resolve from the development machine |
| SHA-256 | `b80817294b8850530aaedf2e515c02593b1824f763a0ff356e5c2081643e6fd0` |
| Values | `food_nutrient.csv`, column `amount`, per 100 g; `food_code` = `fdc_id` |
| Licence | public domain (US government work) |

**Integrity check.** No published checksum was reachable, so the capture was compared with
an independent one: the JSON export `FoodData_Central_sr_legacy_food_json_2021-10-28.zip`
(Wayback capture `20211206014741`, SHA-256
`789240d42d51640b931782310403c415eb4aa03383d8f0a52f6315db80f96bc7`). Both hold the same
644,125 (food, nutrient) values. 68,860 differ only because the JSON rounds to 3 significant
figures (at most 3 decimals). One value disagrees outright: manganese in raw chickpeas
(fdc_id 173756, nutrient 1101), 4.15 mg in the CSV against 21.3 mg in the JSON. No golden
item uses it.

## ANSES-CIQUAL (composition, F7)

Pending: `ciqual.anses.fr` answered 503 on 2026-10-30.
