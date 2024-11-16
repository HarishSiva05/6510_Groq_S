from commit_activity.activity import CommitsActivity

class Orchestrator:
    def __init__(self):
        self.commits_activity_obj = CommitsActivity()

    def chat(self):
        print("Chatbot is ready. Type 'exit' to end the conversation.")
        while True:
            user_input = input("You: ")
            if user_input.lower() == 'exit':
                print("Ending the conversation.")
                break
            response = self.commits_activity_obj.get_answer(user_input)
            print(f"Bot: {response}")

if __name__ == '__main__':
    orchestrator = Orchestrator()
    orchestrator.chat()
    