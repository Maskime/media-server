# Yet Another media-server with docker-compose
Compose file that handles a media server configuration

## Shout Out
Massive shout out to [linuxserver.io][1] for providing all the images from which I was able to make this work.
They're doing a tremendous work (for trying to do it all by myself I can assure that's a very heavy job...).

Shout out to [@Luzifer](https://github.com/Luzifer) for publishing his work on `docker-compose` and his `systemd unit files`.

I'm always amazed about the amount of work each community is able to put on all thoses subjects and then share it freely to the world.

## Prerequisites

  * Docker
  * docker-compose
  * This was tested on an Ubuntu (16.04), as long as you're on a linux distro it should work.

## Components
This media server has the following components for you to enjoy :

|Component|Relevant link|Purpose in the stack|
|:---------:|:----------:|--------------------|
|[Plex](https://www.plex.tv/)|[linuxserver/plex](https://hub.docker.com/r/linuxserver/plex/)|Handles the entertainment part of things|
|[Sonarr](https://sonarr.tv/)|[linuxserver/sonarr](https://hub.docker.com/r/linuxserver/sonarr/)|Search for TV Series|
|[Radarr](https://radarr.video/)|[linuxserver/radarr](https://hub.docker.com/r/linuxserver/radarr/)|Search for Movies|
|[Letsencrypt](https://letsencrypt.org/)|[linuxserver/letsencrypt][0]|Reverse proxy (with Nginx) with SSL enabled|
|[Tautulli](https://tautulli.com/)|[linuxserver/tautulli](https://hub.docker.com/r/linuxserver/tautulli/)|Get stats about your Plex Media Server usage|
|[Deluge](https://torrent-deluge.org)|[linuxserver/deluge](https://hub.docker.com/r/linuxserver/deluge/)|Torrent downloader (not for me for a friend)|
|[Ombi](https://ombi.io/)|[linuxserver/ombi](https://hub.docker.com/r/linuxserver/ombi/)|Take request from other people about what they'd like to find on your PMS|
|[Jackett](https://github.com/Jackett/Jackett)|[linuxserver/jackett](https://hub.docker.com/r/linuxserver/jackett/)|Unified search interface|
|Some Systemd Scripts|[Gist Link][2]|Some systemd unit files for a nice _fire and forget_ way of life|


## Installation

Here are the few steps you have to go through to have this working (eventually)
### Clone the repo
Well, if you don't do that, don't expect it to work.

### Edit the env files in `env_files` directory
#### `commons_envs.env`

  * `PGID` group id of the user running the containers
  * `PUID` user id of the user runing the containers
  * `TZ` timezone description

#### `letsencrypt.env`

  * `EMAIL` E-mail address that will be attached to your SSL certificate on the letsencrypt system
  * `URL` The main domain of your system (if your domain is `domain.com` then services are going to be accessible through `https://[service name].domain.com`)
  * `SUBDOMAINS` List of all the subdomains that will have an SSL certificate generated (unless you add or remove a service you shouldn't have to touch this)
  * `ONLY_SUBDOMAINS` Flag that tells the Letsencrypt bot not to deliver an SSL certificate to the main domain
  * `VALIDATION` Validation method that will be use to validate ownership of the SSL protected URL
  * `STAGING` More information on this flag on the [linuxserver/letsencrypt][0] image documentation

#### `plex.env`
  
  * `VERSION` Plex version you'd like to have (you should leave it at latest)
  
### Rename `.env.dist` to `.env`
You can read about the `.env` file purpose in `docker-compose` [here](https://docs.docker.com/compose/env-file/)

  * `VOLUME_DIR` This media-server implementation is designed with predicate that all the volumes are a sub-directory of a main directory.
  This variable is here to tell where the root of all the volumes is located.

### Configuring the reverse proxy
If you're eager to test it out you can run the `docker-compose up` command then open a browser to `https://plex.maindomain.com` and be
welcome with a `502 Bad Gateway` error. This is because we did not activate any `nginx` configuration in the letsencrypt container.
The nice folks at [linuxserver.io][1] already did the hard work for us and provide in their letsencrypt image all the configurations we need
for our media-server. All we're left to do is to activate them by renaming then from `*.conf.sample` to `*.conf` this way nginx will
load them at boot.

```
#Working dir : Where you cloned the repo
[Working dir]:docker-compose up letsencrypt #This only for the volumes/letsencrypt/config dir to be populated
#hit CTRL+C once it has finished to boot
[Working dir]: cd volumes/letsencrypt/config/nginx/proxy-confs
[Working dir]: mv plex.subdomain.conf.sample plex.subdomain.conf
[Working dir]: mv sonarr.subdomain.conf.sample sonarr.subdomain.conf
[Working dir]: mv radarr.subdomain.conf.sample radarr.subdomain.conf
[Working dir]: mv jackett.subdomain.conf.sample jackett.subdomain.conf
[Working dir]: mv tautulli.subdomain.conf.sample tautulli.subdomain.conf
[Working dir]: mv deluge.subdomain.conf.sample deluge.subdomain.conf
[Working dir]: mv ombi.subdomain.conf.sample ombi.subdomain.conf
```

You can then go in the renamed files and activate the http authentication or the LDAP one.

### First Plex Launch

On the first run, plex expects the person that connects to it to be on the same subnet. Since docker-compose will start it's own subnet
on the host machine, if you run it as is you will experience difficulties to connect to it (and it's really frustrating, believe me I know).

After looking for a clean solution, which I was not able to find, the quick and dirty way to do it, is to run the plex container on its own
first with the following command :
```
docker create \
  --name=plex \
  --net=host \
  -e VERSION=latest \
  -e PUID=<UID> -e PGID=<GID> \
  -e TZ=<timezone> \
  -v </path/to/volumes>/plex/config:/config \
  -v </path/to/volumes>/plex:/transcode \
  linuxserver/plex
```
The important part is related to the `--net=host` parameter. This way the container is not using a bridge to the host, but it's
actually using the host network. This way the container effectively runs on the same subnet as our.

You can now connect to your plex instance :
  1. Open browser to http://localhost:32400/web/index.html
  1. Complete the setup
  1. If all went well, you can now stop the container

We did all that so that the `Preferences.xml` file is updated correctly with our token and all relevant variables.

### Systemd unit files

You can find the whole process that needs to be accomplished [here][2]

### Profit ! _Not just yet_

You still need to handle the port forwarding part of your installation if necessary.
The ports that should be open are :

  * `443 - TCP` HTTPS port
  * `32400 - TCP/UDP` To be able to connect to Plex from outside
  * `58846 - TCP, 58946 - TCP/UDP` Related to deluge (still not for me, for a friend)
  
## Disclaimer

This comes without any warranties of any sorts. I can not be hold responsible if you ever stumble upon this and decide to do something
evil with it (like training some racoon to hold a bazooka and go berserk with it).

Pull requests, issues may or may not be handled but are always welcomed.

[0]:https://hub.docker.com/r/linuxserver/letsencrypt/
[1]:https://linuxsever.io
[2]:https://gist.github.com/Luzifer/7c54c8b0b61da450d10258f0abd3c917
