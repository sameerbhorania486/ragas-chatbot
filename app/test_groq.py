from app.services.llm import test_groq_connection

try:
    answer = test_groq_connection()

    print("\nGROQ CONNECTION SUCCESSFUL")
    print(answer)

except Exception as e:
    print("GROQ ERROR:", str(e))