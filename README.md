### Set up UV

Install UV: `sudo curl -LsSf https://astral.sh/uv/install.sh | sh`

### Config.txt

`sudo nano /boot/firmware/config.txt`

Add:

```
gpio=7=op,dl
gpio=8=op,dl
```


## Stupid Wi-Fi fix

`echo brcmfmac | sudo tee -a /etc/modules`