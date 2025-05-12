## Serving Flask Website with tailscale

```bash
git clone git@github.com:bsepaul/climate-models.git ~/climate-models
cd ~/climate-models
nix develop

# Now that the app is running, use tailscale serve to route to that port:
tailscale server https / http://localhost:5000

# Then you can confirm it with tailscale serve status:
tailscale serve status

tailscale funnel 443 on

# View the url of the website with the following
tailscale funnel status | awk '{print $1}'
```

## Resources
https://tailscale.com/blog/tailscale-funnel-beta/
https://tailscale.com/kb/1223/tailscale-funnel/
https://tailscale.dev/blog/funnel-101
