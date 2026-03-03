from langchain_core.prompts import ChatPromptTemplate

template = ChatPromptTemplate.from_messages(
    [("system", "너는 {topic} 전문가야."), ("human", "{question}")]
)

formated_template = template.format_messages(
    topic="경제", question="코스피 지수를 예측해줘"
)

print(formated_template)

template2 = ChatPromptTemplate.from_template("""너는 {topic} 전문가야. {question}")""")

formated_template2 = template2.format_prompt(
    topic="경제", question="코스피 지수를 예측해줘"
)

print(formated_template2)
