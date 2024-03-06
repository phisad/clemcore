from typing import List, Dict, Tuple, Any
from retry import retry
import anthropic
import backends
import json

logger = backends.get_logger(__name__)

NAME = "anthropic"


class Anthropic(backends.Backend):
    def __init__(self):
        creds = backends.load_credentials(NAME)
        self.client = anthropic.Anthropic(api_key=creds[NAME]["api_key"])

    def get_model_for(self, model_spec: backends.ModelSpec) -> backends.Model:
        return AnthropicModel(self.client, model_spec)


class AnthropicModel(backends.Model):
    def __init__(self, client: anthropic.Client, model_spec: backends.ModelSpec):
        super().__init__(model_spec)
        self.client = client

    @retry(tries=3, delay=0, logger=logger)
    def generate_response(self, messages: List[Dict]) -> Tuple[str, Any, str]:
        """
        :param messages: for example
                [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Who won the world series in 2020?"},
                    {"role": "assistant", "content": "The Los Angeles Dodgers won the World Series in 2020."},
                    {"role": "user", "content": "Where was it played?"}
                ]
        :return: the continuation
        """
        prompt = []
        system_message = ''
        for message in messages:
            if message["role"] == "system":
                system_message = message["content"]
            else:
                claude_message = {
                    "role": message["role"],
                    "content": [
                        {
                            "type": "text",
                            "text": message["content"]
                        }
                    ]
                }
                prompt.append(claude_message)


        completion = self.client.messages.create(
            messages=prompt,
            system=system_message,
            model=self.model_spec.model_id,
            temperature=self.get_temperature(),
            max_tokens=self.get_max_tokens()
        )

        json_output = completion.model_dump_json()
        response_text = completion.content[0].text

        return prompt, json.loads(json_output), response_text
