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
