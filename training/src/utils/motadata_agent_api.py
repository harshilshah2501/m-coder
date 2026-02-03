from clean_output_v2 import clean_agent_response
import requests

class MotadataAgentAPI:
    def __init__(self):
        self.api_url = "http://localhost:8000/v1/chat/completions"
    
    def ask(self, question):
        payload = {
            "model": "motadata-coder",
            "messages": [{"role": "user", "content": f"Answer this about Motadata codebase: {question}"}],
            "temperature": 0.1
        }
        resp = requests.post(self.api_url, json=payload).json()
        raw = resp['choices'][0]['message']['content']
        return clean_agent_response(raw)

# Test
api = MotadataAgentAPI()
print(api.ask("What methods does Query have?"))
