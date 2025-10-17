## AI Streaming and Tool-Calling

### Request

POST `/ai/respond`

Body:

```json
{
  "prompt": "add milk to groceries",
  "history": [{"role":"user","content":"..."}],
  "mode": "tools+chat"
}
```

### Stream Lifecycle

- Text chunks: `{"type":"text.delta","content":"..."}`
- Tool start/finish: `{"type":"tool.status","name":"...","state":"started|finished"}`
- Stream end: `{"type":"done"}`

### Tool Loop

When the model requests tools, the server:

1. Validates args against Pydantic models
2. Executes the mapped in-process service
3. Submits tool outputs back to OpenAI and continues streaming

### Troubleshooting

- Missing API key → 401 with JSON error
- OpenAI error → 502 with `detail`
- Ensure `OPENAI_API_KEY` and `OPENAI_MODEL` set; default model is `gpt-4.1-mini`


