# Overview
With this deployment you'll have a full logging stack that will ingest syslog via syslog-ng, relay syslog messages to Alloy, send them to Loki for storage, and display them within Grafana.

## TL;DR
If you want to skip the background and just get Loki up and running, you can go to the [Configuration section](#configuration) below or just reference the relevant `*-docker-compose.yml` file alongside the individual service config files.

# Why
The purpose of this repo is establish a simple stack with straightfoward service configs to ingest syslog data into Loki while also giving greater context to the configuration process. It took me longer than I wanted to get an MVP for Loki up and running based on available guides, including Grafana's own documentation and tutorials. These sources were often outdated in sneaky ways, glossed over critical config items, or even misrepresented service capabilities.

Grafana recommends deploying Loki to production with k8s and doesn't provide an alternate self-hosted deployment strategy, even to just setup a test environment.

With so many moving parts that must be in a base functional state before you can troubleshoot your own stack, getting started with Loki can be tedious.

# Considerations
## Log storage
You can get away with storing all ingested Loki log files locally on your host's filesystem but [Grafana recommends against it](https://grafana.com/docs/loki/latest/operations/storage/). It's okay for a basic evaluation.

I'd recommend using an S3-compatible object store once your comfortable with your base install. Popular selfhosted S3 options include:
- [SeaweedFS](https://github.com/seaweedfs/seaweedfs) (recommended): Terminology makes getting started a little harder than other S3 options but easy to get past, performant, no need for separate SSD metadata pool, 1st-party web GUI, good development community.
- [Garage](https://garagehq.deuxfleurs.fr/): Easy to get started, straightfoward architecture, 1st-party web GUI in development (no ETA), popular community web GUI is unmaintained, performance is heavily tied to a separate metadata store that should be on performant SSDs (can be separated from regular data pool).
- [RustFS](https://rustfs.com/): Easy to get started, 1st-party web GUI if needed, questionable license in the long-term, concerns about poor quality vibe coded features.

## Grafana Alloy vs. Grafana Agent vs. Promtail
Grafana offers x3 ways to ingest logs:
1. **Grafana Alloy**: collects logs plus everything else.
2. **Grafana Agent**: collects logs plus everything else. Deprecated and replaced by Alloy.
3. **Grafana Promtail**: feature complete log collector.

For this stack, we're using Alloy as it's going to be better supported going forward, even if we don't need the bulk of its features.

With that said, it was a lot easier wrap my head around deploying syslog for Loki using Promtail initially so I've included the relevant config files and docker service info in this repo for reference. 

## Alloy syslog 
- Alloy only plays nice with RFC syslog messages. When you encounter cases outside this scope, you'll need to relay syslog messages using a service like syslog-ng or rsyslog front of Alloy which can ingest unsupported logs and output them in RFC format before forwarding them to Alloy over TCP.
    - Regarding syslog handling, more background can be found in the [Promtail docs about the Syslog Receiver](https://grafana.com/docs/loki/latest/send-data/promtail/scraping/#syslog-receiver). The same considerations from Promtail apply to Alloy. It's *highly* recommended you read this to understand certain limitations around how Loki has to handle incoming syslog data.
- To overcome these limitations, we'll use a syslog-ng service to forward re-formated syslog data to Alloy.

# Prerequisites
## Docker compose
If you're going to deploy the stack you'll need docker compose set up. It should come included if you've installed Docker based on Docker's own [install guide](https://docs.docker.com/engine/install/) for your relevant OS.
```shell
$ docker compose version
Docker Compose version v5.1.2
```

## Config files
Loki, Alloy, and syslog-ng each rely on their own configuration files that specify things like log schema, endpoint ports and addresses, as well as log labels. For a vanilla compose file setup, we won't need to change anything since these configs will reference each other's docker service names versus "real" hostnames or IP addresses.
- Loki: `loki-config.yml`
- Alloy: `config.alloy`
- syslog-ng: `syslog-ng.conf`

# Configuration
1. Clone this repo wherever you plan to run it and `cd` into the project directory:
    ```bash
    $ git clone https://github.com/JamesEisele/grafana-loki-log-stack.git
    $ cd grafana-loki-log-stack
    grafana-loki-log-stack $ 
    grafana-loki-log-stack $ 
    ```

2. Review your Loki config.
    - You shouldn't need to update any of the provided defaults as it will automatically ingest logs sent its way.
    - More info can be found in the [official docs page for it](https://grafana.com/docs/loki/latest/configure/). For our assumed use case, we've loosely followed their "local configuration example".

3. Review your Alloy config.
    - In the `loki.write "default"` section, you *may* need to update your endpoint `url` address of your Loki container if you're using any non-default Docker service names or networks that weren't part of the baseline config provided (it shouldn't by default):
        ```diff
            loki.write "default" {
                endpoint {
        -                url = "http://grafana-loki-log-stack-loki-1:3100/loki/api/v1/push"
        +                url = "http://loki.example.com:3100/loki/api/v1/push"
                }
        ```


4. Review your syslog-ng config file `syslog-ng.conf`.
    - Similar to Step 3, you *may* need to update the `destination d_alloy` address if your Alloy container has a different Docker service name or network setup (it shouldn't by default):
        ```diff
        - syslog("grafana-loki-log-stack-alloy-1" transport("tcp") port(1514));
        + syslog("alloy.example.com" transport("tcp") port(1514));
        ```

5. Review your `local-docker-compose.yml` file which will define how Docker will deploy your services. You shouldn't need to make any changes initially.

6. Run the compose file using the `-f` flag to specify where your compose file is located:
    ```shell
    $ docker compose -f local-docker-compose.yml up -d
    ```

7. Check service status
    ```shell
    $ docker ps
    CONTAINER ID   IMAGE                                COMMAND                  CREATED          STATUS                    PORTS                                                                                                                                       NAMES
    beb45c4f474b   balabit/syslog-ng:4.11.0             "/usr/local/bin/entr…"   38 seconds ago   Up 36 seconds (healthy)   0.0.0.0:514->514/udp, [::]:514->514/udp, 6514/tcp, 0.0.0.0:514->601/tcp, [::]:514->601/tcp                                                  grafana-loki-log-stack-syslog-ng-1
    9dfa597cee4d   grafana/alloy:v1.3.1                 "/bin/alloy run --di…"   38 seconds ago   Up 37 seconds             0.0.0.0:1514->1514/tcp, [::]:1514->1514/tcp, 0.0.0.0:12345->12345/tcp, 0.0.0.0:1514->1514/udp, [::]:12345->12345/tcp, [::]:1514->1514/udp   grafana-loki-log-stack-alloy-1
    8cefffc0b803   grafana/grafana:13.0.1-security-01   "/run.sh"                38 seconds ago   Up 37 seconds             0.0.0.0:3000->3000/tcp, [::]:3000->3000/tcp                                                                                                 grafana-loki-log-stack-grafana-1
    e131f8056ebb   grafana/loki:3.7.2                   "/usr/bin/loki -conf…"   38 seconds ago   Up 37 seconds             0.0.0.0:3100->3100/tcp, [::]:3100->3100/tcp                                                                                                 grafana-loki-log-stack-loki-1
    ```

    If you need to troubleshoot a specific service, you can either show the logs for the container with `docker logs <container name>` or by exec'ing into the container to inspect things further.

8. Login to Grafana with the default credentials `admin`/`admin` and navigate to **Drilldown** > **Logs** to view the Loki logs setup. We automatically provision Loki as a datasource within Grafana when the Grafana service starts.

9. (Optional) Test that syslog-ng is properly relaying syslog messages to Alloy/Loki. You'll need Python v3.7 or higher installed (check with `python3 --version`):
    ```shell
    # Setup a virtual environment (Linux variant):
    $ python3 -m venv venv
    $ source venv/bin/activate
    (venv) $ pip install -r requirements.txt
    # Default test: send TCP and UDP syslog messages to port 514:
    (venv) $ python3 syslog-test.py -l locahost
    > Sent syslog message via TCP to localhost:514
    > Sent syslog message via UDP to localhost:514
    ```

    You can now login to your Grafana instance and under the "Explore" > "Logs" section in the sidebar, you should see your test log messages show up under Loki:
    ![Screenshot of Grafana  web interface showing successful test syslog messages sent from syslog-test.py scritpt.](/media/syslog-py_test.png?raw=true)

10. Shutdown the stack:
    ```shell
    docker compose -f local-docker-compose.yml down
    ```

# Next steps
With this basic Loki log stack up and running, there's a few easy wins that'll improve the stack's resilence and help with general quality of life:
- Configure Loki to store logs on a remote S3 object store (see earlier notes for recommendations).
- Setup log rotation/retention for better storage management of long-lived log files.
- Integrate the stack with a reverse proxy like Traefik or Caddy. This is the easiest path to get certs for hostnames like `syslog.example.com` as well as allow you properly configure and handle TLS syslog.
- Lock down networking so that only relevant Docker services can access things like your `syslog-ng` Docker service ports directly if you've configured them on purpose.
- Setup relevant Grafana dashboards with Loki log references so you're not always hunting for service logs in Grafana.

# Docker Swarm caveats and notes
On the off chance that you want to run this setup in a Docker Swarm environment, the regular Docker compose details should get you most of the way towards a running Loki stack. There's also an included `swarm-docker-compose.yml` version with some specific Swarm sytax and config items.

Loki logs was one of the first stacks I deployed to my cluster environment which helped surface a lot of headaches related to Swarm itself. If this project seems like a good starting point to get into a more decentralized compute setup, I'd warn against new users from deploying Swarm. It's an unmaintained and poorly supported extension of Docker with a narrowly valid usecase that is easy to fall out of. You're likely better off learning K8s or K3s even if you don't need the full complexity they offer.
- Distributed storage in Swarm is largely an unsolved problem, especially for smaller clusters. You might be able to get by with questionable NFS or SMB shares mounted across hosts but these aren't POSIX compliant and will likely result in data corruption over the long term.
    - I finally settled on Ceph, which I'd also use for K8s, but the jump from NFS to a full Ceph setup was a pretty big leap in knowledge and hardware (SSDs + networking).
- Remote log storage is a more important consideration in a Swarm environment versus a single host running a compose file. Again, you might be able to get away with something like an NFS mount, you're going to have a bad time. Think about an S3 object store option outlined earlier.
- Look into a virtual IP setup across your manager hosts using something like Keepalived so that you can assign a shared IP across your Swarm managers in order to take advantage of Swarm's dynamic networking.

## Swarm-specific configuration items

### MVP test swarm setup
If you want to quickly test this stack in Swarm but you don't have a swarm already deployed, you can run it on a single node swarm:
```shell
$ docker swarm init
Swarm initialized: current node (qqicqjamshajxxut69baiqq93) is now a manager.
...
$ docker node ls
ID                 HOSTNAME   STATUS    AVAILABILITY   MANAGER STATUS   ENGINE VERSION
qqicqjamxxut69 *   host-1     Ready     Active         Leader           27.1.2
```

### Storage
If you're deploying this stack via Swarm, the easiest (but sketchy) way to get up and running is to store your named volumes and config files in a remote NFS share that's accessible on all nodes. You might also think about putting your `swarm-docker-compose.yml` file on an NFS share accesible to all managers.

```shell
sudo mkdir /mnt/swarm/volumes/grafana-data
sudo mkdir /mnt/swarm/volumes/grafana-datasources
sudo mkdir /mnt/swarm/volumes/loki-data
sudo mkdir /mnt/swarm/volumes/loki-config
sudo nano /mnt/swarm/volumes/loki-config/loki-config.yml
sudo mkdir /mnt/swarm/volumes/alloy-config/
sudo nano /mnt/swarm/volumes/alloy-config/config.alloy
sudo mkdir /mnt/swarm/volumes/syslog-ng-config/
sudo nano /mnt/swarm/volumes/syslog-ng-config/syslog-ng.conf
sudo cp grafana/provisioning/datasources/loki.yml /mnt/swarm/volumes/grafana-datasources/loki.yml
```

### Swarm-specific commands
```shell
# Deploy stack via the compose file
docker stack deploy -c /mnt/docker-swarm/stacks/swarm-docker-compose.yml loki-logs

# Check service status
$ docker stack ps loki-logs
ID             NAME                        IMAGE                      NODE        DESIRED STATE   CURRENT STATE           ERROR                         PORTS
wctjsqd4boou   loki-logs_alloy.1           grafana/alloy:v1.14.1      prod-dw-3   Running         Running 1 minute ago
sf4445xykhrx   loki-logs_loki.1            grafana/loki:3.7.2         prod-dw-1   Running         Running 1 minute ago
l8mwj612qz62   loki-logs_syslog-ng.1       balabit/syslog-ng:4.11.0   prod-dm-2   Running         Running 1 minute ago

$ docker service ps loki-logs_alloy
ID             NAME                    IMAGE                   NODE        DESIRED STATE   CURRENT STATE          ERROR     PORTS
wctjsqd4boou   loki-logs_alloy.1       grafana/alloy:v1.14.1   prod-dw-3   Running         Running 2 days ago

# Shutdown the stack
$ docker stack rm loki-logs
```

### Networking
Docker Swarm references compose stacks and services differently with its internal DNS setup. The example Grafana Alloy and syslog-ng configs in this project use the regular compose naming conventions such as `grafana-loki-log-stack-alloy-1` to refer to Alloy service. When you deploy this via Swarm, you'll need to check the stack and service name convention and update these configs accordingly.

Docker Swarm also makes use of overlay networks so that services can talk with each other across the swarm cluster. The example compose file for swarm has all the services within the same overlay network. However, I did leave the `ports` section for each service exposed so that users can easily verify connectivity and service status. In a production deployment, these should be removed and/or locked down so that only services attached to the overlay network can ship logs. A reverse proxy like Traefik would also be a good idea to stand between clients shipping their logs and Loki.

### Secrets and configs
A "proper" production deployment of this stack in Swarm would use Docker [Secrets](https://docs.docker.com/engine/swarm/secrets/) an/or Docker [Configs](https://docs.docker.com/engine/swarm/configs/) to better handle sensitive and shared configuration files.

I avoided exploring that here as I've found their implementations too restrictive considering there's better tools to handle this if you want to take on extra complexity with something like Hashicorp Vault.

# Sources
- [Grafana Loki in Docker Swarm](https://medium.com/@mrschneider/grafana-loki-in-docker-swarm-78bfa6a761fa): Great guide around getting Loki setup in swarm. Touches on some of the nuances of Loki's documentation that are good to keep in mind for any deployment.
- https://gist.github.com/xtavras Githug gists for Python syslog testing used here to verify syslog-ng relay functionality with Promtail.
- [Convert a Promtail config to an Alloy config](https://grafana.com/docs/alloy/latest/set-up/migrate/from-promtail/).
