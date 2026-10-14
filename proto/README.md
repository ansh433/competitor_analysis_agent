# Streaming event contract

`competitor_events.proto` is the canonical wire contract. The backend validates
domain payloads with Pydantic before Protobuf encoding. The browser decodes the
same binary message carried as base64 in each SSE frame.

Generate language bindings from the repository root after dependencies are
installed:

```bash
uv run --project backend python -m grpc_tools.protoc \
  -I proto --python_out=backend/app/proto proto/competitor_events.proto
npm --workspace frontend run generate:proto
```

Generated bindings are committed when the contract changes so production
images do not need a compiler.

