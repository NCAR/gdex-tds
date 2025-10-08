### To start fresh, delete containers and images
`podman image rm nginx_nginx`
`podman container rm thredds -f`
`podman container rm nginx -f`


You can check to see that there's nothing running using,
`podman container ps -a`

### Now that there is a clean slate, let's build the project.
#### Be sure to be in this directory as it needs to find a docker-compose file
`podman-compose build`

### After a successful build, from this directory execute the folowing to spin up the container
`podman-compose up -d`


That's it! you should now have the container running

If for whatever reason you want to take a look inside the container, you can execute,
`podman exec -it nginx bash`
which will start a shell within the nginx container. Replace 'nginx' with 'thredds' to view the thredds container.


## Creating systemd unit files

Once the containers are up and running:
```
podman generate systemd --new --files --name thredds
podman generate systemd --new --files --name nginx
```

## Restarting the services
Once the unit files have been loaded, one can restart as root:
```
systemctl restart container-thredds.service
systemctl restart container-nginx.service
```
Restart on Sun Sep 28 07:00:22 MDT 2025
Restart on Mon Sep 29 10:54:02 MDT 2025
Restart on Mon Sep 29 18:54:02 MDT 2025
Restart on Mon Sep 29 21:24:02 MDT 2025
Restart on Thu Oct  2 15:24:02 MDT 2025
Restart on Thu Oct  2 15:54:02 MDT 2025
Restart on Fri Oct  3 01:24:02 MDT 2025
Restart on Fri Oct  3 02:54:02 MDT 2025
Restart on Fri Oct  3 03:54:02 MDT 2025
Restart on Fri Oct  3 05:54:02 MDT 2025
Restart on Fri Oct  3 06:24:02 MDT 2025
Restart on Fri Oct  3 07:54:02 MDT 2025
Restart on Tue Oct  7 07:23:43 UTC 2025 by GHA
Restart on Tue Oct  7 08:25:13 UTC 2025 by GHA
Restart on Tue Oct  7 08:39:19 UTC 2025 by GHA
Restart on Tue Oct  7 09:06:50 UTC 2025 by GHA
Restart on Tue Oct  7 09:24:18 UTC 2025 by GHA
Restart on Tue Oct  7 09:36:05 UTC 2025 by GHA
Restart on Tue Oct  7 09:48:46 UTC 2025 by GHA
Restart on Tue Oct  7 10:24:18 UTC 2025 by GHA
Restart on Tue Oct  7 10:37:34 UTC 2025 by GHA
Restart on Tue Oct  7 10:49:09 UTC 2025 by GHA
Restart on Tue Oct  7 11:05:30 UTC 2025 by GHA
Restart on Tue Oct  7 11:22:09 UTC 2025 by GHA
Restart on Tue Oct  7 11:34:34 UTC 2025 by GHA
Restart on Tue Oct  7 12:50:28 UTC 2025 by GHA
Restart on Tue Oct  7 20:35:55 UTC 2025 by GHA
Restart on Tue Oct  7 20:48:47 UTC 2025 by GHA
Restart on Tue Oct  7 21:34:14 UTC 2025 by GHA
Restart on Tue Oct  7 22:34:54 UTC 2025 by GHA
Restart on Tue Oct  7 23:05:33 UTC 2025 by GHA
Restart on Wed Oct  8 01:33:28 UTC 2025 by GHA
Restart on Wed Oct  8 02:13:15 UTC 2025 by GHA
Restart on Wed Oct  8 02:44:15 UTC 2025 by GHA
Restart on Wed Oct  8 03:06:52 UTC 2025 by GHA
Restart on Wed Oct  8 03:41:13 UTC 2025 by GHA
Restart on Wed Oct  8 04:37:34 UTC 2025 by GHA
Restart on Wed Oct  8 05:36:05 UTC 2025 by GHA
Restart on Wed Oct  8 06:25:40 UTC 2025 by GHA
Restart on Wed Oct  8 06:52:44 UTC 2025 by GHA
Restart on Wed Oct  8 07:48:44 UTC 2025 by GHA
Restart on Wed Oct  8 08:08:55 UTC 2025 by GHA
Restart on Wed Oct  8 08:25:17 UTC 2025 by GHA
Restart on Wed Oct  8 09:48:25 UTC 2025 by GHA
Restart on Wed Oct  8 10:24:13 UTC 2025 by GHA
Restart on Wed Oct  8 10:37:38 UTC 2025 by GHA
Restart on Wed Oct  8 10:48:54 UTC 2025 by GHA
Restart on Wed Oct  8 11:22:23 UTC 2025 by GHA
