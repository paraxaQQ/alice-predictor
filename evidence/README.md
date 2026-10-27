# recorded experiments

## modified test copy: four advance matches

the fixed forecast in `lab-forecast.json` was saved at **2026-10-27 06:13:04.633135 utc**. it was generated once from the known state after `CHART`. later process snapshots were used to verify observations, not to revise that batch.

| forecast | native selection, utc | advance notice |
| --- | --- | --- |
| ALREADY | 06:16:03.259953 | 178.627 seconds |
| INTENT | 06:17:23.999485 | 259.366 seconds |
| READ | 06:17:38.748639 | 274.116 seconds |
| CLOTHES | 06:18:23.494631 | 318.861 seconds |

each word, selected index, and post-shuffle state matched the saved forecast. the native events are in `lab-observations.jsonl`.

the earlier words `FILTER`, `LEMON`, and `CHART` were calibration data. `GREAT` was predicted but not directly observed while the debugger was detached. `NOISE`, `FOOT`, and `TRIED` were not observed before the experiment ended. none is counted as an advance success.

the test copy was unpacked and modified to bypass registration, skip introductory navigation, start automatically, and avoid an optional directplay probe. it ran with a windows 7 compatibility override. the six selection scripts and the checked native generator, random-number handler, parser constructor, and shuffle functions remained byte-for-byte unchanged. that does not prove equivalent startup behavior.

an earlier debugger implementation mishandled wow64 breakpoints and caused a crash. that attempt contributed no successful predictions.

## normal startup: interrupted, no advance matches

the next experiment restored the original packed executable and assets. one byte in a registration condition remained changed. the normal navigation and power switch were used without a compatibility override.

the app selected `PILLOW` at **06:56:47.076422 utc**. its index and state matched the observer's immediate calculation. the separate fixed batch was saved later, at **06:57:30.341489 utc**, so `PILLOW` is not counted as an advance batch prediction.

the pending batch began `DAVID → CELLAR → HILL`. the user closed the sluggish app at **07:00:25.452233 utc**, before those predictions could be verified. the experiment was then stopped. `normal-forecast.json` and `normal-observations.jsonl` preserve that incomplete result.

## what verification establishes

`python verify_evidence.py` recomputes the saved forecast's index and state progression using synthetic index-only banks with the recorded lengths, then compares the recorded word labels, indexes, states, and timestamps. the full proprietary dictionaries are not required for this check.

the sha256 manifest detects changes to the bundled records. it is not independent timestamp attestation. reproducing the model's arithmetic and checking these records is distinct from reproducing a live alice run.
