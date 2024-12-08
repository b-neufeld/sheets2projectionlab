#FROM selenium/standalone-chrome:latest
#FROM selenium/standalone-firefox:4.27.0-20241204
#FROM ubuntu:noble-20241118.1
FROM python:3.11.4


COPY . .

# Another angle on Chrome & Chromedriver https://datawookie.dev/blog/2023/12/chrome-chromedriver-in-docker/
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
# How to run cron in Docker: https://lostindetails.com/articles/How-to-run-cron-inside-Docker
USER root
RUN apt-get -y --fix-broken install cron

# ubuntu intall pip3
# RUN apt update
# RUN apt install python3-pip -y

# https://betterstack.com/community/questions/how-to-run-cron-job-inside-docker-container/
#COPY crontab /etc/cron.d/crontab
#RUN touch /var/log/cron.log

# Notes about how to do this differently 
# 1. https://github.com/googlesamples/assistant-sdk-python/issues/236#issuecomment-383039470
# 2. 
RUN pip install --break-system-packages --upgrade -r requirements.txt

# RUN crontab crontab 
# I think root is required before the python3. 
RUN echo "*/2 * * * * root python3 /sheets2projectionlab.py > /proc/1/fd/1 2>/proc/1/fd/2" >> /etc/crontab

# start cron in foreground (don't fork)
ENTRYPOINT [ "cron", "-f" ]

#CMD ["crond", "-f"]
# https://stackoverflow.com/a/73301815
#CMD ["/usr/sbin/crond", "-n"]
#CMD ["/usr/bin/crontab","-n","crontab"]
#CMD ["/sbin/cron","-f"]
# TRY THIS https://betterstack.com/community/questions/how-to-run-cron-job-inside-docker-container/
# CMD cron && tail -f /var/log/cron.log

LABEL org.opencontainers.image.source="https://github.com/b-neufeld/sheets2projectionlab"