from natasha.obj import Obj
from natasha.extractors import Extractor, Match


class AddrExtractorConfig(Extractor):
    def __init__(self, morph, config):
        from .grammars.addrConfig import get_addr_part

        addr_parts = get_addr_part(config)

        Extractor.__init__(self, addr_parts, morph)

    def find(self, text):
        matches = list(self(text))
        if not matches:
            return

        matches = sorted(matches, key=lambda _: _.start)
        start = matches[0].start
        stop = matches[-1].stop
        parts = [_.fact for _ in matches]
        return Match(start, stop, Obj.Addr(parts))
