FROM node:22-bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends python3 python-is-python3 git ca-certificates \
 && rm -rf /var/lib/apt/lists/*
RUN npm i -g @anthropic-ai/claude-code@2.1.319 @openai/codex@0.163.0 && npm cache clean --force
# No self-updates or telemetry inside throwaway containers.
ENV DISABLE_AUTOUPDATER=1 CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1
USER node
WORKDIR /work
