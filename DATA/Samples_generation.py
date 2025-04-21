import json
import re
import random
import os

def load_samples(path):
    """Load the list of dicts from a JSONL file."""
    samples = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            samples.append(json.loads(line))
    return samples

def randomize_numbers(s):
    """
    Replace each integer in a string with a new random integer
    of the same digit‐length.
    """
    def repl(m):
        orig = m.group(0)
        length = len(orig)
        if length == 1:
            low, high = 1, 9
        else:
            low = 10**(length - 1)
            high = 10**length - 1
        return str(random.randint(low, high))
    return re.sub(r'\d+', repl, s)

def generate(samples, n_samples):
    """
    For each new sample, pick one of the originals at random,
    then randomize numbers in every string field.
    """
    for _ in range(n_samples):
        orig = random.choice(samples)
        new = {}
        for k, v in orig.items():
            if isinstance(v, str):
                new[k] = randomize_numbers(v)
            else:
                new[k] = v
        yield new

def main():
    # raw‐string to avoid invalid-escape warnings
    base_dir = r'D:\LLM\DATA'
    in_path  = os.path.join(base_dir, 'samples.jsonl')
    out_path = os.path.join(base_dir, 'generated_samples.jsonl')
    n = 10000

    samples = load_samples(in_path)
    with open(out_path, 'w', encoding='utf-8') as fout:
        for sample in generate(samples, n):
            fout.write(json.dumps(sample, ensure_ascii=False) + '\n')

if __name__ == '__main__':
    main()
