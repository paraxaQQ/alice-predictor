import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

__version__ = '0.1.0'

def advance(state: int) -> tuple[int, int]:
    state = (214013 * state + 2531011) & 0xFFFFFFFF
    return state, (state >> 16) & 32767


def rnd(state: int, maximum: int) -> tuple[int, int]:
    state, raw = advance(state)
    return state, int(raw * 3.0518509447574615e-05 * maximum + 0.5)


def shuffled_first(state: int, bank: list[str], number: int) -> dict[str, object]:
    if not bank:
        raise ValueError('word bank is empty')
    following, raw = advance(state)
    index = int(raw * (1 / 32767) * len(bank))
    if index >= len(bank):
        raise ValueError('native shuffle endpoint is outside the word bank')
    final = following
    for _ in range(len(bank) - 1):
        final, _ = advance(final)
    return {'word': bank[index], 'bank': number, 'index': index,
            'bank_size': len(bank), 'state_before': state, 'state_after': final}


def response(state: int, banks: list[list[str]]) -> dict[str, object]:
    for checks in range(1, 100001):
        state, event = rnd(state, 50)
        if event > 47:
            break
    else:
        raise RuntimeError('no response trigger within 100000 checks')
    state, dice = rnd(state, 10)
    bank = 0 if dice > 5 else 1
    result = shuffled_first(state, banks[bank], bank)
    result['random_checks'] = checks
    return result


def next_response(state: int, banks: list[list[str]]) -> dict[str, object]:
    state, repeat = rnd(state, 10)
    if repeat > 7:
        result = shuffled_first(state, banks[0], 0)
        result['random_checks'] = 0
    else:
        result = response(state, banks)
    result['repeat_draw'] = repeat
    return result


def sequence(seed: int, banks: list[list[str]], count: int) -> list[dict[str, object]]:
    if count < 1:
        raise ValueError('count must be positive')
    state = seed & 0xFFFFFFFF
    for _ in range(3):
        state, _ = advance(state)
    result = [response(state, banks)]
    for _ in range(count - 1):
        result.append(next_response(int(result[-1]['state_after']), banks))
    return result


def recover(launch_second: int, window: int, observed: list[str], banks: list[list[str]], count: int) -> list[dict[str, object]]:
    if not observed:
        raise ValueError('seed recovery requires observed words')
    if not 0 <= window <= 3600:
        raise ValueError('window must be between 0 and 3600 seconds')
    matches: list[dict[str, object]] = []
    expected = [word.casefold() for word in observed]
    for seed in range(launch_second - window, launch_second + window + 1):
        candidates = sequence(seed, banks, len(observed) + count)
        if [str(row['word']).casefold() for row in candidates[:len(observed)]] == expected:
            matches.append({'seed': seed, 'seed_utc': datetime.fromtimestamp(seed, timezone.utc).isoformat(),
                            'predictions': candidates[len(observed):]})
    return matches


def main() -> None:
    parser = argparse.ArgumentParser(description='experimental alice windows selector model; normal-startup prediction is not yet validated')
    parser.add_argument('--version', action='version', version=__version__)
    parser.add_argument('--bank-dir', type=Path, required=True, help='folder containing locally supplied words.txt and words1.txt')
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--seed', type=lambda value: int(value, 0), help='startup clock seed in unix seconds')
    source.add_argument('--launch', help='approximate startup time in ISO 8601, including timezone offset')
    source.add_argument('--state', type=lambda value: int(value, 0), help='known generator state immediately after a word shuffle')
    parser.add_argument('--observed', nargs='+', default=[])
    parser.add_argument('--window', type=int, default=5, help='seconds on either side of --launch to search')
    parser.add_argument('--count', type=int, default=8)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if not 1 <= args.count <= 1000:
        parser.error('--count must be between 1 and 1000')
    banks = [(args.bank_dir / name).read_text(encoding='cp1252').splitlines()
             for name in ['words.txt', 'words1.txt']]
    if any(not bank for bank in banks):
        parser.error('both word banks must contain entries')
    if args.launch:
        launch = datetime.fromisoformat(args.launch.replace('Z', '+00:00'))
        if launch.tzinfo is None:
            parser.error('--launch must include a timezone offset')
        matches = recover(int(launch.timestamp()), args.window, args.observed, banks, args.count)
    elif args.seed is not None:
        matches = [{'seed': args.seed, 'predictions': sequence(args.seed, banks, args.count)}]
    else:
        state = args.state
        predictions = []
        for _ in range(args.count):
            prediction = next_response(state, banks)
            predictions.append(prediction)
            state = int(prediction['state_after'])
        matches = [{'anchor_state': args.state, 'predictions': predictions}]
    result = {'created_utc': datetime.now(timezone.utc).isoformat(), 'matching_candidate_count': len(matches),
              'observed_words': args.observed, 'matches': matches,
              'bound': 'research prototype validated in a modified test copy; normal-startup prediction remains unverified; fixed word banks and startup assumptions'}
    encoded = json.dumps(result, indent=2) + '\n'
    if args.output:
        args.output.write_text(encoded, encoding='utf-8')
    print(encoded, end='')
    if not matches:
        raise SystemExit(2)


if __name__ == '__main__':
    main()
