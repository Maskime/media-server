# latter versions of the image are broken at the moment
# TODO : Check how I could pass the image version as a parameter from docker
FROM linuxserver/deluge:136

RUN mkdir /scripts

COPY scripts/extract_archive.py /scripts/extract_archive.py
RUN chown -R abc:users /scripts
RUN chmod +x /scripts/extract_archive.py

VOLUME /scripts