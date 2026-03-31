# Imports
from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine
import re

# FAST NLP ENGINE (SMALL MODEL)
configuration = {
    "nlp_engine_name": "spacy",
    "models": [{"lang_code": "en", "model_name": "en_core_web_sm"}],
}

provider = NlpEngineProvider(nlp_configuration=configuration)
nlp_engine = provider.create_engine()

analyzer = AnalyzerEngine(nlp_engine=nlp_engine)
anonymizer = AnonymizerEngine()

# CUSTOM RECOGNIZERS

patterns = [
    ("IP_ADDRESS", r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b", 0.9),
    ("PASSWORD", r"(?i)(password\s*[:=]\s*)(\S+)", 0.95),
    ("POSTCODE", r"\b[A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2}\b", 0.85),
    ("USERNAME", r"(?i)(username\s*[:=]\s*)([a-zA-Z0-9_.-]{3,20})", 0.85),
    ("ID_NUM", r"\b(ID|Student\s?ID|UID)\s*[:=]?\s*([A-Z0-9-]{4,20})\b", 0.85),
    ("URL_PERSONAL", r"\bhttps?://[^\s]+\b", 0.8),
    ("STREET_ADDRESS", r"\b\d{1,5}\s+\w+(\s\w+){1,4}\s?(Street|St|Road|Rd|Avenue|Ave|Lane|Ln)\b", 0.7),
]

for name, regex, score in patterns:
    recognizer = PatternRecognizer(
        supported_entity=name,
        patterns=[Pattern(name=name, regex=regex, score=score)]
    )
    analyzer.registry.add_recognizer(recognizer)

# FAST PRE-FILTER CHECK

def detect_possible_entities(text):
    text_lower = text.lower()
    entities = []

    if any(x in text_lower for x in ["name", "mr", "ms"]):
        entities.append("PERSON")

    if "@" in text or "[at]" in text_lower:
        entities.append("EMAIL_ADDRESS")

    if any(char.isdigit() for char in text):
        entities.extend(["PHONE_NUMBER", "CREDIT_CARD", "ID_NUM", "IP_ADDRESS"])

    if "password" in text_lower:
        entities.append("PASSWORD")

    if "username" in text_lower:
        entities.append("USERNAME")

    if "http" in text_lower:
        entities.append("URL_PERSONAL")

    if any(word in text_lower for word in ["street", "road", "lane", "ave"]):
        entities.append("STREET_ADDRESS")

    if any(month in text_lower for month in [
        "january","february","march","april","may","june",
        "july","august","september","october","november","december"
    ]) or re.search(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b", text):
        entities.append("DATE_TIME")

    # always check postcode (cheap regex)
    entities.append("POSTCODE")

    return list(set(entities))


# Cleanup
def extra_cleanup(text):
    text = re.sub(
        r"\b(\w+)\s?\[at\]\s?(\w+)\s?\[dot\]\s?(\w+)\b",
        "<EMAIL_ADDRESS>",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(r"\b(?:\d[ -]*?){13,16}\b", "<CREDIT_CARD>", text)
    return text


# MAIN FUNCTION (LOW LATENCY)
def redact_pii(text: str) -> str:
    start = time.time()

    text = extra_cleanup(text)

    # Step 1: detect only needed entities
    entities = detect_possible_entities(text)

    # Step 2: analyze only those
    results = analyzer.analyze(
        text=text,
        entities=entities,
        language="en"
    )

    # Step 3: anonymize
    redacted = anonymizer.anonymize(
        text=text,
        analyzer_results=results
    )

    print("Detected:", results)

    latency = time.time() - start_time
    
    return redacted.text, latency


# INPUT
if __name__ == "__main__":
    print("=== SentinLLM PII Redactor ===")
    print("Type 'exit' to stop\n")

    while True:
        user_input = input("Enter text: ")

        if user_input.lower() == "exit":
            print("Exiting...")
            break

        output = redact_pii(user_input)

        print("Redacted Output:", output)
        print("-" * 50)
