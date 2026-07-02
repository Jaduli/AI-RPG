FROM ollama/ollama:0.30.10

# Install curl
RUN apt-get update && apt-get install -y curl

COPY start.sh /start.sh
RUN chmod +x /start.sh

ENTRYPOINT ["/bin/bash", "/start.sh"]