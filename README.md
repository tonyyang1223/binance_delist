# binance_delist

Scrape binance web for delisting announcement and send API call to specified bots to blacklist them

``` 
bash install_chrome.sh
cp bots.json.example bots.json
```

* Modify bots.json with the info of your bots
* Modify blacklist.json to become initial blacklist for all the bots. You can use `blacklist.json.example` if you prefer no initial blacklist.
* Modify `loop_secs` to suit your preference of how often the bot scrape binance. Default is 90 seconds.

## Non-docker
```
bash install.sh
source .venv/bin/activate
bash run.sh
```


## Docker
```
docker-compose up -d --build
```


## Run as a Server

Create a service file at `/etc/systemd/system/monitor_delist.service`. The content is as follows (modify the paths as needed):

```
[Unit]
Description=Delist monitor and notify bots
After=network.target

[Service]
ExecStart=/home/ubuntu/soft/binance_delist/.venv/bin/python3 /home/ubuntu/soft/binance_delist/bot.py
WorkingDirectory=/home/ubuntu/soft/binance_delist/
StandardOutput=append:/home/ubuntu/soft/binance_delist/binance_delist_info.log
StandardError=append:/home/ubuntu/soft/binance_delist/binance_delist_error.log
Restart=always
User=ubuntu
Group=ubuntu

[Install]
WantedBy=multi-user.target
```

Control commands:

1. **Reload the systemd manager configuration**:
    ```bash
    sudo systemctl daemon-reload
    ```

2. **Start the service**:
    ```bash
    sudo systemctl start monitor_delist
    ```

3. **Enable the service to start on boot**:
    ```bash
    sudo systemctl enable monitor_delist
    ```

4. **Check the service status**:
    You can check the service status using the following command:
    ```bash
    sudo systemctl status monitor_delist
    ```

5. **Stop the service**:
    ```bash
    sudo systemctl stop monitor_delist
    ```