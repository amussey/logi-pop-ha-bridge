FROM python:3.12-slim

RUN mkdir /app
WORKDIR /app

# Install dependencies
ADD requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY logi_ha_bridge.py /app/logi_ha_bridge.py
# COPY run.sh /app/run.sh
# RUN chmod a+x /app/run.sh

# CMD [ "/run.sh" ]
CMD [ "python3", "/app/logi_ha_bridge.py" ]
