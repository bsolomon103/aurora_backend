from langchain.prompts import PromptTemplate, ChatPromptTemplate, HumanMessagePromptTemplate, MessagesPlaceholder
from langchain.output_parsers import StructuredOutputParser, ResponseSchema
from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser



def aurora_prompt():
    #Prompt templates provide pre defined recipes for generating prompts for language models
    

    template = """You are a friendly and helpful assistant working for a UK based local authority and you answer all questions with a 50 word maximum response.
        Personalise all references to the local authority, for e.g. instead of contact your local authority, say contact us.
        Answer incoming questions using this {context}. 
        Always include a URL link in your response if one is available.
       
    """
    
    prompt = ChatPromptTemplate.from_messages(
        [("system", template),
         ("human", "{input}"),
         MessagesPlaceholder(variable_name='agent_scratchpad')
        ]

    )
    return prompt