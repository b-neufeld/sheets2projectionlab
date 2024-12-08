FROM selenium/standalone-chrome:latest

COPY . .

# USER root fixes a permissions error https://stackoverflow.com/a/37615312
USER root
RUN sudo apt-get update && apt-get -y --fix-broken install cron

# https://betterstack.com/community/questions/how-to-run-cron-job-inside-docker-container/
COPY crontab /etc/cron.d/crontab
RUN touch /var/log/cron.log

# Notes about how to do this differently 
# 1. https://github.com/googlesamples/assistant-sdk-python/issues/236#issuecomment-383039470
# 2. 
RUN sudo pip install --break-system-packages --upgrade -r requirements.txt

RUN crontab crontab

#CMD ["crond", "-f"]
# https://stackoverflow.com/a/73301815
#CMD ["/usr/sbin/crond", "-n"]
#CMD ["/usr/bin/crontab","-n","crontab"]
CMD ["/sbin/cron","-f"]
# TRY THIS https://betterstack.com/community/questions/how-to-run-cron-job-inside-docker-container/
# CMD cron && tail -f /var/log/cron.log


LABEL org.opencontainers.image.source="https://github.com/b-neufeld/sheets2projectionlab"