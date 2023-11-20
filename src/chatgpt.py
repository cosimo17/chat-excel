import openai


class ChatBot(object):
    def __init__(self):
        self.api_key = ''
        self.model = 'gpt-3.5-turbo'

    def set_api_key(self, api_key):
        self.api_key = api_key
        openai.api_key = api_key

    def get_response(self, content):
        msg = [
            {'role': 'user', 'content': content}
        ]
        if self.api_key is not None:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=msg,
                temperature=0.3)

            message = response.choices[0]['message']['content']
            token_count = response['usage']['total_tokens']
            return message, int(token_count)
        else:
            return '', 0
