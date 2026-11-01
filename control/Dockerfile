FROM docker:28-cli
RUN apk add --no-cache python3
WORKDIR /app
COPY control_actions.py control_server.py ./
CMD ["python3", "-u", "control_server.py"]
