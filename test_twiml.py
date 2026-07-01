
import html

def generate_twiml(agent_response, audio_url):
    media_twiml = f'<Media>{audio_url}</Media>'
    try:
        escaped_body = html.escape(str(agent_response))
        final_twiml = f'<?xml version="1.0" encoding="UTF-8"?>\n<Response>\n    <Message>\n        <Body>{escaped_body}</Body>\n        {media_twiml}\n    </Message>\n</Response>'
        return final_twiml
    except Exception as e:
        return str(e)

# Sample complex response from logs
sample_response = 'नमस्ते रोहित जी, आपका संदेश मिला। आपने मुझसे “गाना” के बारे में पूछा है। \n\nमुझे ठीक से समझने के लिए ...'
sample_url = 'https://impersonal-asconoid-marinda.ngrok-free.dev/staticv2/resp_1766914767.mp3'

print(generate_twiml(sample_response, sample_url))
