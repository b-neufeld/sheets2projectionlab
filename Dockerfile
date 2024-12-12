FROM python:3.11.4

COPY . .

# How I finally got Chrome & Chromedriver working https://datawookie.dev/blog/2023/12/chrome-chromedriver-in-docker/
RUN apt-get update -qq -y && \
    apt-get install -y \
        libasound2 \
        libatk-bridge2.0-0 \
        libgtk-4-1 \
        libnss3 \
        xdg-utils \
        wget && \
    wget -q -O chrome-linux64.zip https://bit.ly/chrome-linux64-121-0-6167-85 && \
    unzip chrome-linux64.zip && \
    rm chrome-linux64.zip && \
    mv chrome-linux64 /opt/chrome/ && \
    ln -s /opt/chrome/chrome /usr/local/bin/ && \
    wget -q -O chromedriver-linux64.zip https://bit.ly/chromedriver-linux64-121-0-6167-85 && \
    unzip -j chromedriver-linux64.zip chromedriver-linux64/chromedriver && \
    rm chromedriver-linux64.zip && \
    mv chromedriver /usr/local/bin/  

# USER root fixes a permissions error https://stackoverflow.com/a/37615312
# TODO: Test if the root thing is actually required. Could possibly remove. 
# How to run cron in Docker: https://lostindetails.com/articles/How-to-run-cron-inside-Docker
USER root
RUN apt-get -y --fix-broken install cron

# Notes about how to do this differently 
# 1. https://github.com/googlesamples/assistant-sdk-python/issues/236#issuecomment-383039470
# 2. Virtual environment in docker container 
RUN pip install --break-system-packages --upgrade -r requirements.txt

# This is currently writing to /etc/crontab successfully but does not seem to be running. 
RUN echo "*/2 * * * * python3 /sheets2projectionlab.py > /proc/1/fd/1 2>/proc/1/fd/2" >> /etc/crontab

# start cron in foreground (don't fork)
# From here: https://stackoverflow.com/a/61631500
RUN chmod 0644 /etc/crontab
RUN /usr/bin/crontab /etc/crontab
# Push Docker env variables to /etc/environment which is where cron can see them per https://stackoverflow.com/a/41938139
CMD ["/bin/bash", "-c", "printenv > /etc/environment && cron -f"]

LABEL org.opencontainers.image.source="https://github.com/b-neufeld/sheets2projectionlab"