from datetime import datetime
import json

from prompts import INITIAL_PROMPT
from prompts import FORMAT_PROMPT
from llm import LLM
from utils import Github

class CommitsActivity:
    def __init__(self):
        self.llm_client = LLM()
        self.today = datetime.now().strftime("%Y-%m-%d %H:%M")
        self.github_object = Github()

    def preprocess_api_response(self, response_list):
        # keys_to_keep = {
        #     "commit": {
        #         "author": ["name", "email", "date"],
        #         "committer": ["name", "email", "date"],
        #         "message": None
        #     },
        #     "html_url": None,
        #     "author": ["login", "id"],
        #     "committer": ["login", "id"]
        # }
        # processed_data = []
        # for response in response_list:
        #     def filter_keys(data, keys):
        #         if isinstance(data, dict):
        #             return {k: filter_keys(data[k], v) for k, v in keys.items() if k in data}
        #         return data

        #     data = [filter_keys(item, keys_to_keep) for item in response]
        #     processed_data.append(data)
        return json.dumps(response_list)

    def get_github_commits(self, call):
        api_response = self.github_object.get_commit_info()
        return self.preprocess_api_response(api_response)

    def get_answer(self, user_input):
        messages = [
            {
                "role": "system",
                "content": INITIAL_PROMPT.format(self.today)

            },
            {
                "role": "user",
                "content": user_input
            }
        ]
        response_message = self.llm_client.get_response(messages)

        tool_calls = response_message.choices[0].message.tool_calls

        if tool_calls:
            available_functions = {
            "get_github_commits": self.get_github_commits
            }

            response_message.choices[0].message.content = 'Proceeding to call function' # Handling this error - {'error': {'message': "'messages.3' : for 'role:tool' the following must be satisfied[('messages.3.content' : value must be a string)]", 'type': 'invalid_request_error'}}
            messages.append(response_message.choices[0].message)

            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_to_call = available_functions[function_name]
                function_args = json.loads(tool_call.function.arguments)

                function_response = function_to_call(
                    call=function_args 
                )

                messages.append(
                    {
                        "tool_call_id": tool_call.id, 
                        "role": "tool",
                        "name": function_name,
                        "content": function_response,
                    }
                )
                messages.append(
                    {
                        "role": "system",
                        "content": FORMAT_PROMPT
                    }
                )

            second_response = self.llm_client.get_response(messages)
            return second_response.choices[0].message.content
        
        else:
            return response_message.choices[0].message.content