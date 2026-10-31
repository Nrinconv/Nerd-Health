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

Foods used: 168928 pasta (cooked, unenriched, no salt), 173756 chickpeas (raw), 173904 oats
(regular, dry), 172470 peanut butter (smooth, no salt), 170287 bulgur (cooked), 172421
lentils (boiled, no salt).

## FAO/WHO 2013 amino acid scoring pattern (F8)

| | |
|---|---|
| Document | *Dietary protein quality evaluation in human nutrition*, FAO Food and Nutrition Paper 92 (2013), Table 5 |
| URL | `https://www.fao.org/ag/humannutrition/35978-02317b979a686a57aa4593304ffc17f06.pdf` (2026-10-30) |
| SHA-256 | `e0946df2595c6def535f2f1ca7d906b00fd8402e7bfc25cd37f71fb615aa1bb3` |
| Pattern used | older child, adolescent, adult (mg/g protein): His 16, Ile 30, Leu 61, Lys 48, SAA 23, AAA 41, Thr 25, Trp 6.6, Val 40 |

**Amino acid score** of a combination: for each of the nine (SAA = Met + Cys, AAA = Phe + Tyr),
mg per g of protein in the mix divided by the pattern value; the score is the smallest ratio,
**not truncated at 1** (the FAO report's own examples print values such as "143 (SAA)"),
rounded to 2 decimals, half up. The limiting amino acid is the one with the smallest ratio.
A score of 1 or more means no amino acid falls below the reference. Not DIAAS: no
digestibility data.

## ANSES-CIQUAL 2020 (composition, F7)

| | |
|---|---|
| Release | CIQUAL 2020, English Excel table (saved by ANSES 2020-07-03) |
| Official URL | `https://ciqual.anses.fr/cms/sites/default/files/inline-files/Table%20Ciqual%202020_ENG_2020%2007%2007.xls` (listed on data.gouv.fr) |
| Retrieved from | Wayback Machine capture `20210507222941` of the official URL (2026-10-30): `ciqual.anses.fr` answered 503 |
| SHA-256 | `5551841f12f40fb6c869f80aa14e9db33bcfb7dcc135f000cb994a2cca4dc2f5` |
| Values | sheet `compo`, the cell as printed (decimal comma read as a point); `food_code` = `alim_code` |
| Licence | Etalab Open Licence |

**Integrity check.** A second, independent capture (`20260223153128`) has the same SHA-256.
A capture from `20210921110017` is truncated at 1 MiB and was discarded. The French edition
(`..._FR_2020 07 07.xls`, capture `20260223153125`, SHA-256
`a728c29d8d3c944aa679d62d7a2e591c80bac512059ea6772af95760f65da75d`) was used only to match
French food names, since the English names are translations: "fromage blanc nature, 0% MG"
is "Fresh cream cheese, plain, fat free" (19644).

**Missing values.** CIQUAL writes `-` for no value, and `0` for a real zero. The `not_in_data`
items that name a missing value point at a `-` cell. Skyr, whey powder and arepa are not in
the table at all, and there is no creatine column.
