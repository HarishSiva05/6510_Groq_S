TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_github_commits",
            "description": """
                Get the github commits in github for a specific repository
            """,
            "parameters": {
                "type": "object",
                "properties": {
                    "call": {
                        "type": "boolean",
                        "description": "Just give a true or false value for function usage"
                    },
                }
            }
        }
    }
]