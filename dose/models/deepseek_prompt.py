import requests
from django.db import models

class DeepSeekPrompt(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='deepseek_prompts')
    prompt = models.TextField(help_text="Prompt sent to DeepSeek API")
    response = models.TextField(blank=True, null=True, help_text="Response from DeepSeek API")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # If response is already set, prevent modification
        if self.pk and DeepSeekPrompt.objects.filter(pk=self.pk, response__isnull=False).exists():
            raise Exception("Cannot modify DeepSeekPrompt after response is saved.")
        # If creating and response is not set, call DeepSeek API
        if not self.response:
            self.response = self.get_deepseek_response()
        super().save(*args, **kwargs)

    def get_deepseek_response(self):
        # Replace with your actual DeepSeek API key
        api_key = 'YOUR_DEEPSEEK_API_KEY'
        url = "https://api.deepseek.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}"}
        data = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": self.prompt}]
        }
        try:
            response = requests.post(url, headers=headers, json=data)
            result = response.json()
            return result.get('choices', [{}])[0].get('message', {}).get('content', '')
        except Exception as e:
            return f"Error: {str(e)}"

    def __str__(self):
        return f"Prompt: {self.prompt[:50]}..."

    class Meta:
        verbose_name = "DoseAI Prompt"
        verbose_name_plural = "DoseAI Prompts"
