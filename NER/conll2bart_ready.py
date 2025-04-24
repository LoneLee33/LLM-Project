import json
import argparse

# same mapping as before
TAG_MAPPING = {
    'VAR':       'var',
    'PARAM':     'param',
    'OBJ_NAME':  'obj_name',
    'OBJ_DIR':   'obj_dir',
    'CONST_DIR': 'const_dir',
    'LIMIT':     'limit',
}

PUNCTUATION = {'.', ',', '!', '?', ';', ':'}
CONTRACTIONS = {"'s", "n't", "'re", "'ll", "'ve", "'d", "'m"}

def read_conll(path):
    sents, tokens, tags = [], [], []
    with open(path, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('-DOCSTART-'):
                if tokens:
                    sents.append((tokens, tags))
                    tokens, tags = [], []
                continue
            parts = line.split()
            tokens.append(parts[0])
            tags.append(parts[-1])
        if tokens:
            sents.append((tokens, tags))
    return sents

def join_tokens(tokens):
    out = ''
    for tok in tokens:
        if not out:
            out = tok
        elif tok in PUNCTUATION or tok in CONTRACTIONS:
            out += tok
        else:
            out += ' ' + tok
    return out

def tokens_to_tagged_text(tokens, tags):
    out_tokens = []
    i = 0
    while i < len(tokens):
        tag = tags[i]
        if tag.startswith('B-'):
            label = tag[2:]
            xml = TAG_MAPPING[label]
            span = [tokens[i]]
            i += 1
            while i < len(tokens) and tags[i] == 'I-'+label:
                span.append(tokens[i])
                i += 1
            out_tokens.append(f"<{xml}>{join_tokens(span)}</{xml}>")
        else:
            out_tokens.append(tokens[i])
            i += 1
    return join_tokens(out_tokens)

def main(conll_path, out_jsonl):
    sents = read_conll(conll_path)
    with open(out_jsonl, 'w', encoding='utf-8') as fw:
        for tokens, tags in sents:
            inp = tokens_to_tagged_text(tokens, tags)
            json.dump({'input': inp}, fw, ensure_ascii=False)
            fw.write('\n')

if __name__ == '__main__':
    p = argparse.ArgumentParser(
        description="Convert CoNLL NER predictions into BART-ready JSONL inputs"
    )
    p.add_argument('--conll', required=True,
                   help="path to your CoNLL output (tokens + predicted BIO tags)")
    p.add_argument('--out', required=True,
                   help="where to write the BART-ready JSONL (each line: {'input': ...})")
    args = p.parse_args()
    main(args.conll, args.out)
