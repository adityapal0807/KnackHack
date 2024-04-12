from langchain_experimental.data_anonymizer import PresidioReversibleAnonymizer

class AnonymizerService:
    def __init__(self):
        self.anonymizer = PresidioReversibleAnonymizer(
            # Faker seed is used here to make sure the same fake data is generated for the test purposes
            # In production, it is recommended to remove the faker_seed parameter (it will default to None)
            # faker_seed=42,
        )

    def create_pattern():
        pass
    
    def anonymize_text(self, text):
        anonymized_text = self.anonymizer.anonymize(text)
        return anonymized_text
    
    def deanonymize_text(self,text):
        anonymized_text = self.anonymizer.deanonymize(text)
        return anonymized_text

    def reset_mapping(self):
        self.anonymizer.reset_deanonymizer_mapping()

    