from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.config import settings


prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """You are a professional customer support agent for Mectro Company.

Reply using ONLY the provided retrieved data.
Never invent information.
If no useful data is found, apologize and ask the customer to verify their order ID or rephrase.
Be concise, warm, and professional.
Never mention databases, agents, tools, or internal systems.
Use bullet points for important order details when helpful."""
    ),
    (
        "human",
        """Customer: {query}
Intent: {intent}
Retrieved data: {retrieved_data}

Write the final customer-facing reply."""
    ),
])


llm = ChatGroq(
    api_key=settings.GROQ_API_KEY,
    model=settings.GROQ_MODEL,
    temperature=0.4,
)

chain = prompt | llm | StrOutputParser()


def generate_response(query: str, intent: str, retrieved_data: str) -> str:
    return chain.invoke({
        "query": query,
        "intent": intent,
        "retrieved_data": retrieved_data,
    })