### 1. Download Git and NFS
`sudo apt update` <br>
`sudo apt install git` <br>
`sudo apt install nfs-common`

### 2. Modify Config.txt

`sudo nano /boot/firmware/config.txt`

Add:

```
gpio=7=op,dl
gpio=8=op,dl
```

### 3. Set up UV

Install UV: `sudo curl -LsSf https://astral.sh/uv/install.sh | sh`

### 4. Set up NFS mount

Create mount dir: `sudo mkdir -p /mnt/frame-images`
Mount remote share manually `sudo mount -t nfs <SERVER_IP>:/path/to/share /mnt/frame-images`
Add following line to `/etc/fstab` for persisting NFS share:\
```
<SERVER_IP>:/path/to/share /mnt/frame-images nfs defaults,noatime,_netdev,x-systemd.automount,x-systemd.requires=network-online.target 0 0
192.168.0.243:/var/nfs/shared/WoonKamerFotoLijst /mnt/frame-images nfs defaults,noatime,_netdev,x-systemd.automount,x-systemd.requires=network-online.target 0 0
```


### 5. Clone project

`git clone https://github.com/LeonJelsma/PiFrame.git`

### 6. Set up Systemd service

Copy contents of `piframe.service` to `/etc/systemd/system/piframe.service`

Then:
```
sudo systemctl daemon-reload
sudo systemctl enable piframe.service
sudo systemctl start piframe.service
```

### 7. (Optional) Stupid Wi-Fi fix

`echo brcmfmac | sudo tee -a /etc/modules`