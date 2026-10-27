# alice-predictor

an experimental python model of the windows alice ghost-hunting app's word selector.

**four future words matched a fixed forecast saved about 3–5 minutes before selection, in a modified local test copy. prediction through normal startup remains unverified.**

the matched words were `ALREADY → INTENT → READ → CLOTHES`. each selected index and post-shuffle generator state also matched. [the evidence](evidence/README.md) records the setup changes and the incomplete normal-startup experiment.

this is a research prototype. it is not a verified predictor for arbitrary alice installations or spirit bridge hardware.

## check the result

use python 3.10 or newer. no third-party packages, alice executable, or word banks are required to check the bundled evidence.

```sh
python verify_evidence.py
python -m unittest discover -s tests -v
```

the verifier reports four advance matches in the modified run and zero advance matches in the interrupted normal-startup run. it checks recorded artifacts against the model; it does not independently authenticate their timestamps or run alice.

## reproduce the saved forecast

supply your own local `words.txt` and `words1.txt` from the examined alice download. the full word banks are not distributed here. their order and contents affect the predictions.

the original download was linked from [the developer's site](https://www.alicebox.co.uk/itc/) and [infraready's software page](https://www.infraready.co.uk/shop/alice-box-instrumental-trans-communication-licesnse-key-free-download/).

with those files in `local/alice/`, run:

```sh
python alice_predictor.py --bank-dir local/alice --launch 2026-10-27T06:10:05.772573+00:00 --window 5 --observed FILTER LEMON CHART --count 8
```

this searches 11 candidate seconds around the recorded launch time, using the three observed words. the expected result is one matching seed, `1793081406`, followed by:

```text
GREAT ALREADY INTENT READ CLOTHES NOISE FOOT TRIED
```

`GREAT`, `NOISE`, `FOOT`, and `TRIED` were not directly observed in the recorded verification window. they are predictions, not additional successes.

the initial model was developed using process-state observations. later seed recovery uses only the supplied time window, word prefix, and local word banks. this example reproduces the recorded experiment; it does not establish the correct startup assumptions for another run.

## other inputs

use a known startup seed:

```sh
python alice_predictor.py --bank-dir local/alice --seed 1793081406 --count 8
```

use a known generator state immediately after a completed word shuffle:

```sh
python alice_predictor.py --bank-dir local/alice --state 4199959400 --count 8
```

add `--output forecast.json` to save the result. `--version` prints the model version. a seed search with no matching word prefix exits with status 2 and reports zero candidates.

## mechanism and limits

the examined binary contains a conventional c-style pseudorandom generator:

```text
state = (214013 * state + 2531011) modulo 2**32
value = (state >> 16) & 32767
```

the recovered response path tests random-number thresholds, chooses one of two word banks, then shuffles that bank. the model accounts for the quick-repeat branch and the random draws consumed by each shuffle.

the seed mode assumes three initial discarded draws, as calibrated in the modified experiment. a different startup path can change seed timing or draw consumption. the same initial seed alone does not establish identical output across different execution paths.

the model raises an error when a shuffle draw scales to an index outside the supplied bank. that edge behavior has not been modeled or validated against a live output.

the examined `alice.exe` has sha256 `157ab8369957fccb70d03b18c2f18ce330047441829c8d899daa711068376041`; its archive entry is dated 2020-08-31. other downloads and hardware versions can behave differently.

this repository contains our predictor and research records. it contains no alice executable, full word banks, activation keys, keygen, or registration-bypass patch. it is an independent project and does not establish or refute claims about every paranormal device.

## license

our original code and documentation are available under the [MIT license](LICENSE). alice and its assets are not licensed by this repository.
