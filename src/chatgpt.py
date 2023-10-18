import openai
import os


class ChatBot(object):
    def __init__(self):
        api_key = os.getenv('WXKEY', default='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')
        if api_key is None:
            raise ValueError("api key missed")
        else:
            self.api_key = api_key
            openai.api_key = api_key
        self.model = 'gpt-3.5-turbo'

    def get_response(self, content):
        msg = [
            {'role': 'user', 'content': content}
        ]
        if self.api_key is not None:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=msg)

            message = response.choices[0]['message']['content']
            return message
        else:
            return ''
