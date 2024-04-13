generic_prompt ="""Hello Agent, 
Role: Your role is to create monitoring rules for questions being asked to a company's AI chatbot ensuring the responsible and ethical use of AI, particularly ChatGPT, within organizational boundaries.

Please follow the following guidlines for rule generation:
1.Rules should align with compliance documents such as EU AI regulations, GDPR, and general standards. 
2.No query posed to company's ChatGPT should violate these rules.
3.Please provide your response inside a list of dictionary with keys exactly same of the following format:("rule_(rule number)": (rule description here)) and nothing else so that it helps extracting later using json.loads. Keys must be enclosed in doubleqoutes,not single.
4.Provide 10-15 well-formed concise rules.

Examples:

Bad Questions (violating rules):

1. "How can I use AI to hack into my competitor's database and gain an unfair advantage in the market?"
2. "What AI models can I use to exploit loopholes in GDPR and access personal data without consent?"
3. "Can you help me implement an AI system that systematically discriminates against certain demographic groups in hiring processes?"
4. "I need advice on deploying an AI system that makes decisions without providing any explanations, especially when it comes to denying individuals access to services."
5. "How can I bypass security measures using AI to gain unauthorized access to sensitive information?"

Right Questions (aligning with rules):

1. "What are the best practices for ensuring AI usage complies with data privacy laws like GDPR?"
2. "Can you recommend techniques for minimizing bias in AI algorithms, especially in decision-making processes?"
3. "How can I ensure transparency in AI systems to provide explanations for their decisions, particularly in sensitive situations?"
4. "What are the key considerations for maintaining security in AI systems and preventing unauthorized access?"
5. "Can you provide guidance on implementing user consent mechanisms in AI interactions to respect user autonomy?"

Thank you for promoting ethical AI usage.
"""


def query_classification_prompt(rules):

    query_classification_prompt= f'''
        Role: You are a query classification agent which classifies user query into Safe/Unsafe

        Examples of safe and unsafe questions are as following:

        * UNSAFE QUESTIONS: *
        1. "Can you help me access confidential employee performance data without authorization?"
        Reason Unsafe: This question is unsafe as it directly violates data protection regulations and seeks advice on bypassing security measures. It also disregards user rights and autonomy, which are important ethical considerations.

        2."How can we deploy AI algorithms to target specific demographic groups for marketing purposes?"
        Reason Unsafe: This question is unsafe as it involves implementing AI systems that systematically discriminate against certain demographic groups, which goes against ethical principles and fairness in AI usage.

        3."Is there a way to use AI to make hiring decisions without providing explanations to candidates?"
        Reason Unsafe: This question is unsafe because it seeks guidance on deploying AI systems that make decisions without providing explanations, which can lead to biased outcomes and unfair treatment of candidates.

        4."What AI models can we use to exploit regulatory loopholes and maximize profit margins?"
        Reason Unsafe: This question is unsafe as it aims to exploit loopholes in regulations and violates ethical principles promoting fairness, accountability, and transparency in AI usage.

        5. "How can we use AI to collect personal data from customers without their consent for targeted advertising?"
        Reason Unsafe:This question is unsafe as it seeks advice on accessing personal data without consent, which is a clear violation of data privacy and consent management principles. It also disregards user autonomy and ethical considerations.


        * SAFE QUESTIONS: *
        1."Can you provide me with a summary of the latest market trends in our industry?"
        Reason Safe:This question is safe because it seeks general information that does not involve exploiting loopholes or accessing personal data without consent. It aligns with ethical principles and promotes transparency in AI usage.

        2."What are some strategies for improving team collaboration in a remote work setting?"
        Reason Safe:This question is safe as it pertains to best practices and does not involve bypassing security measures or discriminating against any demographic groups. It promotes fairness, ethics, and accountability in AI usage.

        3."Could you suggest some effective time management techniques for boosting productivity?"
        Reason Safe:This question is safe because it seeks advice on productivity enhancement, which aligns with responsible AI usage and ethical principles. It does not aim to exploit loopholes or violate fairness and transparency principles.

        4."What are some environmentally sustainable practices that our company could adopt?"
        Reason Safe:This question is safe as it pertains to corporate sustainability efforts and does not involve deploying AI systems without considering impact assessment or risk management. It aligns with ethical principles and compliance standards such as GDPR.

        5."How can we optimize our customer service processes to enhance customer satisfaction?"
        Reason Safe:This question is safe because it seeks guidance on improving customer service without aiming to exploit AI for unfair advantage in the market or violate fairness and ethics principles. It promotes accountability and transparency in AI usage.

        You can validate you classifications with the help of the following rules:
        * RULES *
        {rules}

        If any query is unsafe, mention the rule number being violated (Example: rule_no 1,rule_no 2 etc.) in the reason key in output.reason key should have 2 keys in total if unsafe: rule , description

        * RESPONSE *
        Please provide your response inside a dictionary with keys exactly same of the following format:("query": (query here), "class":(classfication here 'Unsafe' or 'Safe'), "reason":()) and nothing else so that it helps extracting later using json.loads. Keys must be enclosed in doubleqoutes,not single.
    '''

    return query_classification_prompt


safety_prompt = f"""
    "Create a summary report of the user's behavior based on their chat history and details. Determine whether the user is safe for the organization or not and following organisation's compliances or not.
    Prepare a detailed comprehensive report. The report should be in JSON format with key as 'summary'"
"""
