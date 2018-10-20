# Let's write a bit of history...

So...

I ended up trying to fix a common problem which is : neither Radarr or Sonarr are capable
of extracting archives...
So I tried to write a script that would handle this correctly.
But I spent waaaaaay too much time on this and I need to move on other priorities.

For the sake
of "Maybe I'll come back to that when I'm done with the rest" here is the problems that I've
been facing and solutions that should be implemented.

## Corrupted split files

Here the thing, when downloading split archive such as rars, it may happen that you have a 
writing problem along the way. Which will make your 45 GiB file completely unusable...

>"I am the disappointment of Jack..."

### What should be done:

  1. Check if there is a sfv file
        * If there is one use it to check the CRCs before doing anything else as the `unrar` command
    takes FOREVER to handle this check itself
  1. Try to `unrar` the file and check the result for error.
        * If there is an error, I still need to make some research to check if it's feasible to
        ask deluge to re-download only a part of the torrent
        
## Who starts the script ?

My first idea was to use the "Execute" plugin of deluge that would start the `extract.py` script
on `Torrent Completed` event.
Problem is, and I don't know why, if the extraction is taking a long time, the `deluged` process
will start to hang, eventually come back online on its own, but this tells me this is not the 
proper approach for this problem.

### What should be done

The way I see things, in the end, the extraction process should be delegated to its own container.

Within this new container I'd start a daemon that would watch the `media/downloads` dir
and start the extractions accordingly.

> Isn't it a bit Overkill ???

That's what I though also, but when faced with the described problem above, I realised that 
there would be also a need to inform Sonarr and Radarr about the state of the extraction.
Which imply that I have a connection to their respective API, which imply that I have 
a client to connect to them and all the rest...

In the end it's a project on its own.

## Let's talk to Sonarr and Radarr

In the case of a failed unpack and if I can't find a way to ask deluge to re-download only a 
piece of the torrent, I'll have to tell *arr that the download failed and it needs to look for
a new one.

### What should be done

I've fiddle a bit with their REST api, and as far as I saw, I didn't find a way to
reconcile torrent file and their counterpart in *arr softwares.

But if I find a way to reconcile them, I need to find the correct way to tell *arr that
the download failed. With the proper configuration they should start to look for a new one
as soon as the download was flagged as failed.

> Message in a bottle... -- Stings