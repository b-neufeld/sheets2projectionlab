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

# TODO: Delete all these notes once cron stuff is working. Or save any useful links. 
# Possibly useful resources for getting crontab working
# https://betterstack.com/community/questions/how-to-run-cron-job-inside-docker-container/
# RUN crontab crontab 
#CMD ["crond", "-f"]
# https://stackoverflow.com/a/73301815
#CMD ["/usr/sbin/crond", "-n"]
#CMD ["/usr/bin/crontab","-n","crontab"]
#CMD ["/sbin/cron","-f"]
# TRY THIS https://betterstack.com/community/questions/how-to-run-cron-job-inside-docker-container/
# CMD cron && tail -f /var/log/cron.log

# Notes about how to do this differently 
# 1. https://github.com/googlesamples/assistant-sdk-python/issues/236#issuecomment-383039470
# 2. Virtual environment in docker container 
RUN pip install --break-system-packages --upgrade -r requirements.txt

# This is currently writing to /etc/crontab successfully but does not seem to be running. 
# TODO: Change "every 2 minutes" (useful for debugging) to "every 1 hour" once working
RUN echo "*/2 * * * * root python3 /sheets2projectionlab.py > /proc/1/fd/1 2>/proc/1/fd/2" >> /etc/crontab

# start cron in foreground (don't fork)
# TODO: Keep if I can get this working or remove if not. 
ENTRYPOINT [ "cron", "-f" ]

LABEL org.opencontainers.image.source="https://github.com/b-neufeld/sheets2projectionlab"