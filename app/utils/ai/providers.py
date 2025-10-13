from agents import ModelProvider, OpenAIChatCompletionsModel, Model


class OpenRouterProvider(ModelProvider):
    def __init__(self, client, *, model_name: str = None):
        self.client = client
        self.model_name = model_name

    def get_model(self, model_name: str | None) -> Model:
        return OpenAIChatCompletionsModel(
            model=model_name or self.model_name, openai_client=self.client
        )
