import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
from typing import Any

import alice_predictor as model


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding='utf-8'))


def read_events(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]


def verify(root: Path) -> dict[str, Any]:
    manifest = read_json(root / 'manifest.json')
    for name, expected in manifest['sha256'].items():
        relative = Path(name)
        if relative.is_absolute() or '..' in relative.parts:
            raise ValueError(f'unsafe evidence path: {name}')
        actual = hashlib.sha256((root / relative).read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError(f'evidence digest mismatch: {name}')
    forecast = read_json(root / 'lab-forecast.json')
    events = read_events(root / 'lab-observations.jsonl')
    published = datetime.fromisoformat(forecast['created_utc'])
    state = int(forecast['anchor']['state_after'])
    banks = [[str(index) for index in range(size)] for size in (1098, 1053)]
    matches: list[dict[str, Any]] = []
    unobserved: list[str] = []
    for prediction in forecast['predictions']:
        generated = model.next_response(state, banks)
        for generated_key, recorded_key in [('index', 'index'), ('bank', 'bank'),
                                             ('state_before', 'state_before'),
                                             ('state_after', 'state_after_shuffle')]:
            if generated[generated_key] != prediction[recorded_key]:
                raise ValueError(f'model disagrees with saved forecast at word {prediction["number"]}: {recorded_key}')
        state = int(generated['state_after'])
        observed = [event for event in events if event['event'] == 'native_choice'
                    and event['actual_word'] == prediction['word']
                    and event['state_after'] == prediction['state_after_shuffle']]
        if not observed:
            unobserved.append(prediction['word'])
            continue
        if len(observed) != 1:
            raise ValueError('ambiguous native observation')
        selected = observed[0]
        lead = (datetime.fromisoformat(selected['utc']) - published).total_seconds()
        if lead <= 0 or selected['actual_index'] != prediction['index'] or not selected['match']:
            raise ValueError('forecast was not an advance match')
        matches.append({'word': selected['actual_word'], 'lead_seconds': round(lead, 3)})
    expected = manifest['expected_lab_future_words']
    if [row['word'] for row in matches] != expected:
        raise ValueError('observed future words differ from the evidence manifest')
    choices = [event for event in events if event['event'] == 'native_choice']
    if any(event['negative_control_match'] for event in choices):
        raise ValueError('wrong-state control unexpectedly matched')
    normal = read_events(root / 'normal-observations.jsonl')
    normal_forecast = read_json(root / 'normal-forecast.json')
    normal_time = datetime.fromisoformat(normal_forecast['created_utc'])
    normal_choices = [event for event in normal if event['event'] == 'native_choice']
    if len(normal_choices) != 1 or normal_choices[0]['actual_word'] != 'PILLOW':
        raise ValueError('normal-startup observation differs from the recorded result')
    if datetime.fromisoformat(normal_choices[0]['utc']) >= normal_time:
        raise ValueError('normal first word was unexpectedly an advance forecast')
    return {'model_version': model.__version__, 'lab_advance_matches': len(matches),
            'lab_words': matches, 'lab_unobserved_predictions': unobserved,
            'native_state_snapshot_checks': len(choices),
            'wrong_state_controls_rejected': len(choices),
            'normal_startup_observed_words': ['PILLOW'], 'normal_startup_advance_matches': 0,
            'bound': 'checks recorded artifacts and model consistency; does not independently attest timestamps or rerun alice'}


def main() -> None:
    parser = argparse.ArgumentParser(description='verify the bundled prediction evidence without alice or its word banks')
    parser.add_argument('--evidence-dir', type=Path, default=Path(__file__).parent / 'evidence')
    args = parser.parse_args()
    print(json.dumps(verify(args.evidence_dir), indent=2))


if __name__ == '__main__':
    main()
