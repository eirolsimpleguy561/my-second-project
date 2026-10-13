from transformers import pipeline


def create_qa_bot():
    print("Loading QA model (this may take a moment)...")
    qa = pipeline("question-answering", model="distilbert-base-cased-distilled-squad")
    return qa


def chat(qa_pipeline):
    print("\n=== NLP QA Chatbot ===")
    print("Provide a context paragraph, then ask questions about it.")
    print("Type 'new' to change the context. Type 'exit' to quit.\n")

    context = input("Enter context paragraph:\n> ").strip()
    if not context:
        print("No context provided.")
        return

    while True:
        question = input("\nYour question (or 'new'/'exit'): ").strip()
        if question.lower() == 'exit':
            print("Goodbye!")
            break
        if question.lower() == 'new':
            context = input("Enter new context:\n> ").strip()
            continue
        if not question:
            continue

        result = qa_pipeline(question=question, context=context)
        answer = result['answer']
        score = result['score']

        if score < 0.1:
            print("Bot: I'm not confident about that answer based on the context.")
        else:
            print(f"Bot: {answer}  (confidence: {score:.2%})")


if __name__ == "__main__":
    bot = create_qa_bot()
    chat(bot)
