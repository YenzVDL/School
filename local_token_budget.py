"""Conservative ASCII-only Qwen2 byte-BPE budget using installed GGUF metadata.

No inference/downloads. This deliberately refuses other tokenizer families and
non-ASCII prompts; it is not a general-purpose tokenizer. A 64-token allowance
covers the separately pinned two-message Qwen3 chat template and think:false.
"""
import re
from approaches import ContextOverflowError

PIECES = re.compile(r"(?i:'s|'t|'re|'ve|'m|'ll|'d)|[^\r\nA-Za-z0-9]?[A-Za-z]+|[0-9]| ?[^\sA-Za-z0-9]+[\r\n]*|\s*[\r\n]+|\s+(?!\S)|\s+", re.ASCII)


class QwenAsciiBudget:
    def __init__(self, info):
        if (info.get('tokenizer.ggml.pre') != 'qwen2' or info.get('tokenizer.ggml.model') != 'gpt2'
                or info.get('tokenizer.ggml.add_bos_token') is not False):
            raise ValueError('unsupported_local_tokenizer')
        self.ranks = {tuple(pair.split(' ')): rank for rank, pair in enumerate(info['tokenizer.ggml.merges'])}
        values = list(range(33,127)) + list(range(161,173)) + list(range(174,256))
        mapping = {value: chr(value) for value in values}
        extra = 0
        for value in range(256):
            if value not in mapping:
                mapping[value] = chr(256 + extra)
                extra += 1
        self.mapping, self.cache = mapping, {}

    def count(self, text):
        if not text.isascii():
            raise ValueError('non_ascii_budget_preflight_requires_supported_tokenizer')
        count = 0
        for piece in PIECES.findall(text):
            if piece not in self.cache:
                parts = [self.mapping[value] for value in piece.encode('ascii')]
                while len(parts) > 1:
                    choices = [(self.ranks[(left,right)], index) for index,(left,right)
                               in enumerate(zip(parts,parts[1:])) if (left,right) in self.ranks]
                    if not choices:
                        break
                    _, index = min(choices)
                    parts[index:index+2] = [parts[index]+parts[index+1]]
                self.cache[piece] = len(parts)
            count += self.cache[piece]
        return count

    def check(self, request):
        bound = self.count(request.system) + self.count(request.payload_json) + 64
        if bound + request.options['num_predict'] > request.options['num_ctx']:
            raise ContextOverflowError('token_budget_exceeded')
        return bound
