# E32 probability_random audit

- records: 30
- unique source texts: 29
- new dedicated runtime: False

## Classification
- `random_target`: 13
- `random_choice_without_explicit_probability`: 11
- `probabilistic_effect`: 3
- `per_coin_random_outcome`: 1
- `probabilistic_trigger_or_reuse`: 1
- `non_probability_clause_overlap`: 1

## Conclusion

- Random target clauses route to the existing Target Selector/random selector contract.
- Explicit probability triggers/reuse route to the existing probabilistic trigger/reuse contracts.
- Per-coin random outcomes are a genuine contract gap: the audit does not invent a dedicated runtime yet; it identifies the required RuleIR parameterization (independent RNG trial per coin/ammo unit and state-dependent probability).
- Do not apply arbitrary probability corrections or forced 100% conversion in this audit.