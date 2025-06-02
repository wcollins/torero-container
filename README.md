# 📦 torero container
Container image for [torero](https://torero.dev), built using vendor-neutral Containerfile specifications and packaged in a _ready-to-use_ container with optional [OpenTofu](https://opentofu.org) installation. The image is hosted on GitHub Container Registry (GHCR). For more details about _torero_, visit the [official docs](https://docs.torero.dev/en/latest/).

> [!NOTE]
> For questions or _real-time_ feedback, you can connect with us directly in the [Network Automation Forum (NAF) Slack Workspace](https://networkautomationfrm.slack.com/?redir=%2Farchives%2FC075L2LR3HU%3Fname%3DC075L2LR3HU) in the **#tools-torero** channel.

## Features
- Built with vendor-neutral Containerfile for maximum compatibility
- Based on [debian-slim](https://github.com/lxc/lxc-ci/tree/main/images/debian) for minimal footprint
- Hosted on GitHub Container Registry (GHCR) for reliable distribution
- Includes _torero_ installed and ready to go
- Optional [OpenTofu](https://opentofu.org/) installation at runtime
- Optional SSH administration for testing convenience + labs
- Health Check to verify functionality

## Inspiration
Managing and automating a hybrid, _multi-vendor_ infrastrcuture that encompasses _on-premises systems, private and public clouds, edge computing, and colocation environments_ poses significant challenges. How can you experiment to _learn_ without breaking things? How can you test new and innovative products like _torero_ on the test bench without friction to help in your evaluation? How do you test the behavior of changes in lower level environments before making changes to production? I use [containerlab](https://containerlab.dev/) for all of the above! This project makes it easy to insert _torero_ in your _containerlab_ topology file, connect to the container, and run your experiments -- the sky is the limit!

> [!IMPORTANT]
> This project was created for experimenting, labs, tests, and as an exercise to show what is _possible_. It was not built to run in _production_.