"""
Text Preprocessor for Base ASAG.

This module provides the Stage 3 preprocessing component for the Base ASAG
system, performing sentence segmentation, tokenization, basic normalization,
lemmatization, and POS tagging via spaCy.

To preserve complete syntactic integrity for downstream dependency parsing,
stop words, negation markers, and punctuation are strictly preserved.
"""

from dataclasses import dataclass, field
import re
from typing import Any, Dict, List, Optional
import spacy
from spacy.language import Language


@dataclass(frozen=True)
class TokenInfo:
    """
    Structured linguistic attributes for an individual token.

    Attributes
    ----------
    text : str
        Original token surface form.
    lemma : str
        Lemmatized base form of the token.
    pos : str
        Coarse-grained part-of-speech tag (Universal POS tags, e.g., NOUN, VERB).
    tag : str
        Fine-grained part-of-speech tag (Penn Treebank tags, e.g., NN, VBZ).
    idx : int
        Character offset index in the sentence string.
    is_stop : bool
        Whether the token is classified as a stop word in spaCy.
    is_punct : bool
        Whether the token is punctuation.
    is_alpha : bool
        Whether the token consists solely of alphabetic characters.
    """
    text: str
    lemma: str
    pos: str
    tag: str
    idx: int
    is_stop: bool
    is_punct: bool
    is_alpha: bool

    def to_dict(self) -> Dict[str, Any]:
        """Return token attributes as a dictionary."""
        return {
            "text": self.text,
            "lemma": self.lemma,
            "pos": self.pos,
            "tag": self.tag,
            "idx": self.idx,
            "is_stop": self.is_stop,
            "is_punct": self.is_punct,
            "is_alpha": self.is_alpha,
        }


@dataclass
class ProcessedSentence:
    """
    Representation of a processed sentence containing tokens, lemmas, and POS tags.

    Attributes
    ----------
    original_text : str
        The raw surface text of the sentence.
    normalized_text : str
        The normalized text representation (cleaned whitespace, standard unicode).
    tokens : List[str]
        List of surface token strings.
    lemmas : List[str]
        List of lemmatized token strings.
    pos_tags : List[str]
        List of coarse-grained Universal POS tags (e.g., NOUN, VERB).
    detailed_pos_tags : List[str]
        List of fine-grained Penn Treebank POS tags (e.g., NN, VBZ).
    tokens_info : List[TokenInfo]
        Detailed structured metadata for each token.
    """
    original_text: str
    normalized_text: str
    tokens: List[str]
    lemmas: List[str]
    pos_tags: List[str]
    detailed_pos_tags: List[str] = field(default_factory=list)
    tokens_info: List[TokenInfo] = field(default_factory=list)

    @property
    def token_count(self) -> int:
        """Total number of tokens in the sentence."""
        return len(self.tokens)

    def to_dict(self) -> Dict[str, Any]:
        """Return sentence representation as a dictionary."""
        return {
            "original_text": self.original_text,
            "normalized_text": self.normalized_text,
            "tokens": self.tokens,
            "lemmas": self.lemmas,
            "pos_tags": self.pos_tags,
            "detailed_pos_tags": self.detailed_pos_tags,
            "tokens_info": [tok.to_dict() for tok in self.tokens_info],
        }


@dataclass
class ProcessedDocument:
    """
    Representation of a processed multi-sentence document or answer string.

    Attributes
    ----------
    original_text : str
        The raw unedited document string.
    normalized_text : str
        The document text with whitespace and character normalization.
    sentences : List[ProcessedSentence]
        Individual segmented and processed sentences.
    """
    original_text: str
    normalized_text: str
    sentences: List[ProcessedSentence]

    @property
    def sentence_count(self) -> int:
        """Total number of segmented sentences."""
        return len(self.sentences)

    @property
    def tokens(self) -> List[str]:
        """Flattened list of all token strings across sentences."""
        return [tok for sent in self.sentences for tok in sent.tokens]

    @property
    def lemmas(self) -> List[str]:
        """Flattened list of all lemmas across sentences."""
        return [lem for sent in self.sentences for lem in sent.lemmas]

    @property
    def pos_tags(self) -> List[str]:
        """Flattened list of all coarse POS tags across sentences."""
        return [pos for sent in self.sentences for pos in sent.pos_tags]

    @property
    def detailed_pos_tags(self) -> List[str]:
        """Flattened list of all fine-grained POS tags across sentences."""
        return [tag for sent in self.sentences for tag in sent.detailed_pos_tags]

    def to_dict(self) -> Dict[str, Any]:
        """Return document representation as a dictionary."""
        return {
            "original_text": self.original_text,
            "normalized_text": self.normalized_text,
            "sentence_count": self.sentence_count,
            "sentences": [s.to_dict() for s in self.sentences],
            "tokens": self.tokens,
            "lemmas": self.lemmas,
            "pos_tags": self.pos_tags,
        }


def normalize_text(text: str, lowercase: bool = False) -> str:
    """
    Perform non-destructive basic text normalization.

    Operations:
    1. Unicode quotation and dash standardization.
    2. Non-breaking space replacement.
    3. Multiple consecutive whitespace collapsing.
    4. Leading and trailing whitespace stripping.
    5. Optional lowercasing.

    Does NOT remove stop words, negation terms, or syntactic punctuation.

    Parameters
    ----------
    text : str
        Raw input string.
    lowercase : bool, default=False
        Whether to convert characters to lowercase.

    Returns
    -------
    str
        Cleaned, normalized string.

    Raises
    ------
    TypeError
        If text is not a string.
    """
    if not isinstance(text, str):
        raise TypeError(f"Input text must be a string, got {type(text).__name__}.")

    # Standardize non-breaking spaces and typography
    clean = text.replace("\u00a0", " ")
    clean = clean.replace("“", '"').replace("”", '"')
    clean = clean.replace("‘", "'").replace("’", "'")
    clean = clean.replace("—", " - ").replace("–", " - ")

    # Collapse multiple whitespace characters
    clean = re.sub(r"\s+", " ", clean).strip()

    if lowercase:
        clean = clean.lower()

    return clean


class TextPreprocessor:
    """
    Preprocessing pipeline for Base ASAG.

    Coordinates sentence segmentation, tokenization, normalization,
    lemmatization, and POS tagging using a spaCy pipeline.

    The dependency parser and NER modules are explicitly disabled to maintain
    modular isolation from Stage 4 (Dependency Parsing).
    """

    def __init__(
        self,
        model_name: str = "en_core_web_sm",
        lowercase: bool = False,
        nlp: Optional[Language] = None,
    ):
        """
        Initialize the TextPreprocessor with a spaCy language model.

        Parameters
        ----------
        model_name : str, default="en_core_web_sm"
            Name of the spaCy English model to load.
        lowercase : bool, default=False
            Whether normalized_text should be converted to lowercase.
        nlp : Optional[Language], default=None
            Existing spaCy Language object to reuse.
        """
        self.model_name = model_name
        self.lowercase = lowercase

        if nlp is not None:
            self.nlp = nlp
        else:
            try:
                # Disable parser and NER to keep Stage 3 strictly focused on preprocessing
                self.nlp = spacy.load(model_name, disable=["parser", "ner"])
            except OSError as exc:
                raise OSError(
                    f"spaCy English model '{model_name}' is not installed.\n"
                    f"Please install it using:\n"
                    f"  python -m spacy download {model_name}"
                ) from exc

        # Use sentencizer component for rule-based sentence boundary detection
        if not self.nlp.has_pipe("sentencizer"):
            self.nlp.add_pipe("sentencizer")

    def _validate_input(self, text: Any, allow_empty: bool) -> str:
        """
        Validate input string and enforce type and emptiness constraints.

        Parameters
        ----------
        text : Any
            Input text to validate.
        allow_empty : bool
            Whether empty or whitespace-only inputs are allowed.

        Returns
        -------
        str
            Validated string.

        Raises
        ------
        TypeError
            If input is not a string.
        ValueError
            If input is empty or whitespace-only when allow_empty=False.
        """
        if not isinstance(text, str):
            raise TypeError(f"Input text must be a string, got {type(text).__name__}.")

        if not text.strip() and not allow_empty:
            raise ValueError("Input text cannot be empty or contain only whitespace.")

        return text

    def process(self, text: str, allow_empty: bool = False) -> ProcessedDocument:
        """
        Process a document or answer string into structured sentences and tokens.

        Parameters
        ----------
        text : str
            Input text to preprocess.
        allow_empty : bool, default=False
            If True, empty string yields an empty ProcessedDocument.
            If False, empty or whitespace-only input raises ValueError.

        Returns
        -------
        ProcessedDocument
            Document structure containing segmented ProcessedSentence instances.
        """
        raw_text = self._validate_input(text, allow_empty=allow_empty)

        # Handle allowed empty inputs gracefully
        if not raw_text.strip():
            return ProcessedDocument(
                original_text=raw_text,
                normalized_text="",
                sentences=[],
            )

        doc_normalized = normalize_text(raw_text, lowercase=self.lowercase)
        spacy_doc = self.nlp(doc_normalized)

        processed_sentences: List[ProcessedSentence] = []
        for sent_span in spacy_doc.sents:
            sent_orig = sent_span.text
            sent_norm = normalize_text(sent_orig, lowercase=self.lowercase)

            tokens: List[str] = []
            lemmas: List[str] = []
            pos_tags: List[str] = []
            detailed_pos_tags: List[str] = []
            tokens_info: List[TokenInfo] = []

            for tok in sent_span:
                # Do not discard stop words, negations, or punctuation
                tokens.append(tok.text)
                lemmas.append(tok.lemma_)
                pos_tags.append(tok.pos_)
                detailed_pos_tags.append(tok.tag_)

                tokens_info.append(
                    TokenInfo(
                        text=tok.text,
                        lemma=tok.lemma_,
                        pos=tok.pos_,
                        tag=tok.tag_,
                        idx=tok.idx,
                        is_stop=tok.is_stop,
                        is_punct=tok.is_punct,
                        is_alpha=tok.is_alpha,
                    )
                )

            processed_sentences.append(
                ProcessedSentence(
                    original_text=sent_orig,
                    normalized_text=sent_norm,
                    tokens=tokens,
                    lemmas=lemmas,
                    pos_tags=pos_tags,
                    detailed_pos_tags=detailed_pos_tags,
                    tokens_info=tokens_info,
                )
            )

        return ProcessedDocument(
            original_text=raw_text,
            normalized_text=doc_normalized,
            sentences=processed_sentences,
        )

    def process_document(self, text: str, allow_empty: bool = False) -> ProcessedDocument:
        """
        Alias for process() for explicit document-level preprocessing.

        Parameters
        ----------
        text : str
            Input document text.
        allow_empty : bool, default=False
            Whether empty input is accepted.

        Returns
        -------
        ProcessedDocument
            Structured document representation.
        """
        return self.process(text, allow_empty=allow_empty)

    def process_sentence(self, sentence_text: str) -> ProcessedSentence:
        """
        Preprocess a single sentence string.

        Parameters
        ----------
        sentence_text : str
            Sentence text to process.

        Returns
        -------
        ProcessedSentence
            Structured sentence representation.

        Raises
        ------
        ValueError
            If text contains zero or multiple segmented sentences.
        """
        doc = self.process(sentence_text, allow_empty=False)
        if len(doc.sentences) == 0:
            raise ValueError("Provided text does not yield any sentence.")
        if len(doc.sentences) > 1:
            raise ValueError(
                f"Expected exactly 1 sentence, but found {len(doc.sentences)}. "
                f"Use process() or process_document() for multi-sentence inputs."
            )
        return doc.sentences[0]
