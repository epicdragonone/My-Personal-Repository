# Learnt a bit of Python from this :)
# Like Rnums and dataclasses

from enum import Enum
from typing import List, Union, Dict, Set, Optional, Sequence, Tuple
from dataclasses import dataclass

class NonTerminal(Enum):
    S  = 1
    NP = 2
    VP = 3
    PP = 4
    N  = 5
    V  = 6
    P  = 7

RULES: Dict[NonTerminal, List[List[Union[NonTerminal, str]]]] = {
    NonTerminal.S : [[NonTerminal.NP, NonTerminal.VP]],
    NonTerminal.NP: [[NonTerminal.N, NonTerminal.PP], [NonTerminal.N]],
    NonTerminal.PP: [[NonTerminal.P, NonTerminal.NP]],
    NonTerminal.VP: [
        [NonTerminal.VP, NonTerminal.PP],
        [NonTerminal.V, NonTerminal.VP],
        [NonTerminal.V, NonTerminal.NP],
        [NonTerminal.V]
    ],
    NonTerminal.N : [["can"], ["fish"], ["they"], ["rivers"], ["December"]],
    NonTerminal.P : [["in"]],
    NonTerminal.V : [["can"], ["they"]]
}

@dataclass(frozen=True)
class Production:
    lhs: NonTerminal
    rhs: Tuple[Union[NonTerminal, str], ...]

    def __repr__(self) -> str:
        rhs_str = " ".join(sym.name if isinstance(sym, NonTerminal) else sym for sym in self.rhs)
        return f"{self.lhs.name} -> {rhs_str}"

@dataclass(frozen=True)
class State:
    production: Production
    dot: int
    start: int

    def is_complete(self) -> bool:
        return self.dot >= len(self.production.rhs)

    def next_symbol(self) -> Optional[Union[NonTerminal, str]]:
        return None if self.is_complete() else self.production.rhs[self.dot]

    def advance(self) -> "State":
        return State(self.production, self.dot + 1, self.start)

    def __repr__(self) -> str:
        items = list(self.production.rhs)
        items.insert(self.dot, " . ")
        rhs_str = " ".join(sym.name if isinstance(sym, NonTerminal) else sym for sym in items)
        return f"[{self.production.lhs.name} -> {rhs_str}, from {self.start}]"

class Grammar:
    def __init__(self, rules: Dict[NonTerminal, List[List[Union[NonTerminal, str]]]], start: NonTerminal) -> None:
        self.rules = rules
        self.start = start

    def productions_for(self, nt: NonTerminal) -> List[Production]:
        return [Production(nt, tuple(rhs)) for rhs in self.rules.get(nt, [])]

class Chart:
    def __init__(self, length: int) -> None:
        self.columns: List[Set[State]] = [set() for _ in range(length + 1)]

    def add(self, idx: int, state: State) -> bool:
        if state not in self.columns[idx]:
            self.columns[idx].add(state)
            return True
        return False

    def __getitem__(self, idx: int) -> Set[State]:
        return self.columns[idx]

    def __repr__(self) -> str:
        lines = []
        for i, col in enumerate(self.columns):
            entries = ", ".join(str(s) for s in col)
            lines.append(f"Chart[{i}]: {entries}")
        return "\n".join(lines)

class EarleyParser:
    def __init__(self, grammar: Grammar) -> None:
        self.grammar = grammar

    def parse(self, tokens: Sequence[str]) -> bool:
        n = len(tokens)
        chart = Chart(n)
        for prod in self.grammar.productions_for(self.grammar.start):
            chart.add(0, State(prod, 0, 0))
        for i in range(n + 1):
            changed = True
            while changed:
                changed = False
                for st in list(chart[i]):
                    sym = st.next_symbol()
                    if sym is None:
                        # Completer
                        for prev in list(chart[st.start]):
                            if prev.next_symbol() == st.production.lhs:
                                if chart.add(i, prev.advance()):
                                    changed = True
                    elif isinstance(sym, NonTerminal):
                        # Predictor
                        for prod in self.grammar.productions_for(sym):
                            if chart.add(i, State(prod, 0, i)):
                                changed = True
                    else:
                        # Scanner
                        if i < n and tokens[i] == sym:
                            if chart.add(i + 1, st.advance()):
                                changed = True
        return sum(
            st.production.lhs == self.grammar.start and st.start == 0 and st.is_complete()
            for st in chart.columns[n]
        )

if __name__ == "__main__":
    grammar = Grammar(RULES, NonTerminal.S)
    parser = EarleyParser(grammar)
    test_sents = [["they", "can", "fish", "in", "rivers", "in", "December"], ["they", "can", "fish"]]
    for sent in test_sents:
        res = parser.parse(sent)
        print(f"{sent} -> {res if res else 'rejected'}")