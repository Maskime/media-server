# latter versions of the image are broken at the moment
# TODO : Check how I could pass the image version as a parameter from docker
FROM linuxserver/deluge:136

RUN mkdir /scripts

COPY scripts/extract.py /scripts/extract.py
COPY scripts/mark_complete.py /scripts/mark_complete.py
COPY scripts/mark_and_extract.sh /scripts/mark_and_extract.sh
RUN chown -R abc:users /scripts
RUN chmod +x /scripts/extract.py
RUN chmod +x /scripts/mark_complete.py
RUN chmod +x /scripts/mark_and_extract.sh

RUN ls -la /scripts

#VOLUME /scripts