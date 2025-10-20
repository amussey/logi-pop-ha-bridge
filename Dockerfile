FROM python:3.12-slim

RUN mkdir /app
WORKDIR /app

# Install dependencies
ADD requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
ADD logi_ha_bridge /app/logi_ha_bridge
COPY scripts/run.sh /app/run.sh
RUN chmod a+x /app/run.sh

CMD [ "/app/run.sh" ]
