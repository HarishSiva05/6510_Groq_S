import warnings
warnings.filterwarnings("ignore")

from groq import Groq
from commit_activity.tools import TOOLS
import constants

class LLM:
    def __init__(self):
        self.api_key = constants.GROQ_API_KEY
        self.model = constants.MODEL
        self.client = Groq(api_key=self.api_key)

    def get_response(self, messages_list, tool_use="auto"):
        response = self.client.chat.completions.create(
            model = self.model,
            messages = messages_list,
            stream=False,
            temperature = 1.0,
            tools = TOOLS,
            tool_choice = tool_use
            )

        return response

if __name__ == '__main__':
    llm = LLM()
    messages = [
        {
            "role":"user",
            "content":"What is the date today?"
        }
    ]
    response = llm.get_response(messages)
    print(response)