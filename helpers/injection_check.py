from langchain_experimental.prompt_injection_identifier.hugging_face_identifier import (
    HuggingFaceInjectionIdentifier,
)


def run_injection_check(query):
    injection_identifier = HuggingFaceInjectionIdentifier()
    try:
        injection_identifier.run(query)
        return "Safe"
    except:
        return "Prompt Injection Detected"