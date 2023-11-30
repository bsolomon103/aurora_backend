from langchain.prompts import PromptTemplate, ChatPromptTemplate, HumanMessagePromptTemplate, MessagesPlaceholder

def aurora_prompt():
    #Prompt templates provide pre defined recipes for generating prompts for language models
    template = """You are a friendly and helpful assistant working for a UK based local authority.
    Answer incoming questions using this {context}
    Limit your response to 50 words max
    """
    
    prompt = ChatPromptTemplate.from_messages(
        [("system", template),
         ("human", "{input}"),
         MessagesPlaceholder(variable_name='agent_scratchpad')
    
        ]
    )
    return prompt