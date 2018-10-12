# latter versions of the image are broken at the moment
# TODO : Check how I could pass the image version as a parameter from docker
FROM linuxserver/deluge:136

RUN mkdir /scripts

COPY scripts/extract.py /scripts/extract.py
RUN chown -R abc:users /scripts
RUN chmod +x /scripts/extract.py

RUN ls -la /scripts

#VOLUME /scripts