# Qualitative Error Analysis

Systematic error analysis revealed three major findings:
1. **Non-Sentential Reference Fragments**: 33 out of 81 reference answers in the Mohler benchmark are noun phrases or lists without finite verbs, causing classical triple parsers to extract 0 reference propositions.
2. **Verbosity and Additional Information**: Unmatched student information frequently consists of conversational filler or restatements. Early scoring models (V2) awarded excessive bonus points for length.
3. **Core Paraphrase Divergence**: Students often rephrase core concepts using different syntax (e.g. passive voice, nominalizations). Failing to recognize these as core matches caused false unmatched classifications.
