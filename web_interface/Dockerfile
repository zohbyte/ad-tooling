FROM python:3.12-slim

WORKDIR /app

COPY web_interface/requirements.txt ./web_interface/
RUN pip install --no-cache-dir -r web_interface/requirements.txt

COPY web_interface/ ./web_interface/
COPY exploit-template.py .

ENV WORKSPACES_ROOT=/workspaces
ENV DEFAULT_TEAM=exploits
ENV TULIP_API_BASE=http://api:5000
ENV TULIP_UI_URL=http://localhost:3000
ENV GLITCH_API_BASE=https://glitch.ad
ENV GLITCH_NOP_HOST=10.100.1.1
ENV TOOLING_API_KEY=supersecretkey

VOLUME /workspaces
EXPOSE 8000

CMD ["python", "-m", "uvicorn", "web_interface.main:app", "--host", "0.0.0.0", "--port", "8000"]
